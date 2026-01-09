#!/bin/bash
# Start vLLM as OpenAI-compatible API server for CrewAI
# This allows CrewAI agents to use the local model via OpenAI API format

set -e

MODEL_PATH="models/base/llama3.1-nemotron-nano-8b-v1"
PORT=8000

echo "Starting vLLM OpenAI-compatible server..."
echo "Model: $MODEL_PATH"
echo "Port: $PORT"
echo ""

# Activate virtual environment
source .venv/bin/activate

# Start vLLM server
python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --port $PORT \
    --host 0.0.0.0 \
    --dtype auto \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9

# To test: curl http://localhost:8000/v1/models
