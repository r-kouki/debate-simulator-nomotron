#!/usr/bin/env python3
"""
Phase 4: Education Adapter Evaluation

Evaluates the trained LoRA adapter on the held-out test set.

Produces:
- Test loss and perplexity
- Qualitative generation examples
- Comparison with base model (no adapter)

Run from project root:
    python scripts/evaluate_education_adapter.py
"""

import sys
import json
import math
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch
from torch.utils.data import DataLoader
from transformers import DataCollatorForLanguageModeling, GenerationConfig
from peft import PeftModel
from tqdm import tqdm

from src.utils.model_loader import (
    load_base_model,
    get_model_info,
    BASE_MODEL_PATH,
    ADAPTERS_PATH,
)
from src.train.dataset import (
    load_debate_jsonl,
    prepare_dataset_for_training,
    format_debate_prompt,
)

# Configuration
DOMAIN = "education"
DATA_DIR = PROJECT_ROOT / "data" / "splits" / DOMAIN
ADAPTER_PATH = ADAPTERS_PATH / DOMAIN
EVAL_DIR = PROJECT_ROOT / "runs" / "eval" / DOMAIN


@dataclass
class EvalResult:
    """Container for evaluation results."""
    model_type: str  # "base" or "adapter"
    test_loss: float
    test_perplexity: float
    num_samples: int


@dataclass
class GenerationExample:
    """Container for qualitative generation example."""
    topic: str
    stance: str
    context: str
    reference: str
    base_generation: str
    adapter_generation: str


def compute_test_loss(model, tokenizer, test_dataset, batch_size: int = 2) -> float:
    """
    Compute average loss on test dataset.

    Args:
        model: Model to evaluate
        tokenizer: Tokenizer
        test_dataset: Tokenized test dataset
        batch_size: Evaluation batch size

    Returns:
        Average loss value
    """
    model.eval()

    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    # Create DataLoader
    dataloader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        collate_fn=data_collator,
        shuffle=False,
    )

    total_loss = 0.0
    total_samples = 0

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Evaluating"):
            batch = {k: v.to(model.device) for k, v in batch.items()}

            outputs = model(**batch)
            loss = outputs.loss

            batch_size_actual = batch["input_ids"].size(0)
            total_loss += loss.item() * batch_size_actual
            total_samples += batch_size_actual

    avg_loss = total_loss / total_samples
    return avg_loss


def generate_response(
    model,
    tokenizer,
    topic: str,
    stance: str,
    context: str,
    max_new_tokens: int = 150,
) -> str:
    """
    Generate a debate argument using the model.

    Args:
        model: Model to use for generation
        tokenizer: Tokenizer
        topic: Debate topic
        stance: "pro" or "con"
        context: Context/instructions
        max_new_tokens: Maximum tokens to generate

    Returns:
        Generated text
    """
    system_msg = f"You are an expert debate assistant specializing in education. Generate compelling, well-reasoned arguments."

    user_msg = f"""Topic: {topic}
Stance: {stance.upper()}
Context: {context}

Generate a single, persuasive argument for this position."""

    # Llama 3.1 chat format
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{system_msg}<|eot_id|><|start_header_id|>user<|end_header_id|>

{user_msg}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    generation_config = GenerationConfig(
        max_new_tokens=max_new_tokens,
        temperature=0.7,
        top_p=0.9,
        do_sample=True,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            generation_config=generation_config,
        )

    full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Extract just the assistant's response
    # Find the last "Generate a single, persuasive argument" and take text after it
    marker = "Generate a single, persuasive argument for this position."
    if marker in full_response:
        response = full_response.split(marker)[-1].strip()
    else:
        response = full_response[len(prompt):].strip()

    return response


def generate_qualitative_examples(
    base_model,
    adapter_model,
    tokenizer,
    test_data,
    num_examples: int = 5,
) -> list[GenerationExample]:
    """
    Generate qualitative comparison examples.

    Args:
        base_model: Base model without adapter
        adapter_model: Model with trained adapter
        tokenizer: Tokenizer
        test_data: Raw test dataset
        num_examples: Number of examples to generate

    Returns:
        List of GenerationExample objects
    """
    examples = []

    # Select diverse examples (mix of pro/con)
    indices = list(range(min(num_examples, len(test_data))))

    for idx in tqdm(indices, desc="Generating examples"):
        sample = test_data[idx]

        base_gen = generate_response(
            base_model, tokenizer,
            sample['topic'], sample['stance'], sample['context']
        )

        adapter_gen = generate_response(
            adapter_model, tokenizer,
            sample['topic'], sample['stance'], sample['context']
        )

        examples.append(GenerationExample(
            topic=sample['topic'],
            stance=sample['stance'],
            context=sample['context'],
            reference=sample['output'],
            base_generation=base_gen,
            adapter_generation=adapter_gen,
        ))

    return examples


def save_evaluation_report(
    output_dir: Path,
    base_result: EvalResult,
    adapter_result: EvalResult,
    examples: list[GenerationExample],
):
    """Save comprehensive evaluation report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "domain": DOMAIN,
        "adapter_path": str(ADAPTER_PATH),
        "results": {
            "base_model": asdict(base_result),
            "adapter_model": asdict(adapter_result),
            "improvement": {
                "loss_reduction": base_result.test_loss - adapter_result.test_loss,
                "loss_reduction_pct": (base_result.test_loss - adapter_result.test_loss) / base_result.test_loss * 100,
                "perplexity_reduction": base_result.test_perplexity - adapter_result.test_perplexity,
            }
        },
        "qualitative_examples": [asdict(ex) for ex in examples],
    }

    report_path = output_dir / "evaluation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    # Also save human-readable examples
    examples_path = output_dir / "generation_examples.md"
    with open(examples_path, 'w') as f:
        f.write("# Qualitative Generation Examples\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")

        for i, ex in enumerate(examples, 1):
            f.write(f"## Example {i}\n\n")
            f.write(f"**Topic:** {ex.topic}\n\n")
            f.write(f"**Stance:** {ex.stance.upper()}\n\n")
            f.write(f"**Context:** {ex.context}\n\n")
            f.write(f"### Reference (Ground Truth)\n{ex.reference}\n\n")
            f.write(f"### Base Model Generation\n{ex.base_generation}\n\n")
            f.write(f"### Adapter Model Generation\n{ex.adapter_generation}\n\n")
            f.write("---\n\n")

    return report_path, examples_path


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    eval_dir = EVAL_DIR / timestamp

    print("=" * 60)
    print("PHASE 4: Education Adapter Evaluation")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Adapter: {ADAPTER_PATH}")
    print(f"Output: {eval_dir}")

    eval_dir.mkdir(parents=True, exist_ok=True)

    # Load test data
    print("\n--- Loading Test Data ---")
    test_data_raw = load_debate_jsonl(DATA_DIR / "test.jsonl")
    print(f"Test samples: {len(test_data_raw)}")

    # Load base model
    print("\n--- Loading Base Model ---")
    base_model, tokenizer = load_base_model()
    print(f"Base model loaded: {get_model_info(base_model)['device']}")

    # Tokenize test data
    print("\n--- Tokenizing Test Data ---")
    test_dataset = prepare_dataset_for_training(
        test_data_raw,
        tokenizer,
        max_length=512
    )

    # Evaluate base model
    print("\n--- Evaluating Base Model ---")
    base_loss = compute_test_loss(base_model, tokenizer, test_dataset)
    base_result = EvalResult(
        model_type="base",
        test_loss=base_loss,
        test_perplexity=math.exp(base_loss),
        num_samples=len(test_dataset),
    )
    print(f"Base model - Loss: {base_loss:.4f}, Perplexity: {base_result.test_perplexity:.2f}")

    # Load adapter
    print("\n--- Loading Adapter ---")
    adapter_model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
    print(f"Adapter loaded from: {ADAPTER_PATH}")

    # Evaluate adapter model
    print("\n--- Evaluating Adapter Model ---")
    adapter_loss = compute_test_loss(adapter_model, tokenizer, test_dataset)
    adapter_result = EvalResult(
        model_type="adapter",
        test_loss=adapter_loss,
        test_perplexity=math.exp(adapter_loss),
        num_samples=len(test_dataset),
    )
    print(f"Adapter model - Loss: {adapter_loss:.4f}, Perplexity: {adapter_result.test_perplexity:.2f}")

    # Generate qualitative examples
    print("\n--- Generating Qualitative Examples ---")
    # Need to reload base model without adapter for comparison
    del base_model
    torch.cuda.empty_cache()

    base_model_fresh, _ = load_base_model()
    examples = generate_qualitative_examples(
        base_model_fresh,
        adapter_model,
        tokenizer,
        test_data_raw,
        num_examples=5,
    )

    # Save results
    print("\n--- Saving Evaluation Report ---")
    report_path, examples_path = save_evaluation_report(
        eval_dir,
        base_result,
        adapter_result,
        examples,
    )
    print(f"Report saved to: {report_path}")
    print(f"Examples saved to: {examples_path}")

    # Summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"\n{'Model':<15} {'Loss':>10} {'Perplexity':>12}")
    print("-" * 40)
    print(f"{'Base':<15} {base_result.test_loss:>10.4f} {base_result.test_perplexity:>12.2f}")
    print(f"{'+ Adapter':<15} {adapter_result.test_loss:>10.4f} {adapter_result.test_perplexity:>12.2f}")
    print("-" * 40)

    improvement = base_result.test_loss - adapter_result.test_loss
    improvement_pct = improvement / base_result.test_loss * 100
    print(f"\nImprovement: {improvement:.4f} loss ({improvement_pct:.1f}%)")

    # Cleanup
    del base_model_fresh
    del adapter_model
    torch.cuda.empty_cache()

    print("\n✓ Phase 4 complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
