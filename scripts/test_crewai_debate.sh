#!/bin/bash
# Test CrewAI debate system with vLLM server
# Saves complete output including commands for reproduction

set -e

PROJECT_ROOT="/home/remote-core/project/debate-simulator-nomotron"
OUTPUT_FILE="$PROJECT_ROOT/test_outputs/crewai_debate_test_$(date +%Y%m%d_%H%M%S).log"
VLLM_LOG="$PROJECT_ROOT/test_outputs/vllm_server_$(date +%Y%m%d_%H%M%S).log"

cd "$PROJECT_ROOT"
source .venv/bin/activate

echo "==================================================================" | tee "$OUTPUT_FILE"
echo "  CrewAI Debate System Test" | tee -a "$OUTPUT_FILE"
echo "  Date: $(date)" | tee -a "$OUTPUT_FILE"
echo "==================================================================" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "COMMANDS TO REPRODUCE THIS TEST:" | tee -a "$OUTPUT_FILE"
echo "--------------------------------" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
echo "# Terminal 1: Start vLLM server" | tee -a "$OUTPUT_FILE"
echo "cd $PROJECT_ROOT" | tee -a "$OUTPUT_FILE"
echo "source .venv/bin/activate" | tee -a "$OUTPUT_FILE"
echo "bash scripts/start_vllm_server.sh" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
echo "# Terminal 2: Run debate" | tee -a "$OUTPUT_FILE"
echo "cd $PROJECT_ROOT" | tee -a "$OUTPUT_FILE"
echo "source .venv/bin/activate" | tee -a "$OUTPUT_FILE"
echo "python scripts/run_debate_crew.py \"Should AI be regulated?\" --rounds 1" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
echo "==================================================================" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Check if vLLM server is already running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ vLLM server already running at http://localhost:8000" | tee -a "$OUTPUT_FILE"
    SERVER_STARTED=false
else
    echo "→ Starting vLLM server..." | tee -a "$OUTPUT_FILE"
    echo "  (This may take 1-2 minutes to load the model)" | tee -a "$OUTPUT_FILE"
    echo "" | tee -a "$OUTPUT_FILE"

    # Start vLLM server in background
    python -m vllm.entrypoints.openai.api_server \
        --model "models/base/llama3.1-nemotron-nano-8b-v1" \
        --port 8000 \
        --host 0.0.0.0 \
        --dtype auto \
        --max-model-len 4096 \
        --gpu-memory-utilization 0.9 \
        > "$VLLM_LOG" 2>&1 &

    VLLM_PID=$!
    echo "  vLLM server PID: $VLLM_PID" | tee -a "$OUTPUT_FILE"
    echo "  vLLM logs: $VLLM_LOG" | tee -a "$OUTPUT_FILE"
    SERVER_STARTED=true

    # Wait for server to be ready (max 3 minutes)
    echo -n "  Waiting for server to start" | tee -a "$OUTPUT_FILE"
    for i in {1..36}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "" | tee -a "$OUTPUT_FILE"
            echo "✓ vLLM server is ready!" | tee -a "$OUTPUT_FILE"
            break
        fi
        echo -n "." | tee -a "$OUTPUT_FILE"
        sleep 5

        # Check if process died
        if ! kill -0 $VLLM_PID 2>/dev/null; then
            echo "" | tee -a "$OUTPUT_FILE"
            echo "✗ vLLM server process died!" | tee -a "$OUTPUT_FILE"
            echo "Check logs at: $VLLM_LOG" | tee -a "$OUTPUT_FILE"
            exit 1
        fi
    done
    echo "" | tee -a "$OUTPUT_FILE"
fi

# Test server is responding
echo "→ Testing vLLM server endpoints..." | tee -a "$OUTPUT_FILE"
if curl -s http://localhost:8000/v1/models | grep -q "llama"; then
    echo "✓ Server is responding correctly" | tee -a "$OUTPUT_FILE"
else
    echo "✗ Server not responding as expected" | tee -a "$OUTPUT_FILE"
    exit 1
fi
echo "" | tee -a "$OUTPUT_FILE"

# Show environment configuration
echo "→ Environment Configuration:" | tee -a "$OUTPUT_FILE"
if [ -f .env ]; then
    echo "  .env file exists:" | tee -a "$OUTPUT_FILE"
    grep -E "^OPENAI" .env | sed 's/^/    /' | tee -a "$OUTPUT_FILE"
else
    echo "  ✗ .env file not found!" | tee -a "$OUTPUT_FILE"
fi
echo "" | tee -a "$OUTPUT_FILE"

# Show installed versions
echo "→ Package Versions:" | tee -a "$OUTPUT_FILE"
pip list | grep -E "(crewai|vllm|openai|pydantic|transformers|tokenizers)" | sed 's/^/  /' | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "==================================================================" | tee -a "$OUTPUT_FILE"
echo "  Running CrewAI Debate Test" | tee -a "$OUTPUT_FILE"
echo "==================================================================" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Run the debate
echo "Topic: Should AI be regulated?" | tee -a "$OUTPUT_FILE"
echo "Rounds: 1" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

python scripts/run_debate_crew.py "Should AI be regulated?" --rounds 1 2>&1 | tee -a "$OUTPUT_FILE"

DEBATE_EXIT_CODE=$?

echo "" | tee -a "$OUTPUT_FILE"
echo "==================================================================" | tee -a "$OUTPUT_FILE"
echo "  Test Complete" | tee -a "$OUTPUT_FILE"
echo "==================================================================" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
echo "Exit code: $DEBATE_EXIT_CODE" | tee -a "$OUTPUT_FILE"
echo "Output saved to: $OUTPUT_FILE" | tee -a "$OUTPUT_FILE"

# Cleanup: stop vLLM server if we started it
if [ "$SERVER_STARTED" = true ]; then
    echo "" | tee -a "$OUTPUT_FILE"
    echo "→ Stopping vLLM server (PID: $VLLM_PID)..." | tee -a "$OUTPUT_FILE"
    kill $VLLM_PID 2>/dev/null || true
    sleep 2
    kill -9 $VLLM_PID 2>/dev/null || true
    echo "✓ Server stopped" | tee -a "$OUTPUT_FILE"
fi

echo "" | tee -a "$OUTPUT_FILE"
echo "Done! Check the output at:" | tee -a "$OUTPUT_FILE"
echo "$OUTPUT_FILE" | tee -a "$OUTPUT_FILE"

exit $DEBATE_EXIT_CODE
