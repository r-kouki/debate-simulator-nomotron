"""
Dataset utilities for debate turn training.

Provides functions to load JSONL datasets and prepare them for training.
"""

import json
from pathlib import Path
from datasets import Dataset


def load_debate_jsonl(path: Path) -> Dataset:
    """Load a JSONL debate dataset into HuggingFace Dataset format."""
    records = []
    with open(path) as f:
        for line in f:
            records.append(json.loads(line))
    return Dataset.from_list(records)


def load_sft_jsonl(path: Path) -> Dataset:
    """Load a JSONL SFT dataset with a text field."""
    records = []
    with open(path) as f:
        for line in f:
            records.append(json.loads(line))
    return Dataset.from_list(records)


def format_debate_prompt(example: dict) -> str:
    """
    Format a debate example into a training prompt.

    Input format:
        domain, topic, stance, context -> output

    Output format (chat-style):
        <|begin_of_text|>...<|end_of_text|>
    """
    system_msg = f"You are an expert debate assistant specializing in {example['domain']}. Generate compelling, well-reasoned arguments."

    user_msg = f"""Topic: {example['topic']}
Stance: {example['stance'].upper()}
Context: {example['context']}

Generate a single, persuasive argument for this position."""

    assistant_msg = example['output']

    # Llama 3.1 chat format
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{system_msg}<|eot_id|><|start_header_id|>user<|end_header_id|>

{user_msg}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

{assistant_msg}<|eot_id|><|end_of_text|>"""

    return prompt


def prepare_dataset_for_training(
    dataset: Dataset,
    tokenizer,
    max_length: int = 512,
) -> Dataset:
    """
    Tokenize and prepare dataset for causal LM training.

    Args:
        dataset: Raw debate dataset
        tokenizer: Model tokenizer
        max_length: Maximum sequence length

    Returns:
        Tokenized dataset ready for training
    """
    def tokenize_function(examples):
        # Format each example
        texts = [format_debate_prompt({
            'domain': d,
            'topic': t,
            'stance': s,
            'context': c,
            'output': o
        }) for d, t, s, c, o in zip(
            examples['domain'],
            examples['topic'],
            examples['stance'],
            examples['context'],
            examples['output']
        )]

        # Tokenize
        tokenized = tokenizer(
            texts,
            truncation=True,
            max_length=max_length,
            padding="max_length",
        )

        # For causal LM, labels = input_ids
        tokenized["labels"] = tokenized["input_ids"].copy()

        return tokenized

    return dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset.column_names,
        desc="Tokenizing"
    )


def prepare_sft_dataset_for_training(
    dataset: Dataset,
    tokenizer,
    max_length: int = 512,
) -> Dataset:
    """
    Tokenize and prepare SFT dataset for causal LM training.

    Expects a "text" field containing chat-formatted content.
    """
    def tokenize_function(examples):
        texts = examples.get("text", [])
        tokenized = tokenizer(
            texts,
            truncation=True,
            max_length=max_length,
            padding="max_length",
        )
        tokenized["labels"] = tokenized["input_ids"].copy()
        return tokenized

    return dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset.column_names,
        desc="Tokenizing"
    )
