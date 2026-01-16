# CrewAI Integration Issue

## Problem Discovered

The current CrewAI implementation (`src/crew/`) has a **design conflict**:

### Two Different LLM Access Methods

1. **CrewAI Agents** (router, research, factcheck, judge, persona):
   - Use CrewAI's `Agent` class with `llm` parameter
   - Expect OpenAI API format (can be vLLM server)
   - Configured via `.env`: `OPENAI_API_BASE`, `OPENAI_API_KEY`

2. **Debate Generation Tools** ([src/crew/utils/dual_model_manager.py](src/crew/utils/dual_model_manager.py)):
   - Use `DualModelManager` class
   - **Load models directly** using HuggingFace Transformers
   - Load TWO model instances (Pro and Con) for parallel generation
   - Requires GPU VRAM for both model instances

### The Conflict

When you run the vLLM server (which uses GPU), then run the CrewAI debate:
```bash
# Terminal 1: vLLM server loads model → Uses GPU
bash scripts/start_vllm_server.sh

# Terminal 2: DualModelManager tries to load 2 more models → GPU out of memory!
python scripts/run_debate_crew.py "Topic" --rounds 1
```

**Error:**
```
ValueError: Some modules are dispatched on the CPU or the disk. Make sure you have enough GPU RAM to fit the quantized model.
```

## Why This Design?

The DualModelManager was designed to:
- Load two independent model instances (Pro and Con debaters)
- Enable parallel argument generation
- Allow independent domain adapter loading per stance
- Work **standalone** without external API servers

But CrewAI agents need an LLM, which by default expects OpenAI API.

## Solutions

### Option 1: Standalone Mode (Recommended)

**Don't use vLLM server** - let DualModelManager load models directly:

```bash
# Just run the debate (no vLLM server needed)
python scripts/run_debate_crew.py "Should AI be regulated?" --rounds 2
```

**Pros:**
- Simple - one command
- Dual model loading works as designed
- No API overhead

**Cons:**
- CrewAI agents fail if they try to use LLM (need configuration fix)
- Loads models in-process (slower startup)

### Option 2: API-Only Mode (Requires Rewrite)

Rewrite DualModelManager to use vLLM API instead of direct loading:

```python
# Instead of loading models:
model, tokenizer = load_base_model()

# Use OpenAI API client:
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")
response = client.completions.create(...)
```

**Pros:**
- Consistent API usage throughout
- vLLM server optimizations (paged attention, continuous batching)
- Single model in memory

**Cons:**
- Loses dual-model parallel generation
- Loses independent adapter per stance
- Requires significant code rewrite

### Option 3: Separate Virtual Environment

Create separate venv for CrewAI standalone:

```bash
python -m venv .venv_crewai
source .venv_crewai/bin/activate
pip install crewai==1.8.0 crewai-tools==1.8.0 transformers peft torch ...
python scripts/run_debate_crew.py "Topic"
```

**Pros:**
- No dependency conflicts
- Standalone mode works as designed

**Cons:**
- Two separate environments to maintain
- Duplicate packages

## Recommended Fix

**Configure CrewAI agents to not require LLM** (they can work without it for this use case):

The router, research, factcheck, and judge agents are currently set up but not actually using LLM calls - they just run Python functions. We can configure them to work without requiring OpenAI API.

Then the debate generation uses DualModelManager as designed, and everything runs standalone.

## Test Output

The test ran successfully until it hit the GPU memory issue:

```
✓ vLLM server started (models loaded)
✓ CrewAI agents loaded (trying to use API)
✓ Domain routing: technology
✓ Research gathered
✗ Debate generation failed: GPU out of memory (DualModelManager tried to load 2 more models)
```

**Output saved to:**
- [test_outputs/crewai_debate_test_20260109_103014.log](test_outputs/crewai_debate_test_20260109_103014.log)
- [test_outputs/vllm_server_20260109_103014.log](test_outputs/vllm_server_20260109_103014.log)

## Next Steps

Choose one of:
1. Fix agents to work without LLM requirement (standalone mode)
2. Rewrite DualModelManager to use API (significant work)
3. Accept that CrewAI system is standalone-only (simplest)

The **original debate system** ([scripts/run_debate.py](scripts/run_debate.py)) works fine standalone without these issues.
