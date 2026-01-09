# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-agent debate simulator using LLMs with QLoRA fine-tuning and RAG. Runs entirely locally on NVIDIA GPU for academic evaluation. Frontend is a Windows 98-themed React app with draggable/resizable windows.

## Development Commands

```bash
# Python setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Verify base model loads
python scripts/verify_base_model.py

# Training pipeline
python scripts/generate_education_dataset.py  # Generate domain dataset
python scripts/train_education_adapter.py     # Train QLoRA adapter
python scripts/evaluate_education_adapter.py  # Evaluate adapter vs base

# Run multi-agent debate (original system)
python scripts/run_debate.py "Your debate topic here" --rounds 2

# Run CrewAI-based debate (standalone mode - recommended!)
python scripts/run_debate_crew.py "Your debate topic here" --rounds 2

# Generate academic report with plots
python scripts/generate_academic_report.py

# Python API server
python scripts/run_server.py             # Full mode (with LLM, ~1 min load)
python scripts/run_server.py --no-model  # Quick mode (mocked LLM)

# Frontend
cd frontend && npm install && npm run dev  # http://localhost:5173
cd frontend && npm run test                 # Vitest tests
cd frontend && npm run lint                 # ESLint
cd frontend && npm run build                # Typecheck + production build
```

## Full Stack Development

Two backend options:

**Option 1: Python backend** (local LLM with QLoRA adapters)
```bash
# Terminal 1: Python API (http://localhost:8000)
python scripts/run_server.py

# Terminal 2: Frontend (http://localhost:5173)
cd frontend && npm run dev
```

**Option 2: Node.js API** (uses OpenRouter for LLM)
```bash
# Terminal 1: Build shared contracts
cd frontend/packages/contracts && npm install && npm run build

# Terminal 2: Node API (http://localhost:4000)
cd frontend/apps/api
npm install && cp .env.example .env
npm run prisma:generate && npm run prisma:migrate
npm run dev

# Terminal 3: Frontend
cd frontend && VITE_API_BASE_URL=http://localhost:4000 npm run dev
```

Without a backend, frontend falls back to mock mode automatically.

## Architecture

```
src/                           # Python backend
├── agents/                    # Multi-agent system
│   ├── base.py                # Agent base class, DebateContext, state machine
│   ├── router.py              # DomainRouterAgent - topic classification
│   ├── research.py            # ResearchAgent - BM25 retrieval
│   ├── debater.py             # DebaterAgent - argument generation with adapters
│   ├── factcheck.py           # FactCheckAgent - claim verification
│   ├── judge.py               # JudgeAgent - scoring and winner selection
│   └── logger.py              # LoggerAgent - artifact persistence
├── orchestration/
│   └── pipeline.py            # DebatePipeline - state machine orchestrator
├── serving/                   # FastAPI server
│   ├── api.py                 # REST endpoints
│   ├── models.py              # Pydantic request/response models
│   ├── topics.py              # Topic search and data
│   ├── profile.py             # JSON-based profile storage
│   └── debate_service.py      # Real-time debate session manager
├── train/
│   ├── dataset.py             # Dataset loading and tokenization
│   └── trainer.py             # Training loop with metrics
└── utils/
    └── model_loader.py        # Model/adapter loading utilities

frontend/                      # React + TypeScript + Vite
├── src/
│   ├── api/                   # API adapters (mock, openRouter), React Query hooks
│   ├── components/            # WindowFrame, Taskbar, Desktop, StartMenu
│   ├── features/              # debate/, topics/, profile/, settings/
│   └── state/                 # Zustand stores (window, debate, settings, profile)
├── apps/api/                  # Optional Fastify backend (OpenRouter LLM)
│   ├── src/routes/            # health, profile, topics, debates
│   ├── src/agents/            # researchAgent, debaterAgent, judgeAgent
│   └── prisma/                # SQLite schema
└── packages/contracts/        # Shared Zod schemas

scripts/                       # Runnable Python scripts
models/base/                   # Llama 3.1 Nemotron Nano 8B (local)
models/adapters/               # Trained LoRA adapters by domain
data/splits/                   # Train/val/test JSONL datasets
runs/                          # train/, eval/, debates/, reports/ outputs
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

## Testing

```bash
# Python smoke tests
python scripts/verify_base_model.py    # Verifies model loads
python qlora_smoke_test.py             # Verifies QLoRA works

# Frontend tests
cd frontend && npm run test            # Vitest

# Node API tests
cd frontend/apps/api && npm run test   # Requires prisma:migrate first
```

## Environment Variables

**Frontend** (`frontend/.env`):
- `VITE_API_BASE_URL` - Backend URL (if missing, uses mocks)
- `VITE_USE_MOCKS` - Force mock mode (`true`/`false`)

**Node API** (`frontend/apps/api/.env`):
- `OPENROUTER_API_KEY` - Required for LLM calls
- `OPENROUTER_MODEL` - Default `nvidia/nemotron-nano-9b-v2:free`
- `DATABASE_URL` - Default `file:./dev.db`

## Requirements

- Python 3.12+, NVIDIA GPU with CUDA 12.x
- ~6GB VRAM for inference, ~10GB for training
- Base model at `models/base/llama3.1-nemotron-nano-8b-v1/`
- Node 18+ for frontend

## CrewAI Integration

The project includes a CrewAI-based debate system (`src/crew/`) that runs alongside the original multi-agent system (`src/agents/`).

**Status:** ✅ **Fully functional in standalone mode!**

### Quick Start

```bash
# Single command - no server needed!
python scripts/run_debate_crew.py "Your debate topic" --rounds 2
```

### Features

- **Dual Model System:** Loads two independent model instances (Pro and Con debaters)
- **Dynamic Adapters:** Automatically loads domain-specific adapters (education, technology, etc.)
- **Fast:** Complete debates in ~50 seconds
- **Simple:** No server configuration required

### Dependency Resolution

CrewAI 1.8.0 was installed with `--no-deps` to avoid conflicts with vLLM 0.13.0:

```bash
# Already done in requirements.txt
pip install --no-deps crewai==1.8.0 crewai-tools==1.8.0
```

This works because your existing package versions (openai 2.14.0, pydantic 2.12.5, tokenizers 0.22.1) are compatible with both.

### Test Results

See [test_outputs/STANDALONE_TEST_SUMMARY.md](test_outputs/STANDALONE_TEST_SUMMARY.md) for complete test report.

**Tested successfully:**
- ✅ Model loading (2 instances, ~11.5 GB VRAM)
- ✅ Domain adapter loading (education adapter tested)
- ✅ Debate generation (quality arguments)
- ✅ Fact-checking and judging
- ✅ Artifact saving (JSON + transcript)

**Performance:** 52 seconds for complete debate with 1 round
