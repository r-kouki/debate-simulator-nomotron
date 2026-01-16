# PYTHON BACKEND ARCHITECTURE

> **Complete Technical Documentation of the Python Backend System**
>
> This document covers model loading, training pipeline, FastAPI server, and the original multi-agent system.

---

## TABLE OF CONTENTS

1. [Model Loading System](#1-model-loading-system)
2. [QLoRA Training Pipeline](#2-qlora-training-pipeline)
3. [Original Multi-Agent System (Legacy)](#3-original-multi-agent-system-legacy)
4. [FastAPI Server](#4-fastapi-server)
5. [Utility Modules](#5-utility-modules)
6. [Scripts Reference](#6-scripts-reference)
7. [Configuration Files](#7-configuration-files)

---

## 1. MODEL LOADING SYSTEM

**File**: `src/utils/model_loader.py` (175 lines)

### 1.1 Constants and Paths

```python
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, PeftModel

# Project root detection
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Default model paths
BASE_MODEL_PATH = PROJECT_ROOT / "models" / "base" / "llama3.1-nemotron-nano-8b-v1"
ADAPTERS_PATH = PROJECT_ROOT / "models" / "adapters"
```

### 1.2 4-bit Quantization Configuration (QLoRA)

```python
def get_bnb_config() -> BitsAndBytesConfig:
    """
    Get BitsAndBytes configuration for 4-bit quantization.

    This configuration enables QLoRA (Quantized Low-Rank Adaptation):
    - load_in_4bit: Load model weights in 4-bit precision
    - bnb_4bit_quant_type: "nf4" (Normalized Float 4) is optimal for LLMs
    - bnb_4bit_compute_dtype: Compute in fp16 for speed
    - bnb_4bit_use_double_quant: Additional quantization of quantization constants

    Memory impact:
    - 8B model: ~32GB (fp32) → ~16GB (fp16) → ~6GB (4-bit)

    Returns:
        BitsAndBytesConfig for model loading
    """
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
```

### 1.3 LoRA Configuration

```python
def get_lora_config(
    r: int = 16,
    lora_alpha: int = 32,
    target_modules: list[str] | None = None,
    lora_dropout: float = 0.05,
) -> LoraConfig:
    """
    Get LoRA configuration for adapter training.

    LoRA (Low-Rank Adaptation) adds trainable rank decomposition matrices
    to attention layers, allowing efficient fine-tuning.

    Args:
        r: Rank of the low-rank matrices (higher = more capacity, more params)
        lora_alpha: Scaling factor (typically 2x r)
        target_modules: Which layers to add LoRA to (default: q_proj, v_proj)
        lora_dropout: Dropout probability for regularization

    Typical configurations:
    - r=8, alpha=16: Minimal (~1MB adapter)
    - r=16, alpha=32: Standard (~2MB adapter)
    - r=32, alpha=64: High capacity (~4MB adapter)

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
```

### 1.4 Base Model Loading

```python
def load_base_model(
    model_path: Path | str | None = None,
    device_map: str = "auto",
    torch_dtype: torch.dtype = torch.float16,
) -> tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load the base LLM in 4-bit quantized mode.

    Args:
        model_path: Path to model directory (default: BASE_MODEL_PATH)
        device_map: Device placement strategy
            - "auto": Automatically distribute across available GPUs
            - "cuda:0": Specific GPU
            - "cpu": CPU only (very slow)
        torch_dtype: Compute dtype (fp16 recommended)

    Returns:
        Tuple of (model, tokenizer)

    Example:
        model, tokenizer = load_base_model()
        inputs = tokenizer("Hello", return_tensors="pt")
        outputs = model.generate(**inputs.to(model.device))
    """
    if model_path is None:
        model_path = BASE_MODEL_PATH

    model_path = Path(model_path)

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}")

    print(f"Loading base model from: {model_path}")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True,
    )

    # Set padding token if not set
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model with quantization
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        quantization_config=get_bnb_config(),
        device_map=device_map,
        torch_dtype=torch_dtype,
        trust_remote_code=True,
    )

    print(f"Model loaded. Device: {model.device}")
    print(f"Model dtype: {model.dtype}")

    return model, tokenizer
```

### 1.5 Loading Model with Adapter

```python
def load_model_with_adapter(
    adapter_path: Path | str,
    base_model_path: Path | str | None = None,
) -> tuple[PeftModel, AutoTokenizer]:
    """
    Load base model with a trained LoRA adapter.

    The adapter modifies attention layers without changing base weights,
    allowing domain-specific behavior while keeping the base model frozen.

    Args:
        adapter_path: Path to adapter directory
            Expected files: adapter_config.json, adapter_model.safetensors
        base_model_path: Path to base model (default: BASE_MODEL_PATH)

    Returns:
        Tuple of (PeftModel with adapter, tokenizer)

    Example:
        model, tokenizer = load_model_with_adapter("models/adapters/education")
    """
    adapter_path = Path(adapter_path)

    if not adapter_path.exists():
        raise FileNotFoundError(f"Adapter not found at {adapter_path}")

    # Load base model
    model, tokenizer = load_base_model(base_model_path)

    # Load adapter
    print(f"Loading adapter from: {adapter_path}")
    model = PeftModel.from_pretrained(
        model,
        adapter_path,
        is_trainable=False,  # Inference mode
    )

    print("Adapter loaded successfully")

    return model, tokenizer
```

### 1.6 Preparing Model for Training

```python
def prepare_model_for_training(
    model: AutoModelForCausalLM,
    lora_config: LoraConfig | None = None,
) -> AutoModelForCausalLM:
    """
    Prepare a base model for QLoRA training.

    This function:
    1. Freezes all base model parameters
    2. Adds LoRA layers to specified modules
    3. Makes only LoRA parameters trainable

    Args:
        model: Base model (already loaded with quantization)
        lora_config: LoRA configuration (default: standard config)

    Returns:
        Model with LoRA layers added

    Example:
        model, tokenizer = load_base_model()
        model = prepare_model_for_training(model)
        # Now model.parameters() only contains LoRA weights
    """
    if lora_config is None:
        lora_config = get_lora_config()

    # Enable gradient checkpointing for memory efficiency
    model.gradient_checkpointing_enable()

    # Prepare for k-bit training (enables gradients through quantized layers)
    model = prepare_model_for_kbit_training(model)

    # Add LoRA layers
    model = get_peft_model(model, lora_config)

    # Print trainable parameters
    model.print_trainable_parameters()
    # Typically: "trainable params: 3,407,872 || all params: 8,030,261,248 || trainable%: 0.0424"

    return model
```

### 1.7 Utility Functions

```python
def get_adapter_list() -> list[str]:
    """
    Get list of available trained adapters.

    Returns:
        List of adapter names (directory names in ADAPTERS_PATH)
    """
    if not ADAPTERS_PATH.exists():
        return []

    adapters = []
    for path in ADAPTERS_PATH.iterdir():
        if path.is_dir():
            # Check for adapter files
            config_file = path / "adapter_config.json"
            if config_file.exists():
                adapters.append(path.name)

    return sorted(adapters)


def get_model_info(model: AutoModelForCausalLM) -> dict:
    """
    Get information about a loaded model.

    Returns:
        Dict with model statistics
    """
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    return {
        "total_parameters": total_params,
        "trainable_parameters": trainable_params,
        "trainable_percentage": trainable_params / total_params * 100,
        "device": str(model.device),
        "dtype": str(model.dtype),
        "is_quantized": hasattr(model, "is_loaded_in_4bit") and model.is_loaded_in_4bit,
    }
```

---

## 2. QLORA TRAINING PIPELINE

### 2.1 Dataset Loading

**File**: `src/train/dataset.py`

```python
from pathlib import Path
import json
from datasets import Dataset
from transformers import AutoTokenizer

def load_jsonl_dataset(path: Path | str) -> list[dict]:
    """
    Load a JSONL dataset file.

    Expected format (one JSON object per line):
    {"domain": "education", "topic": "...", "stance": "pro", "context": "...", "output": "..."}

    Args:
        path: Path to JSONL file

    Returns:
        List of dictionaries
    """
    path = Path(path)
    data = []

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))

    return data


def load_domain_dataset(
    domain: str,
    splits_dir: Path | str = Path("data/splits"),
) -> dict[str, list[dict]]:
    """
    Load train/val/test splits for a domain.

    Args:
        domain: Domain name (e.g., "education")
        splits_dir: Base directory for splits

    Returns:
        Dict with "train", "val", "test" keys
    """
    splits_dir = Path(splits_dir) / domain

    return {
        "train": load_jsonl_dataset(splits_dir / "train.jsonl"),
        "val": load_jsonl_dataset(splits_dir / "val.jsonl"),
        "test": load_jsonl_dataset(splits_dir / "test.jsonl"),
    }


def tokenize_dataset(
    data: list[dict],
    tokenizer: AutoTokenizer,
    max_length: int = 512,
) -> Dataset:
    """
    Tokenize dataset for training.

    Converts each example into input_ids and labels suitable for
    causal language model training.

    Args:
        data: List of examples with "context" and "output" keys
        tokenizer: Tokenizer to use
        max_length: Maximum sequence length

    Returns:
        HuggingFace Dataset ready for training
    """

    def format_example(example: dict) -> str:
        """Format example as prompt + completion."""
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an expert debater specializing in {example.get('domain', 'general')} topics.
<|eot_id|><|start_header_id|>user<|end_header_id|>

Topic: {example['topic']}
Stance: {example['stance']}
Context: {example.get('context', '')}

Generate a compelling argument.
<|eot_id|><|start_header_id|>assistant<|end_header_id|>

{example['output']}<|eot_id|>"""
        return prompt

    def tokenize_function(examples):
        """Tokenize a batch of examples."""
        texts = [format_example(ex) for ex in examples]

        tokenized = tokenizer(
            texts,
            truncation=True,
            max_length=max_length,
            padding="max_length",
            return_tensors="pt",
        )

        # For causal LM, labels = input_ids
        tokenized["labels"] = tokenized["input_ids"].clone()

        return tokenized

    # Convert to HuggingFace Dataset
    dataset = Dataset.from_list(data)

    # Tokenize
    tokenized_dataset = dataset.map(
        lambda batch: tokenize_function([batch]),
        batched=False,
        remove_columns=dataset.column_names,
    )

    return tokenized_dataset
```

### 2.2 Training Loop

**File**: `src/train/trainer.py`

```python
from dataclasses import dataclass, field
from pathlib import Path
from transformers import (
    Trainer,
    TrainingArguments,
    TrainerCallback,
    TrainerState,
    TrainerControl,
)

@dataclass
class TrainingMetrics:
    """Collected training metrics."""
    training_loss: list[float] = field(default_factory=list)
    validation_loss: list[float] = field(default_factory=list)
    learning_rate: list[float] = field(default_factory=list)
    steps: list[int] = field(default_factory=list)
    epochs: list[float] = field(default_factory=list)


class MetricsCallback(TrainerCallback):
    """
    Callback to collect detailed training metrics.

    Captures loss, learning rate, and step information during training
    for later visualization and analysis.
    """

    def __init__(self, metrics: TrainingMetrics):
        self.metrics = metrics

    def on_log(
        self,
        args: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        logs: dict | None = None,
        **kwargs,
    ):
        """Called when trainer logs metrics."""
        if logs is None:
            return

        # Record step
        self.metrics.steps.append(state.global_step)

        # Record epoch
        if "epoch" in logs:
            self.metrics.epochs.append(logs["epoch"])

        # Record training loss
        if "loss" in logs:
            self.metrics.training_loss.append(logs["loss"])

        # Record validation loss
        if "eval_loss" in logs:
            self.metrics.validation_loss.append(logs["eval_loss"])

        # Record learning rate
        if "learning_rate" in logs:
            self.metrics.learning_rate.append(logs["learning_rate"])


def get_training_arguments(
    output_dir: Path | str,
    num_epochs: int = 3,
    batch_size: int = 4,
    gradient_accumulation_steps: int = 4,
    learning_rate: float = 2e-4,
    warmup_ratio: float = 0.1,
    logging_steps: int = 10,
    eval_steps: int = 50,
    save_steps: int = 100,
) -> TrainingArguments:
    """
    Get training arguments for QLoRA fine-tuning.

    These settings are optimized for:
    - Single GPU training (RTX 3090/4090 with 12-24GB VRAM)
    - 8B parameter models in 4-bit quantization
    - Domain adaptation (not from-scratch training)

    Args:
        output_dir: Where to save checkpoints
        num_epochs: Number of training epochs (2-5 typical for adaptation)
        batch_size: Per-device batch size (reduce if OOM)
        gradient_accumulation_steps: Effective batch = batch_size * accumulation
        learning_rate: Peak learning rate (2e-4 to 5e-4 typical for LoRA)
        warmup_ratio: Fraction of steps for LR warmup
        logging_steps: Log metrics every N steps
        eval_steps: Evaluate on validation set every N steps
        save_steps: Save checkpoint every N steps

    Returns:
        TrainingArguments configured for QLoRA
    """
    return TrainingArguments(
        output_dir=str(output_dir),

        # Training duration
        num_train_epochs=num_epochs,
        max_steps=-1,  # Use epochs, not steps

        # Batch size
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,

        # Learning rate
        learning_rate=learning_rate,
        lr_scheduler_type="cosine",
        warmup_ratio=warmup_ratio,

        # Logging
        logging_dir=str(Path(output_dir) / "logs"),
        logging_steps=logging_steps,
        logging_first_step=True,
        report_to=["tensorboard"],

        # Evaluation
        eval_strategy="steps",
        eval_steps=eval_steps,

        # Checkpointing
        save_strategy="steps",
        save_steps=save_steps,
        save_total_limit=3,  # Keep only last 3 checkpoints
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,

        # Memory optimization
        fp16=True,
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",  # Memory-efficient optimizer

        # Other
        remove_unused_columns=False,
        dataloader_num_workers=4,
        seed=42,
    )


def train_adapter(
    model,
    tokenizer,
    train_dataset,
    val_dataset,
    output_dir: Path | str,
    training_args: TrainingArguments | None = None,
) -> tuple[Trainer, TrainingMetrics]:
    """
    Train a LoRA adapter.

    Args:
        model: Model prepared for training (with LoRA layers)
        tokenizer: Tokenizer
        train_dataset: Tokenized training dataset
        val_dataset: Tokenized validation dataset
        output_dir: Output directory
        training_args: Training arguments (default: standard config)

    Returns:
        Tuple of (trainer, metrics)

    Example:
        model, tokenizer = load_base_model()
        model = prepare_model_for_training(model)

        train_data = tokenize_dataset(train_examples, tokenizer)
        val_data = tokenize_dataset(val_examples, tokenizer)

        trainer, metrics = train_adapter(
            model, tokenizer, train_data, val_data,
            output_dir="models/adapters/my_adapter"
        )
    """
    if training_args is None:
        training_args = get_training_arguments(output_dir)

    # Create metrics tracker
    metrics = TrainingMetrics()

    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        callbacks=[MetricsCallback(metrics)],
    )

    # Train
    print("Starting training...")
    trainer.train()

    # Save final adapter
    print(f"Saving adapter to {output_dir}")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    return trainer, metrics
```

### 2.3 Evaluation

```python
import math
from tqdm import tqdm
import torch

def evaluate_perplexity(
    model,
    tokenizer,
    test_data: list[dict],
    max_length: int = 512,
) -> float:
    """
    Evaluate model perplexity on test data.

    Perplexity measures how "surprised" the model is by the test data.
    Lower = better (model predicts test data well).

    Args:
        model: Model to evaluate
        tokenizer: Tokenizer
        test_data: List of test examples
        max_length: Maximum sequence length

    Returns:
        Perplexity score
    """
    model.eval()
    total_loss = 0.0
    total_tokens = 0

    with torch.no_grad():
        for example in tqdm(test_data, desc="Evaluating"):
            # Format and tokenize
            text = format_example(example)
            inputs = tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=max_length,
            ).to(model.device)

            # Forward pass
            outputs = model(**inputs, labels=inputs["input_ids"])

            # Accumulate loss
            total_loss += outputs.loss.item() * inputs["input_ids"].size(1)
            total_tokens += inputs["input_ids"].size(1)

    # Calculate perplexity
    avg_loss = total_loss / total_tokens
    perplexity = math.exp(avg_loss)

    return perplexity


def compare_base_vs_adapter(
    base_model,
    adapter_model,
    tokenizer,
    test_data: list[dict],
) -> dict:
    """
    Compare base model vs adapter on test data.

    Args:
        base_model: Base model without adapter
        adapter_model: Model with adapter loaded
        tokenizer: Tokenizer
        test_data: Test examples

    Returns:
        Dict with comparison metrics
    """
    base_ppl = evaluate_perplexity(base_model, tokenizer, test_data)
    adapter_ppl = evaluate_perplexity(adapter_model, tokenizer, test_data)

    improvement = (base_ppl - adapter_ppl) / base_ppl * 100

    return {
        "base_perplexity": base_ppl,
        "adapter_perplexity": adapter_ppl,
        "improvement_percent": improvement,
        "adapter_is_better": adapter_ppl < base_ppl,
    }
```

---

## 3. ORIGINAL MULTI-AGENT SYSTEM (LEGACY)

**Location**: `src/agents/` and `src/orchestration/`

This is the original state-machine based system before CrewAI integration.

### 3.1 Agent State Machine

**File**: `src/agents/base.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

class AgentState(Enum):
    """States in the debate pipeline."""
    INIT = "init"
    ROUTING = "routing"
    RESEARCHING = "researching"
    DEBATING_PRO = "debating_pro"
    DEBATING_CON = "debating_con"
    FACT_CHECKING = "fact_checking"
    JUDGING = "judging"
    LOGGING = "logging"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class DebateTurn:
    """A single debate turn."""
    stance: str              # "pro" or "con"
    argument: str            # The argument text
    round_num: int           # Round number (1-indexed)
    timestamp: float = 0.0   # When generated


@dataclass
class JudgeScore:
    """Final debate score."""
    pro_score: int           # 0-100
    con_score: int           # 0-100
    winner: str              # "pro", "con", or "tie"
    reasoning: str           # Explanation


@dataclass
class DebateContext:
    """
    Shared state passed between all agents.

    This is the central data structure that flows through the pipeline.
    Each agent reads from and writes to this context.
    """
    # Core configuration
    topic: str
    num_rounds: int = 2

    # Current state
    current_state: AgentState = AgentState.INIT
    current_round: int = 0

    # Domain routing
    domain: str | None = None

    # Research
    retrieved_passages: list[dict] = field(default_factory=list)

    # Debate turns
    pro_turns: list[DebateTurn] = field(default_factory=list)
    con_turns: list[DebateTurn] = field(default_factory=list)

    # Evaluation
    judge_score: JudgeScore | None = None

    # Metrics and logging
    metrics: dict = field(default_factory=dict)
    agent_logs: list[dict] = field(default_factory=list)

    # Error handling
    error_message: str | None = None


class Agent(ABC):
    """
    Abstract base class for all agents.

    Each agent:
    1. Receives a DebateContext
    2. Performs its specific task
    3. Updates the context
    4. Returns the updated context
    """

    name: str = "BaseAgent"

    @abstractmethod
    def process(self, context: DebateContext) -> DebateContext:
        """
        Process the debate context.

        Args:
            context: Current debate state

        Returns:
            Updated debate state
        """
        pass

    def log(self, context: DebateContext, message: str):
        """Add a log entry to the context."""
        context.agent_logs.append({
            "agent": self.name,
            "message": message,
            "state": context.current_state.value,
        })
```

### 3.2 Domain Router Agent

**File**: `src/agents/router.py`

```python
class DomainRouterAgent(Agent):
    """
    Routes debates to appropriate domain adapters.

    Analyzes the topic and selects the best domain:
    - education, medicine, ecology, technology, or general debate
    """

    name = "DomainRouter"

    # Domain keywords (simplified)
    DOMAIN_KEYWORDS = {
        "education": ["school", "student", "university", "learning"],
        "medicine": ["health", "doctor", "hospital", "treatment"],
        "ecology": ["climate", "environment", "pollution", "species"],
        "technology": ["ai", "software", "digital", "automation"],
    }

    def process(self, context: DebateContext) -> DebateContext:
        """Classify topic into domain."""
        self.log(context, f"Routing topic: {context.topic}")

        topic_lower = context.topic.lower()

        # Score each domain
        scores = {}
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in topic_lower)
            if score > 0:
                scores[domain] = score

        # Select best domain
        if scores:
            context.domain = max(scores, key=scores.get)
        else:
            context.domain = "debate"  # General fallback

        self.log(context, f"Selected domain: {context.domain}")
        context.current_state = AgentState.RESEARCHING

        return context
```

### 3.3 Research Agent

**File**: `src/agents/research.py`

```python
from rank_bm25 import BM25Okapi

class ResearchAgent(Agent):
    """
    Retrieves relevant passages for the debate topic.

    Uses BM25 (Best Matching 25) for document retrieval.
    """

    name = "Researcher"

    def __init__(self, corpus: list[dict] | None = None):
        """
        Initialize with document corpus.

        Args:
            corpus: List of documents with "text" and "source" keys
        """
        self.corpus = corpus or []
        self._bm25 = None

    def _build_index(self):
        """Build BM25 index from corpus."""
        if not self.corpus:
            return

        # Tokenize documents
        tokenized = [doc["text"].lower().split() for doc in self.corpus]
        self._bm25 = BM25Okapi(tokenized)

    def process(self, context: DebateContext) -> DebateContext:
        """Retrieve relevant passages."""
        self.log(context, "Starting research")

        if self._bm25 is None:
            self._build_index()

        if self._bm25 is None:
            self.log(context, "No corpus available")
            context.current_state = AgentState.DEBATING_PRO
            return context

        # Tokenize query
        query_tokens = context.topic.lower().split()

        # Retrieve top passages
        scores = self._bm25.get_scores(query_tokens)

        # Get top 5 passages
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:5]

        context.retrieved_passages = [
            {
                "text": self.corpus[i]["text"],
                "source": self.corpus[i].get("source", "unknown"),
                "score": scores[i],
            }
            for i in top_indices
        ]

        self.log(context, f"Retrieved {len(context.retrieved_passages)} passages")
        context.current_state = AgentState.DEBATING_PRO

        return context
```

### 3.4 Debater Agent

**File**: `src/agents/debater.py`

```python
import time

class DebaterAgent(Agent):
    """
    Generates debate arguments.

    Uses the loaded LLM with optional domain adapter.
    """

    name = "Debater"

    def __init__(self, model, tokenizer, stance: str = "pro"):
        """
        Initialize debater.

        Args:
            model: LLM model
            tokenizer: Tokenizer
            stance: "pro" or "con"
        """
        self.model = model
        self.tokenizer = tokenizer
        self.stance = stance
        self.name = f"Debater_{stance.upper()}"

    def process(self, context: DebateContext) -> DebateContext:
        """Generate a debate argument."""
        self.log(context, f"Generating {self.stance} argument for round {context.current_round + 1}")

        # Build prompt
        prompt = self._build_prompt(context)

        # Generate
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=200,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # Decode
        argument = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        ).strip()

        # Create turn
        turn = DebateTurn(
            stance=self.stance,
            argument=argument,
            round_num=context.current_round + 1,
            timestamp=time.time(),
        )

        # Add to context
        if self.stance == "pro":
            context.pro_turns.append(turn)
            context.current_state = AgentState.DEBATING_CON
        else:
            context.con_turns.append(turn)
            context.current_round += 1

            # Check if more rounds
            if context.current_round < context.num_rounds:
                context.current_state = AgentState.DEBATING_PRO
            else:
                context.current_state = AgentState.FACT_CHECKING

        self.log(context, f"Generated argument: {argument[:100]}...")

        return context

    def _build_prompt(self, context: DebateContext) -> str:
        """Build generation prompt."""
        # Get research context
        research = "\n".join(p["text"] for p in context.retrieved_passages[:3])

        # Get opponent's last argument (if rebuttal)
        opponent_arg = ""
        opponent_turns = context.con_turns if self.stance == "pro" else context.pro_turns
        if opponent_turns:
            opponent_arg = opponent_turns[-1].argument

        stance_name = "FOR" if self.stance == "pro" else "AGAINST"

        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a skilled debater arguing {stance_name} the topic.
<|eot_id|><|start_header_id|>user<|end_header_id|>

Topic: {context.topic}

Research:
{research}

{"Previous argument from opponent: " + opponent_arg if opponent_arg else "This is your opening statement."}

Generate a compelling argument {stance_name} this topic.
<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
```

### 3.5 Pipeline Orchestrator

**File**: `src/orchestration/pipeline.py`

```python
class DebatePipeline:
    """
    Orchestrates the full debate pipeline.

    Manages state transitions and agent execution.
    """

    def __init__(
        self,
        model,
        tokenizer,
        corpus: list[dict] | None = None,
    ):
        """
        Initialize pipeline with model and agents.

        Args:
            model: LLM model
            tokenizer: Tokenizer
            corpus: Optional document corpus for research
        """
        self.model = model
        self.tokenizer = tokenizer

        # Initialize agents
        self.router = DomainRouterAgent()
        self.researcher = ResearchAgent(corpus)
        self.pro_debater = DebaterAgent(model, tokenizer, stance="pro")
        self.con_debater = DebaterAgent(model, tokenizer, stance="con")
        self.fact_checker = FactCheckAgent()
        self.judge = JudgeAgent()
        self.logger = LoggerAgent()

    def run(
        self,
        topic: str,
        num_rounds: int = 2,
    ) -> DebateContext:
        """
        Run a complete debate.

        Args:
            topic: Debate topic
            num_rounds: Number of debate rounds

        Returns:
            Final DebateContext with results
        """
        # Initialize context
        context = DebateContext(
            topic=topic,
            num_rounds=num_rounds,
            current_state=AgentState.ROUTING,
        )

        # State machine loop
        while context.current_state not in (AgentState.COMPLETE, AgentState.ERROR):
            context = self._process_state(context)

        return context

    def _process_state(self, context: DebateContext) -> DebateContext:
        """Process current state and transition."""
        state = context.current_state

        try:
            if state == AgentState.ROUTING:
                return self.router.process(context)
            elif state == AgentState.RESEARCHING:
                return self.researcher.process(context)
            elif state == AgentState.DEBATING_PRO:
                return self.pro_debater.process(context)
            elif state == AgentState.DEBATING_CON:
                return self.con_debater.process(context)
            elif state == AgentState.FACT_CHECKING:
                return self.fact_checker.process(context)
            elif state == AgentState.JUDGING:
                return self.judge.process(context)
            elif state == AgentState.LOGGING:
                return self.logger.process(context)
            else:
                context.current_state = AgentState.ERROR
                context.error_message = f"Unknown state: {state}"
                return context

        except Exception as e:
            context.current_state = AgentState.ERROR
            context.error_message = str(e)
            return context
```

---

## 4. FASTAPI SERVER

**File**: `src/serving/api.py`

### 4.1 Server Configuration

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

app = FastAPI(
    title="Debate Simulator API",
    description="Multi-agent debate orchestration with LLM",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4.2 Request/Response Models

**File**: `src/serving/models.py`

```python
from pydantic import BaseModel, Field
from typing import Optional

class StartDebateRequest(BaseModel):
    """Request to start a new debate."""
    topic: str = Field(..., min_length=5, description="Debate topic")
    rounds: int = Field(2, ge=1, le=5, description="Number of rounds")
    use_internet: bool = Field(False, description="Enable internet research")

class StartDebateResponse(BaseModel):
    """Response after starting debate."""
    debate_id: str
    topic: str
    domain: str
    status: str

class SendTurnRequest(BaseModel):
    """Request to send a turn (human or trigger AI)."""
    content: Optional[str] = None  # Human turn content
    generate_ai: bool = True       # Generate AI response

class SendTurnResponse(BaseModel):
    """Response with turn results."""
    pro_argument: Optional[str] = None
    con_argument: Optional[str] = None
    round_num: int
    is_complete: bool

class ScoreDebateResponse(BaseModel):
    """Final debate score."""
    pro_score: int
    con_score: int
    winner: str
    reasoning: str
    fact_check: dict

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    gpu_available: bool
```

### 4.3 API Endpoints

```python
from src.serving.debate_service import DebateService

# Global service instance
debate_service: DebateService | None = None

@app.on_event("startup")
async def startup():
    """Initialize service on startup."""
    global debate_service
    debate_service = DebateService()

# Health check
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and model status."""
    return HealthResponse(
        status="healthy",
        model_loaded=debate_service.is_model_loaded(),
        gpu_available=torch.cuda.is_available(),
    )

# Start debate
@app.post("/debates", response_model=StartDebateResponse)
async def start_debate(request: StartDebateRequest):
    """Start a new debate session."""
    try:
        debate_id = debate_service.create_debate(
            topic=request.topic,
            num_rounds=request.rounds,
            use_internet=request.use_internet,
        )

        session = debate_service.get_session(debate_id)

        return StartDebateResponse(
            debate_id=debate_id,
            topic=session.topic,
            domain=session.domain,
            status="created",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Send turn
@app.post("/debates/{debate_id}/turns", response_model=SendTurnResponse)
async def send_turn(debate_id: str, request: SendTurnRequest):
    """Send a turn and optionally generate AI response."""
    session = debate_service.get_session(debate_id)
    if not session:
        raise HTTPException(status_code=404, detail="Debate not found")

    try:
        result = debate_service.process_turn(
            debate_id=debate_id,
            human_content=request.content,
            generate_ai=request.generate_ai,
        )

        return SendTurnResponse(
            pro_argument=result.get("pro_argument"),
            con_argument=result.get("con_argument"),
            round_num=result.get("round_num", 1),
            is_complete=result.get("is_complete", False),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Stream turns (Server-Sent Events)
@app.post("/debates/{debate_id}/turns/stream")
async def stream_turn(debate_id: str, request: SendTurnRequest):
    """Stream AI response as Server-Sent Events."""
    session = debate_service.get_session(debate_id)
    if not session:
        raise HTTPException(status_code=404, detail="Debate not found")

    async def event_generator():
        """Generate SSE events."""
        async for chunk in debate_service.stream_turn(debate_id, request):
            yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: {\"done\": true}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )

# Score debate
@app.post("/debates/{debate_id}/score", response_model=ScoreDebateResponse)
async def score_debate(debate_id: str):
    """Get final debate score."""
    session = debate_service.get_session(debate_id)
    if not session:
        raise HTTPException(status_code=404, detail="Debate not found")

    try:
        score = debate_service.score_debate(debate_id)

        return ScoreDebateResponse(
            pro_score=score.pro_score,
            con_score=score.con_score,
            winner=score.winner,
            reasoning=score.reasoning,
            fact_check=score.fact_check,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Topic search
@app.get("/topics/search")
async def search_topics(q: str, limit: int = 10):
    """Search suggested debate topics."""
    from src.serving.topics import TopicSearchService

    service = TopicSearchService()
    results = service.search(q, limit=limit)

    return {"topics": results}
```

### 4.4 Debate Service

**File**: `src/serving/debate_service.py`

```python
from dataclasses import dataclass, field
from typing import Optional, AsyncIterator
import uuid

@dataclass
class DebateSession:
    """Active debate session."""
    id: str
    topic: str
    domain: str
    num_rounds: int
    current_round: int = 0
    pro_arguments: list[str] = field(default_factory=list)
    con_arguments: list[str] = field(default_factory=list)
    is_complete: bool = False
    use_internet: bool = False

class DebateService:
    """
    Manages debate sessions and LLM interactions.
    """

    def __init__(self):
        self._sessions: dict[str, DebateSession] = {}
        self._crew: DebateCrew | None = None
        self._model_loaded = False

    def is_model_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model_loaded

    def _ensure_crew(self, use_internet: bool = False):
        """Lazy-load DebateCrew."""
        if self._crew is None:
            self._crew = DebateCrew(use_internet=use_internet)
            self._model_loaded = True

    def create_debate(
        self,
        topic: str,
        num_rounds: int,
        use_internet: bool,
    ) -> str:
        """Create a new debate session."""
        self._ensure_crew(use_internet)

        debate_id = str(uuid.uuid4())

        # Analyze topic for domain
        from src.crew.agents.topic_analyst import analyze_topic
        analysis = analyze_topic(topic)

        session = DebateSession(
            id=debate_id,
            topic=analysis.corrected_topic,
            domain=analysis.domain_hint,
            num_rounds=num_rounds,
            use_internet=use_internet,
        )

        self._sessions[debate_id] = session

        return debate_id

    def get_session(self, debate_id: str) -> Optional[DebateSession]:
        """Get session by ID."""
        return self._sessions.get(debate_id)

    def process_turn(
        self,
        debate_id: str,
        human_content: str | None,
        generate_ai: bool,
    ) -> dict:
        """Process a debate turn."""
        session = self._sessions[debate_id]

        # ... implementation details ...

        return {
            "pro_argument": pro_arg,
            "con_argument": con_arg,
            "round_num": session.current_round,
            "is_complete": session.is_complete,
        }

    async def stream_turn(
        self,
        debate_id: str,
        request,
    ) -> AsyncIterator[dict]:
        """Stream turn generation."""
        # ... streaming implementation ...
        pass

    def score_debate(self, debate_id: str):
        """Score completed debate."""
        session = self._sessions[debate_id]

        from src.crew.agents.judge_agent import judge_debate
        from src.crew.agents.factcheck_agent import compute_faithfulness_score

        # Fact-check both sides
        fact_check = {
            "pro": compute_faithfulness_score(
                " ".join(session.pro_arguments),
                "",  # Research context
            ),
            "con": compute_faithfulness_score(
                " ".join(session.con_arguments),
                "",
            ),
        }

        # Judge
        score = judge_debate(
            session.pro_arguments,
            session.con_arguments,
            fact_check,
        )

        score.fact_check = fact_check

        return score
```

---

## 5. UTILITY MODULES

### 5.1 Web Search

**File**: `src/utils/web_search.py`

```python
from duckduckgo_search import DDGS

def search_duckduckgo(
    query: str,
    max_results: int = 5,
    region: str = "wt-wt",
) -> list[dict]:
    """
    Search DuckDuckGo for web results.

    Args:
        query: Search query
        max_results: Maximum results to return
        region: Region code (wt-wt = worldwide)

    Returns:
        List of results with title, snippet, url
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                query,
                region=region,
                max_results=max_results,
            ))

        return [
            {
                "title": r.get("title", ""),
                "snippet": r.get("body", ""),
                "url": r.get("href", ""),
            }
            for r in results
        ]

    except Exception as e:
        print(f"DuckDuckGo search error: {e}")
        return []
```

---

## 6. SCRIPTS REFERENCE

### 6.1 run_debate_crew.py

Main CLI entry point for running debates.

```bash
# Usage
python scripts/run_debate_crew.py "Topic" [OPTIONS]

# Options
--rounds N          Number of debate rounds (default: 2)
--use-internet      Enable web search
--recommend-guests  Find expert recommendations
--output-dir PATH   Output directory
--quiet             Reduce output verbosity
```

### 6.2 run_server.py

Start the FastAPI server.

```bash
# Full mode (loads LLM)
python scripts/run_server.py

# Quick mode (mocked LLM)
python scripts/run_server.py --no-model

# Custom port
python scripts/run_server.py --port 8080
```

### 6.3 Training Scripts

```bash
# Generate training dataset
python scripts/generate_education_dataset.py

# Train adapter
python scripts/train_education_adapter.py

# Evaluate adapter
python scripts/evaluate_education_adapter.py

# Generate report with visualizations
python scripts/generate_academic_report.py
```

### 6.4 verify_base_model.py

Test that the base model loads correctly.

```bash
python scripts/verify_base_model.py

# Expected output:
# Loading base model...
# Model loaded. Device: cuda:0
# Model dtype: torch.float16
# Generating test output...
# Test successful!
```

---

## 7. CONFIGURATION FILES

### 7.1 Training Config

**File**: `configs/training_config.yaml`

```yaml
# Training configuration
training:
  num_epochs: 3
  batch_size: 4
  gradient_accumulation_steps: 4
  learning_rate: 2e-4
  warmup_ratio: 0.1
  max_length: 512

# LoRA configuration
lora:
  r: 16
  alpha: 32
  dropout: 0.05
  target_modules:
    - q_proj
    - v_proj

# Evaluation
evaluation:
  eval_steps: 50
  save_steps: 100
  metric: eval_loss

# Output
output:
  dir: models/adapters
  save_total_limit: 3
```

### 7.2 requirements.txt (Key Dependencies)

```
# Core ML
torch>=2.0.0
transformers>=4.40.0
peft>=0.10.0
bitsandbytes>=0.43.0
accelerate>=0.30.0

# CrewAI (installed with --no-deps)
crewai==1.8.0
crewai-tools==1.8.0

# API
fastapi>=0.110.0
uvicorn>=0.29.0
pydantic>=2.0.0

# Search
duckduckgo-search>=5.0.0
wikipedia>=1.4.0
rank-bm25>=0.2.2

# Utilities
python-dotenv>=1.0.0
tqdm>=4.66.0
datasets>=2.18.0
```

---

*Continue to [DETAILED_PROJECT_EXPLICATION_FRONTEND.md](./DETAILED_PROJECT_EXPLICATION_FRONTEND.md) for frontend documentation.*
