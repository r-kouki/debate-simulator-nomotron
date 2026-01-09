#!/bin/bash
# Quick start script for the XP Debate Simulator

echo "============================================================"
echo "Starting Debate Simulator XP"
echo "============================================================"
echo ""
echo "This will start:"
echo "  1. Backend API (http://localhost:5040) with preloaded models"
echo "  2. Frontend XP UI (http://localhost:5173)"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Store PIDs for cleanup
PIDS=()

# Cleanup function
cleanup() {
    echo ""
    echo "Shutting down..."
    for pid in "${PIDS[@]}"; do
        kill $pid 2>/dev/null
    done
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
echo "[1/2] Starting backend API..."
cd /home/remote-core/project/debate-simulator-nomotron
source .venv/bin/activate
python scripts/run_xp_server.py &
BACKEND_PID=$!
PIDS+=($BACKEND_PID)

# Wait for backend to start
echo "Waiting for backend to initialize (30 seconds for model loading)..."
sleep 30

# Check if backend is running
if curl -s http://localhost:5040/api/health > /dev/null; then
    echo "✓ Backend is ready!"
else
    echo "✗ Backend failed to start"
    cleanup
fi

# Start frontend
echo ""
echo "[2/2] Starting frontend..."
cd frontend-xp
npm run dev &
FRONTEND_PID=$!
PIDS+=($FRONTEND_PID)

echo ""
echo "============================================================"
echo "✓ All services started!"
echo "============================================================"
echo ""
echo "Backend API: http://localhost:5040"
echo "Frontend UI: http://localhost:5173"
echo ""
echo "Open http://localhost:5173 in your browser"
echo "Click 'New Debate' to start a debate with real-time streaming!"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for user interrupt
wait
