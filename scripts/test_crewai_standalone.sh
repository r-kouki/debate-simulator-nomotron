#!/bin/bash
# Test CrewAI debate system in standalone mode (no vLLM server)

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="test_outputs/crewai_standalone_test_${TIMESTAMP}.log"

# Create output directory
mkdir -p test_outputs

# Redirect all output to file and terminal
exec > >(tee "$OUTPUT_FILE") 2>&1

echo "=================================================================="
echo "  CrewAI Standalone Test (No vLLM Server)"
echo "  Date: $(date)"
echo "=================================================================="
echo ""

echo "COMMANDS TO REPRODUCE THIS TEST:"
echo "--------------------------------"
echo ""
echo "# Single command - no server needed!"
echo "cd /home/remote-core/project/debate-simulator-nomotron"
echo "source .venv/bin/activate"
echo "python scripts/run_debate_crew.py \"Should free college education be available?\" --rounds 1"
echo ""
echo "=================================================================="
echo ""

# Check if vLLM server is running
echo -e "${YELLOW}→ Checking if vLLM server is running...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}✗ WARNING: vLLM server is running! This may cause GPU conflicts.${NC}"
    echo "  Please stop it with: pkill -f 'vllm.entrypoints.openai.api_server'"
    echo ""
else
    echo -e "${GREEN}✓ No vLLM server detected (good for standalone test)${NC}"
    echo ""
fi

# Check GPU memory
echo -e "${YELLOW}→ GPU Status:${NC}"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits | \
    awk -F', ' '{printf "  GPU: %s\n  Total VRAM: %.1f GB\n  Used: %.1f GB\n  Free: %.1f GB\n", $1, $2/1024, $3/1024, $4/1024}'
else
    echo "  nvidia-smi not available"
fi
echo ""

# Remove OpenAI env vars to force standalone mode
echo -e "${YELLOW}→ Configuring standalone mode...${NC}"
unset OPENAI_API_BASE
unset OPENAI_API_KEY
unset OPENAI_MODEL_NAME
echo "✓ OpenAI env vars unset (will use direct model loading)"
echo ""

# Activate venv
echo -e "${YELLOW}→ Activating virtual environment...${NC}"
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Check packages
echo -e "${YELLOW}→ Package Versions:${NC}"
pip list | grep -E "(crewai|openai|pydantic|tokenizers|transformers|vllm|peft)" | sed 's/^/  /'
echo ""

echo "=================================================================="
echo "  Running CrewAI Standalone Debate Test"
echo "=================================================================="
echo ""
echo "Topic: Should free college education be available?"
echo "Rounds: 1"
echo "Mode: STANDALONE (Direct model loading)"
echo ""

# Run the debate
python scripts/run_debate_crew.py \
    "Should free college education be available?" \
    --rounds 1 \
    --output-dir test_outputs/debates

EXIT_CODE=$?

echo ""
echo "=================================================================="
echo "  Test Complete"
echo "=================================================================="
echo ""
echo "Exit code: $EXIT_CODE"

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Test completed successfully!${NC}"
else
    echo -e "${RED}✗ Test failed with exit code $EXIT_CODE${NC}"
fi

echo ""
echo "Output saved to: $OUTPUT_FILE"
echo ""
echo "Done!"
