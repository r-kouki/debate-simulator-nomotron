# CrewAI Setup Guide

## Problem: Dependency Conflicts

CrewAI 1.8.0 and vLLM 0.13.0 have incompatible dependencies:

| Package | vLLM 0.13.0 requires | CrewAI 1.8.0 requires |
|---------|---------------------|----------------------|
| openai | >=1.99.1 | ~=1.83.0 |
| pydantic | >=2.12.0 | ~=2.11.9 |
| tokenizers | >=0.21.1 | ~=0.20.3 |

## Solution: Install CrewAI with --no-deps

We install CrewAI without its dependencies and use the versions already installed for vLLM:

```bash
pip install --no-deps crewai==1.8.0 crewai-tools==1.8.0
```

This works because:
- openai 2.14.0 (your version) is **newer** than both requirements and supports all features
- pydantic 2.12.5 (your version) satisfies vLLM and is close enough to work with CrewAI
- tokenizers 0.22.1 (your version) satisfies vLLM and works with CrewAI

## How to Use CrewAI with Local vLLM

CrewAI needs an "LLM" - it expects OpenAI API format. We use vLLM's OpenAI-compatible server:

### Step 1: Start vLLM Server (Terminal 1)

```bash
source .venv/bin/activate
bash scripts/start_vllm_server.sh
```

This starts vLLM at http://localhost:8000/v1 with OpenAI-compatible endpoints.

### Step 2: Configure Environment

The [.env](.env) file is already configured:

```bash
OPENAI_API_BASE=http://localhost:8000/v1
OPENAI_API_KEY=dummy-key-for-local-vllm
OPENAI_MODEL_NAME=llama3.1-nemotron-nano-8b
```

### Step 3: Run CrewAI Debate (Terminal 2)

```bash
source .venv/bin/activate
python scripts/run_debate_crew.py "Should AI be regulated?" --rounds 2
```

## Testing the Setup

1. **Test vLLM server is running:**
   ```bash
   curl http://localhost:8000/v1/models
   ```

2. **Test CrewAI can load:**
   ```bash
   python -c "from src.crew.debate_crew import DebateCrew; print('✓ CrewAI loaded')"
   ```

3. **Run a quick debate:**
   ```bash
   python scripts/run_debate_crew.py "Test topic" --rounds 1 --quiet
   ```

## Troubleshooting

### Error: "OPENAI_API_KEY is required"
- Make sure [.env](.env) exists in project root
- Check that `python-dotenv` is installed: `pip list | grep dotenv`

### Error: "Connection refused"
- vLLM server not running - start it in Terminal 1
- Check server is listening: `curl http://localhost:8000/health`

### Import errors
- Reinstall dependencies: `pip install -r requirements.txt`
- Then reinstall CrewAI: `pip install --no-deps crewai==1.8.0 crewai-tools==1.8.0`

## Why Two Separate Systems?

You now have **two debate systems**:

1. **Original system** ([src/agents/](src/agents/)):
   - Direct HuggingFace Transformers usage
   - Loads models in-process
   - Run: `python scripts/run_debate.py`

2. **CrewAI system** ([src/crew/](src/crew/)):
   - CrewAI orchestration framework
   - Accesses models via vLLM API server
   - Run: `python scripts/run_debate_crew.py` (needs vLLM server)

Both systems work independently. Choose based on your needs.

## Alternative: Separate Virtual Environment

If you still encounter issues, you can create a separate venv just for CrewAI:

```bash
# Create new venv
python -m venv .venv_crewai
source .venv_crewai/bin/activate

# Install only what CrewAI needs
pip install crewai==1.8.0 crewai-tools==1.8.0

# Still need vLLM server from main venv
```

This isolates dependencies but you lose access to vLLM/transformers in the CrewAI environment.

## Sources

- [CrewAI PyPI](https://pypi.org/project/crewai/)
- [CrewAI with vLLM Community Thread](https://community.crewai.com/t/crewai-and-openai-compatible-vllm-hosted-model/6674)
- [vLLM OpenAI Server Docs](https://docs.vllm.ai/en/latest/)
- [CrewAI GitHub Issues on Dependencies](https://github.com/crewAIInc/crewAI/issues)
