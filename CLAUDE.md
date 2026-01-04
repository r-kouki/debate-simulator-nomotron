# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-agent debate simulator using LLMs with QLoRA fine-tuning and RAG. Runs entirely locally on NVIDIA GPU for academic evaluation.

## Development Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Verify base model loads
python scripts/verify_base_model.py

# Generate education domain dataset
python scripts/generate_education_dataset.py

# Train QLoRA adapter
python scripts/train_education_adapter.py

# Evaluate adapter vs base model
python scripts/evaluate_education_adapter.py

# Run multi-agent debate
python scripts/run_debate.py "Your debate topic here" --rounds 2

# Generate academic report with plots
python scripts/generate_academic_report.py

# Run API server (with LLM - takes ~1 min to load model)
python scripts/run_server.py

# Run API server (without LLM - for quick testing)
python scripts/run_server.py --no-model

# Run frontend (in separate terminal)
cd frontend && npm run dev
```

## Full Stack Development

Run backend and frontend in separate terminals:

```bash
# Terminal 1: Backend API (http://localhost:8000)
python scripts/run_server.py

# Terminal 2: Frontend (http://localhost:5173)
cd frontend && npm run dev
```

Then open http://localhost:5173 in your browser.

## Architecture

```
src/
├── agents/              # Multi-agent system
│   ├── base.py          # Agent base class, DebateContext, state machine
│   ├── router.py        # DomainRouterAgent - topic classification
│   ├── research.py      # ResearchAgent - BM25 retrieval
│   ├── debater.py       # DebaterAgent - argument generation with adapters
│   ├── factcheck.py     # FactCheckAgent - claim verification
│   ├── judge.py         # JudgeAgent - scoring and winner selection
│   └── logger.py        # LoggerAgent - artifact persistence
├── orchestration/
│   └── pipeline.py      # DebatePipeline - state machine orchestrator
├── serving/             # REST API server
│   ├── api.py           # FastAPI endpoints
│   ├── models.py        # Pydantic request/response models
│   ├── topics.py        # Topic search and data
│   ├── profile.py       # JSON-based profile storage
│   └── debate_service.py # Real-time debate session manager
├── train/
│   ├── dataset.py       # Dataset loading and tokenization
│   └── trainer.py       # Training loop with metrics
└── utils/
    └── model_loader.py  # Model/adapter loading utilities

frontend/                # React + TypeScript + Vite (Windows 98 theme)
scripts/                 # Executable scripts for each phase
models/base/             # Llama 3.1 Nemotron Nano 8B (local)
models/adapters/         # Trained LoRA adapters by domain
data/splits/             # Train/val/test JSONL datasets
runs/                    # train/, eval/, debates/, reports/ outputs
```

## Multi-Agent Pipeline

State machine flow:
```
ROUTING → RESEARCHING → DEBATING_PRO → DEBATING_CON → (repeat) → FACT_CHECKING → JUDGING → LOGGING → COMPLETE
```

Usage:
```python
from src.orchestration.pipeline import DebatePipeline
from src.utils.model_loader import load_base_model

model, tokenizer = load_base_model()
pipeline = DebatePipeline(model=model, tokenizer=tokenizer)
result = pipeline.run("Should AI be regulated?", num_rounds=2)
print(result.judge_score.winner)
```

## Key Patterns

**Model loading (4-bit QLoRA)**:
```python
from src.utils.model_loader import load_base_model, load_model_with_adapter

# Base model
model, tokenizer = load_base_model()

# With adapter
model, tokenizer = load_model_with_adapter("models/adapters/education")
```

**Dataset format** (JSONL):
```json
{"domain": "education", "topic": "...", "stance": "pro", "context": "...", "output": "..."}
```

## Metrics Produced

- Training/validation loss curves
- Perplexity (base vs adapter)
- Faithfulness score (fact-check)
- Judge scores and win rates
- All saved to `runs/reports/`

## Requirements

- Python 3.12+, NVIDIA GPU with CUDA 12.x
- ~6GB VRAM for inference, ~10GB for training
- Base model at `models/base/llama3.1-nemotron-nano-8b-v1/`
