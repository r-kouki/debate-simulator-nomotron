#!/usr/bin/env python3
"""
Train a QLoRA adapter from domain SFT data.

Uses data/sft/<domain>.jsonl with a "text" field containing chat-formatted input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import torch
from peft import prepare_model_for_kbit_training
from datasets import Dataset

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.model_loader import (  # noqa: E402
    load_base_model,
    get_lora_config,
    get_model_info,
    prepare_model_for_training,
    BASE_MODEL_PATH,
    ADAPTERS_PATH,
)
from src.train.dataset import (  # noqa: E402
    prepare_sft_dataset_for_training,
)
from src.train.trainer import (  # noqa: E402
    TrainingMetrics,
    get_training_arguments,
    create_trainer,
    save_training_report,
    compute_perplexity,
)


SEED = 42


def stable_hash(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest(), 16)


def assign_split(text: str) -> str:
    bucket = stable_hash(f"{SEED}:{text}") % 100
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "val"
    return "test"


def load_sft_splits(
    path: Path,
    max_train: Optional[int],
    max_val: Optional[int],
    max_test: Optional[int],
) -> tuple[Dataset, Dataset, Dataset, dict]:
    splits = {"train": [], "val": [], "test": []}
    counts = {"train": 0, "val": 0, "test": 0, "skipped": 0}
    limits = {"train": max_train, "val": max_val, "test": max_test}

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            text = record.get("text")
            if not text:
                counts["skipped"] += 1
                continue
            split = assign_split(text)
            limit = limits.get(split)
            if limit is not None and counts[split] >= limit:
                continue
            splits[split].append(record)
            counts[split] += 1
            if all(
                limits[name] is not None and counts[name] >= limits[name]
                for name in ["train", "val", "test"]
            ):
                break

    return (
        Dataset.from_list(splits["train"]),
        Dataset.from_list(splits["val"]),
        Dataset.from_list(splits["test"]),
        counts,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a QLoRA adapter for a domain.")
    parser.add_argument("domain", help="Domain name (e.g., medicine, ecology, debate)")
    parser.add_argument("--sft-path", help="Override SFT jsonl path")
    parser.add_argument("--max-train-samples", type=int, default=None)
    parser.add_argument("--max-val-samples", type=int, default=None)
    parser.add_argument("--max-test-samples", type=int, default=None)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--max-seq-length", type=int, default=512)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--target-modules", default="q_proj,v_proj")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    domain = args.domain
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    sft_path = Path(args.sft_path) if args.sft_path else PROJECT_ROOT / "data" / "sft" / f"{domain}.jsonl"
    if not sft_path.exists():
        raise FileNotFoundError(
            f"SFT dataset not found: {sft_path}. Run scripts/normalize_and_split.py first."
        )

    run_dir = PROJECT_ROOT / "runs" / "train" / domain / timestamp
    adapter_output = ADAPTERS_PATH / domain
    run_dir.mkdir(parents=True, exist_ok=True)
    adapter_output.mkdir(parents=True, exist_ok=True)

    training_config = {
        "domain": domain,
        "base_model": str(BASE_MODEL_PATH),
        "sft_path": str(sft_path),
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_alpha,
        "lora_dropout": args.lora_dropout,
        "target_modules": [m.strip() for m in args.target_modules.split(",") if m.strip()],
        "num_epochs": args.epochs,
        "batch_size": args.batch_size,
        "gradient_accumulation_steps": args.grad_accum,
        "learning_rate": args.learning_rate,
        "max_seq_length": args.max_seq_length,
        "max_train_samples": args.max_train_samples,
        "max_val_samples": args.max_val_samples,
        "max_test_samples": args.max_test_samples,
    }

    with (run_dir / "config.json").open("w", encoding="utf-8") as handle:
        json.dump(training_config, handle, indent=2)

    print("=" * 60)
    print("QLoRA ADAPTER TRAINING")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Domain: {domain}")
    print(f"SFT path: {sft_path}")
    print(f"Run directory: {run_dir}")

    print("\n--- Loading SFT Dataset ---")
    train_data, val_data, test_data, counts = load_sft_splits(
        sft_path,
        max_train=args.max_train_samples,
        max_val=args.max_val_samples,
        max_test=args.max_test_samples,
    )
    print(f"Train samples: {len(train_data)}")
    print(f"Validation samples: {len(val_data)}")
    print(f"Test samples: {len(test_data)}")
    if counts["skipped"]:
        print(f"Skipped: {counts['skipped']}")

    print("\n--- Loading Base Model (4-bit) ---")
    model, tokenizer = load_base_model()
    model_info = get_model_info(model)
    print(f"Model loaded: {model_info['model_type']}")
    print(f"Device: {model_info['device']}")
    print(f"GPU memory: {model_info.get('gpu_memory_allocated_gb', 0):.2f} GB")

    print("\n--- Preparing Model for QLoRA ---")
    model = prepare_model_for_kbit_training(model)

    print("\n--- Applying LoRA Adapters ---")
    lora_config = get_lora_config(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=training_config["target_modules"],
    )
    model = prepare_model_for_training(model, lora_config)

    print("\n--- Tokenizing Datasets ---")
    train_dataset = prepare_sft_dataset_for_training(
        train_data,
        tokenizer,
        max_length=args.max_seq_length,
    )
    val_dataset = prepare_sft_dataset_for_training(
        val_data,
        tokenizer,
        max_length=args.max_seq_length,
    )
    test_dataset = None
    if len(test_data) > 0:
        test_dataset = prepare_sft_dataset_for_training(
            test_data,
            tokenizer,
            max_length=args.max_seq_length,
        )

    print("\n--- Configuring Training ---")
    training_args = get_training_arguments(
        output_dir=run_dir / "checkpoints",
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        warmup_ratio=0.1,
        logging_steps=5,
        eval_steps=20,
        save_steps=40,
        dataloader_num_workers=0,
        dataloader_pin_memory=False,
    )

    metrics = TrainingMetrics()
    trainer = create_trainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        training_args=training_args,
        metrics=metrics,
    )

    print("\n--- Starting Training ---")
    train_result = trainer.train()

    print("\n--- Final Evaluation ---")
    eval_result = trainer.evaluate()

    final_train_loss = train_result.training_loss
    final_val_loss = eval_result["eval_loss"]
    test_loss = None
    if test_dataset is not None and len(test_dataset) > 0:
        test_result = trainer.evaluate(eval_dataset=test_dataset)
        test_loss = test_result["eval_loss"]

    print(f"Final training loss: {final_train_loss:.4f}")
    print(f"Final training perplexity: {compute_perplexity(final_train_loss):.2f}")
    print(f"Final validation loss: {final_val_loss:.4f}")
    print(f"Final validation perplexity: {compute_perplexity(final_val_loss):.2f}")
    if test_loss is not None:
        print(f"Final test loss: {test_loss:.4f}")
        print(f"Final test perplexity: {compute_perplexity(test_loss):.2f}")

    print("\n--- Saving Adapter ---")
    model.save_pretrained(adapter_output)
    tokenizer.save_pretrained(adapter_output)
    print(f"Adapter saved to: {adapter_output}")

    print("\n--- Saving Training Report ---")
    report_path = save_training_report(
        output_dir=run_dir,
        metrics=metrics,
        config=training_config,
        final_train_loss=final_train_loss,
        final_val_loss=final_val_loss,
        test_loss=test_loss,
        dataset_sizes={
            "train": len(train_data),
            "val": len(val_data),
            "test": len(test_data),
        },
    )
    with report_path.open("r", encoding="utf-8") as handle:
        report = json.load(handle)
    with (adapter_output / "training_report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"Adapter: {adapter_output}")
    print(f"Run artifacts: {run_dir}")

    del model
    del trainer
    torch.cuda.empty_cache()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
