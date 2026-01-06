"""
QLoRA training utilities for debate adapters.

Provides training loop with metric logging for academic evaluation.
"""

import json
import math
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional

import torch
from transformers import (
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    TrainerCallback,
)


@dataclass
class TrainingMetrics:
    """Container for training run metrics."""
    training_loss: list[float] = field(default_factory=list)
    validation_loss: list[float] = field(default_factory=list)
    learning_rate: list[float] = field(default_factory=list)
    steps: list[int] = field(default_factory=list)
    epochs: list[float] = field(default_factory=list)


class MetricsCallback(TrainerCallback):
    """Custom callback to track detailed training metrics."""

    def __init__(self, metrics: TrainingMetrics):
        self.metrics = metrics

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is None:
            return

        step = state.global_step

        if "loss" in logs:
            self.metrics.training_loss.append(logs["loss"])
            self.metrics.steps.append(step)
            if "epoch" in logs:
                self.metrics.epochs.append(logs["epoch"])
            if "learning_rate" in logs:
                self.metrics.learning_rate.append(logs["learning_rate"])

        if "eval_loss" in logs:
            self.metrics.validation_loss.append(logs["eval_loss"])


def compute_perplexity(loss: float) -> float:
    """Compute perplexity from cross-entropy loss."""
    return math.exp(loss)


def get_training_arguments(
    output_dir: Path,
    num_epochs: int = 3,
    batch_size: int = 4,
    gradient_accumulation_steps: int = 4,
    learning_rate: float = 2e-4,
    warmup_ratio: float = 0.1,
    logging_steps: int = 10,
    eval_steps: int = 50,
    save_steps: int = 100,
    dataloader_num_workers: int = 0,
    dataloader_pin_memory: bool = False,
) -> TrainingArguments:
    """
    Get training arguments optimized for QLoRA training on RTX 3090.

    Args:
        output_dir: Directory for checkpoints and logs
        num_epochs: Number of training epochs
        batch_size: Per-device batch size
        gradient_accumulation_steps: Steps to accumulate gradients
        learning_rate: Learning rate for AdamW
        warmup_ratio: Fraction of steps for LR warmup
        logging_steps: Log metrics every N steps
        eval_steps: Evaluate every N steps
        save_steps: Save checkpoint every N steps

    Returns:
        TrainingArguments configured for QLoRA
    """
    return TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        learning_rate=learning_rate,
        warmup_ratio=warmup_ratio,
        logging_steps=logging_steps,
        eval_strategy="steps",
        eval_steps=eval_steps,
        save_strategy="steps",
        save_steps=save_steps,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=True,
        bf16=False,  # Use fp16 for RTX 3090 compatibility
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",
        report_to="none",  # No external logging (local only)
        dataloader_num_workers=dataloader_num_workers,
        dataloader_pin_memory=dataloader_pin_memory,
        remove_unused_columns=False,
    )


def create_trainer(
    model,
    tokenizer,
    train_dataset,
    eval_dataset,
    training_args: TrainingArguments,
    metrics: TrainingMetrics,
) -> Trainer:
    """
    Create a Trainer instance configured for QLoRA training.

    Args:
        model: Model with LoRA adapters
        tokenizer: Tokenizer
        train_dataset: Training dataset
        eval_dataset: Validation dataset
        training_args: Training configuration
        metrics: Metrics container

    Returns:
        Configured Trainer instance
    """
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
        callbacks=[MetricsCallback(metrics)],
    )

    return trainer


def save_training_report(
    output_dir: Path,
    metrics: TrainingMetrics,
    config: dict,
    final_train_loss: float,
    final_val_loss: float,
    test_loss: Optional[float] = None,
    dataset_sizes: Optional[dict] = None,
):
    """
    Save comprehensive training report for academic evaluation.

    Args:
        output_dir: Directory to save report
        metrics: Training metrics
        config: Training configuration
        final_train_loss: Final training loss
        final_val_loss: Final validation loss
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "config": config,
        "dataset_sizes": dataset_sizes,
        "final_metrics": {
            "train_loss": final_train_loss,
            "train_perplexity": compute_perplexity(final_train_loss),
            "val_loss": final_val_loss,
            "val_perplexity": compute_perplexity(final_val_loss),
        },
        "training_history": {
            "steps": metrics.steps,
            "training_loss": metrics.training_loss,
            "validation_loss": metrics.validation_loss,
            "learning_rate": metrics.learning_rate,
            "epochs": metrics.epochs,
        },
    }
    if test_loss is not None:
        report["final_metrics"]["test_loss"] = test_loss
        report["final_metrics"]["test_perplexity"] = compute_perplexity(test_loss)

    report_path = output_dir / "training_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    return report_path
