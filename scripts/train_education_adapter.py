#!/usr/bin/env python3
"""
Phase 3: QLoRA Adapter Training for Education Domain

Trains a LoRA adapter on the education debate dataset using 4-bit quantization.

Features:
- Freezes base model weights
- Trains LoRA adapters (q_proj, v_proj)
- Logs training/validation loss and perplexity
- Saves adapter and training artifacts

Run from project root:
    python scripts/train_education_adapter.py

Requirements:
- NVIDIA GPU with ~10GB VRAM
- Education dataset in data/splits/education/
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch
from peft import prepare_model_for_kbit_training

from src.utils.model_loader import (
    load_base_model,
    get_lora_config,
    get_model_info,
    prepare_model_for_training,
    BASE_MODEL_PATH,
    ADAPTERS_PATH,
)
from src.train.dataset import (
    load_debate_jsonl,
    prepare_dataset_for_training,
)
from src.train.trainer import (
    TrainingMetrics,
    get_training_arguments,
    create_trainer,
    save_training_report,
    compute_perplexity,
)

# Configuration
DOMAIN = "education"
DATA_DIR = PROJECT_ROOT / "data" / "splits" / DOMAIN
ADAPTER_OUTPUT = ADAPTERS_PATH / DOMAIN
RUNS_DIR = PROJECT_ROOT / "runs" / "train" / DOMAIN

# Training hyperparameters
TRAINING_CONFIG = {
    "domain": DOMAIN,
    "base_model": str(BASE_MODEL_PATH),
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "target_modules": ["q_proj", "v_proj"],
    "num_epochs": 3,
    "batch_size": 2,
    "gradient_accumulation_steps": 8,
    "learning_rate": 2e-4,
    "warmup_ratio": 0.1,
    "max_seq_length": 512,
    "logging_steps": 5,
    "eval_steps": 20,
    "save_steps": 40,
}


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / timestamp

    print("=" * 60)
    print("PHASE 3: QLoRA Adapter Training")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Domain: {DOMAIN}")
    print(f"Run directory: {run_dir}")

    # Create output directories
    run_dir.mkdir(parents=True, exist_ok=True)
    ADAPTER_OUTPUT.mkdir(parents=True, exist_ok=True)

    # Save config
    with open(run_dir / "config.json", 'w') as f:
        json.dump(TRAINING_CONFIG, f, indent=2)

    # Step 1: Load datasets
    print("\n--- Loading Datasets ---")
    train_data = load_debate_jsonl(DATA_DIR / "train.jsonl")
    val_data = load_debate_jsonl(DATA_DIR / "val.jsonl")
    print(f"Train samples: {len(train_data)}")
    print(f"Validation samples: {len(val_data)}")

    # Step 2: Load base model
    print("\n--- Loading Base Model (4-bit) ---")
    model, tokenizer = load_base_model()

    model_info = get_model_info(model)
    print(f"Model loaded: {model_info['model_type']}")
    print(f"Device: {model_info['device']}")
    print(f"GPU memory: {model_info['gpu_memory_allocated_gb']:.2f} GB")

    # Step 3: Prepare model for k-bit training
    print("\n--- Preparing Model for QLoRA ---")
    model = prepare_model_for_kbit_training(model)

    # Step 4: Apply LoRA adapters
    print("\n--- Applying LoRA Adapters ---")
    lora_config = get_lora_config(
        r=TRAINING_CONFIG["lora_r"],
        lora_alpha=TRAINING_CONFIG["lora_alpha"],
        lora_dropout=TRAINING_CONFIG["lora_dropout"],
        target_modules=TRAINING_CONFIG["target_modules"],
    )
    model = prepare_model_for_training(model, lora_config)

    # Step 5: Tokenize datasets
    print("\n--- Tokenizing Datasets ---")
    train_dataset = prepare_dataset_for_training(
        train_data,
        tokenizer,
        max_length=TRAINING_CONFIG["max_seq_length"]
    )
    val_dataset = prepare_dataset_for_training(
        val_data,
        tokenizer,
        max_length=TRAINING_CONFIG["max_seq_length"]
    )

    # Step 6: Setup training
    print("\n--- Configuring Training ---")
    training_args = get_training_arguments(
        output_dir=run_dir / "checkpoints",
        num_epochs=TRAINING_CONFIG["num_epochs"],
        batch_size=TRAINING_CONFIG["batch_size"],
        gradient_accumulation_steps=TRAINING_CONFIG["gradient_accumulation_steps"],
        learning_rate=TRAINING_CONFIG["learning_rate"],
        warmup_ratio=TRAINING_CONFIG["warmup_ratio"],
        logging_steps=TRAINING_CONFIG["logging_steps"],
        eval_steps=TRAINING_CONFIG["eval_steps"],
        save_steps=TRAINING_CONFIG["save_steps"],
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

    # Step 7: Train
    print("\n--- Starting Training ---")
    print(f"Epochs: {TRAINING_CONFIG['num_epochs']}")
    print(f"Effective batch size: {TRAINING_CONFIG['batch_size'] * TRAINING_CONFIG['gradient_accumulation_steps']}")
    print(f"Learning rate: {TRAINING_CONFIG['learning_rate']}")
    print()

    train_result = trainer.train()

    # Step 8: Evaluate
    print("\n--- Final Evaluation ---")
    eval_result = trainer.evaluate()

    final_train_loss = train_result.training_loss
    final_val_loss = eval_result["eval_loss"]

    print(f"Final training loss: {final_train_loss:.4f}")
    print(f"Final training perplexity: {compute_perplexity(final_train_loss):.2f}")
    print(f"Final validation loss: {final_val_loss:.4f}")
    print(f"Final validation perplexity: {compute_perplexity(final_val_loss):.2f}")

    # Step 9: Save adapter
    print("\n--- Saving Adapter ---")
    model.save_pretrained(ADAPTER_OUTPUT)
    tokenizer.save_pretrained(ADAPTER_OUTPUT)
    print(f"Adapter saved to: {ADAPTER_OUTPUT}")

    # Step 10: Save training report
    print("\n--- Saving Training Report ---")
    report_path = save_training_report(
        output_dir=run_dir,
        metrics=metrics,
        config=TRAINING_CONFIG,
        final_train_loss=final_train_loss,
        final_val_loss=final_val_loss,
    )
    print(f"Report saved to: {report_path}")

    # Copy report to adapter directory for reference
    with open(report_path) as f:
        report = json.load(f)
    with open(ADAPTER_OUTPUT / "training_report.json", 'w') as f:
        json.dump(report, f, indent=2)

    # Summary
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"Adapter: {ADAPTER_OUTPUT}")
    print(f"Run artifacts: {run_dir}")
    print(f"Training loss: {final_train_loss:.4f} (PPL: {compute_perplexity(final_train_loss):.2f})")
    print(f"Validation loss: {final_val_loss:.4f} (PPL: {compute_perplexity(final_val_loss):.2f})")

    # Memory cleanup
    del model
    del trainer
    torch.cuda.empty_cache()

    print("\n✓ Phase 3 complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
