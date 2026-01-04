"""
Model loading utilities for the debate simulator.

Provides standardized functions for loading the base model and LoRA adapters
in 4-bit quantized mode (QLoRA) for memory-efficient training and inference.
"""

import torch
from pathlib import Path
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)
from peft import PeftModel, LoraConfig, get_peft_model

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
BASE_MODEL_PATH = PROJECT_ROOT / "models" / "base" / "llama3.1-nemotron-nano-8b-v1"
ADAPTERS_PATH = PROJECT_ROOT / "models" / "adapters"


def get_bnb_config() -> BitsAndBytesConfig:
    """
    Returns the standard 4-bit quantization config for QLoRA.

    Uses NF4 quantization with double quantization for optimal
    memory efficiency while maintaining model quality.
    """
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )


def get_lora_config(
    r: int = 16,
    lora_alpha: int = 32,
    lora_dropout: float = 0.05,
    target_modules: list[str] | None = None,
) -> LoraConfig:
    """
    Returns LoRA configuration for adapter training.

    Args:
        r: LoRA rank (dimension of low-rank matrices)
        lora_alpha: LoRA scaling factor
        lora_dropout: Dropout probability for LoRA layers
        target_modules: Which modules to apply LoRA to

    Returns:
        LoraConfig for PEFT
    """
    if target_modules is None:
        target_modules = ["q_proj", "v_proj"]

    return LoraConfig(
        r=r,
        lora_alpha=lora_alpha,
        target_modules=target_modules,
        lora_dropout=lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
    )


def load_base_model(
    model_path: Path | str | None = None,
    device_map: str = "auto",
) -> tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Loads the base model in 4-bit quantized mode.

    Args:
        model_path: Path to model directory (defaults to project base model)
        device_map: Device placement strategy

    Returns:
        Tuple of (model, tokenizer)
    """
    if model_path is None:
        model_path = BASE_MODEL_PATH

    model_path = Path(model_path)

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        use_fast=True,
        trust_remote_code=True,
    )

    # Ensure pad token is set
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    # Load model in 4-bit
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        quantization_config=get_bnb_config(),
        device_map=device_map,
        trust_remote_code=True,
        torch_dtype=torch.float16,
    )

    return model, tokenizer


def load_model_with_adapter(
    adapter_path: Path | str,
    base_model_path: Path | str | None = None,
) -> tuple[PeftModel, AutoTokenizer]:
    """
    Loads the base model with a trained LoRA adapter.

    Args:
        adapter_path: Path to the saved adapter
        base_model_path: Path to base model (defaults to project base model)

    Returns:
        Tuple of (model with adapter, tokenizer)
    """
    model, tokenizer = load_base_model(base_model_path)
    model = PeftModel.from_pretrained(model, adapter_path)
    return model, tokenizer


def prepare_model_for_training(
    model: AutoModelForCausalLM,
    lora_config: LoraConfig | None = None,
) -> AutoModelForCausalLM:
    """
    Prepares a base model for LoRA training.

    Args:
        model: The base model (should already be quantized)
        lora_config: LoRA configuration (uses defaults if None)

    Returns:
        Model with LoRA layers ready for training
    """
    if lora_config is None:
        lora_config = get_lora_config()

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    return model


def get_model_info(model: AutoModelForCausalLM) -> dict:
    """
    Returns diagnostic information about a loaded model.
    """
    info = {
        "model_type": type(model).__name__,
        "device": str(next(model.parameters()).device),
        "dtype": str(next(model.parameters()).dtype),
        "num_parameters": sum(p.numel() for p in model.parameters()),
        "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
    }

    # Check memory usage
    if torch.cuda.is_available():
        info["gpu_memory_allocated_gb"] = torch.cuda.memory_allocated() / 1e9
        info["gpu_memory_reserved_gb"] = torch.cuda.memory_reserved() / 1e9

    return info
