#!/usr/bin/env python3
"""
Phase 1 Verification: Base Model Loading Test

This script verifies that the Llama 3.1 Nemotron Nano 8B model:
1. Loads successfully in 4-bit quantized mode
2. Uses GPU acceleration
3. Can perform basic inference

Run from project root:
    python scripts/verify_base_model.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch
from transformers import GenerationConfig

from src.utils.model_loader import (
    load_base_model,
    get_model_info,
    BASE_MODEL_PATH,
)


def verify_model_files() -> bool:
    """Check that all required model files are present."""
    required_files = [
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "model.safetensors.index.json",
        "model-00001-of-00004.safetensors",
        "model-00002-of-00004.safetensors",
        "model-00003-of-00004.safetensors",
        "model-00004-of-00004.safetensors",
    ]

    print(f"Checking model files at: {BASE_MODEL_PATH}")
    missing = []
    for f in required_files:
        path = BASE_MODEL_PATH / f
        if path.exists():
            print(f"  ✓ {f}")
        else:
            print(f"  ✗ {f} MISSING")
            missing.append(f)

    return len(missing) == 0


def verify_cuda() -> bool:
    """Check CUDA availability."""
    print("\n--- CUDA Verification ---")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU device: {torch.cuda.get_device_name(0)}")
        print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        return True
    else:
        print("ERROR: CUDA not available!")
        return False


def verify_model_loading() -> dict | None:
    """Load model and return diagnostics."""
    print("\n--- Loading Model (4-bit Quantization) ---")
    print("This may take 1-2 minutes...")

    try:
        model, tokenizer = load_base_model()
        info = get_model_info(model)

        print(f"\n✓ Model loaded successfully")
        print(f"  Model type: {info['model_type']}")
        print(f"  Device: {info['device']}")
        print(f"  Dtype: {info['dtype']}")
        print(f"  Total parameters: {info['num_parameters']:,}")
        print(f"  GPU memory allocated: {info['gpu_memory_allocated_gb']:.2f} GB")
        print(f"  GPU memory reserved: {info['gpu_memory_reserved_gb']:.2f} GB")

        return {"model": model, "tokenizer": tokenizer, "info": info}

    except Exception as e:
        print(f"\n✗ Model loading failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def verify_inference(model, tokenizer) -> bool:
    """Test basic inference capability."""
    print("\n--- Testing Inference ---")

    prompt = """You are a debate assistant. Generate a single argument.

Topic: Should artificial intelligence be regulated?
Stance: Pro (in favor of regulation)

Argument:"""

    print(f"Prompt: {prompt[:100]}...")

    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        generation_config = GenerationConfig(
            max_new_tokens=100,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
        )

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                generation_config=generation_config,
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        generated = response[len(prompt):]

        print(f"\n✓ Inference successful")
        print(f"Generated text:\n{generated.strip()}")

        return True

    except Exception as e:
        print(f"\n✗ Inference failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def save_verification_report(results: dict):
    """Save verification results to file."""
    report_dir = PROJECT_ROOT / "runs" / "verification"
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"base_model_verification_{timestamp}.json"

    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nReport saved to: {report_path}")


def main():
    print("=" * 60)
    print("PHASE 1: Base Model Verification")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")

    results = {
        "timestamp": datetime.now().isoformat(),
        "model_path": str(BASE_MODEL_PATH),
        "checks": {},
    }

    # Check 1: Model files
    print("\n--- Model Files Check ---")
    files_ok = verify_model_files()
    results["checks"]["model_files"] = files_ok

    if not files_ok:
        print("\nERROR: Missing model files. Cannot continue.")
        save_verification_report(results)
        return 1

    # Check 2: CUDA
    cuda_ok = verify_cuda()
    results["checks"]["cuda"] = cuda_ok

    if not cuda_ok:
        print("\nERROR: CUDA not available. Cannot continue.")
        save_verification_report(results)
        return 1

    # Check 3: Model loading
    load_result = verify_model_loading()
    results["checks"]["model_loading"] = load_result is not None

    if load_result is None:
        print("\nERROR: Model loading failed. Cannot continue.")
        save_verification_report(results)
        return 1

    results["model_info"] = load_result["info"]

    # Check 4: Inference
    inference_ok = verify_inference(load_result["model"], load_result["tokenizer"])
    results["checks"]["inference"] = inference_ok

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    all_passed = all(results["checks"].values())

    for check, passed in results["checks"].items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {check}: {status}")

    results["overall_status"] = "PASS" if all_passed else "FAIL"

    print(f"\nOverall: {'✓ ALL CHECKS PASSED' if all_passed else '✗ SOME CHECKS FAILED'}")

    save_verification_report(results)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
