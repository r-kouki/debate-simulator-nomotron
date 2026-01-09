#!/usr/bin/env python3
"""
FastAPI server for the Windows XP-themed Debate Simulator frontend.
Provides API endpoints for debate management with CrewAI integration.
NO SIMULATION MODE - Uses real CrewAI only.
"""

import asyncio
import json
import os
import sys
import uuid
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List, AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import CrewAI components
try:
    from src.crew.debate_crew import DebateCrew
    CREWAI_AVAILABLE = True
    CREWAI_ERROR = None
except ImportError as e:
    CREWAI_AVAILABLE = False
    CREWAI_ERROR = str(e)
    print(f"ERROR: CrewAI not available: {e}")
except Exception as e:
    CREWAI_AVAILABLE = False
    CREWAI_ERROR = str(e)
    print(f"ERROR: Failed to import CrewAI: {e}")


# ============================================================================
# Models
# ============================================================================

class DebateRequest(BaseModel):
    topic: str
    rounds: int = Field(default=2, ge=1, le=5)
    use_internet: bool = False
    recommend_guests: bool = False
    domain: Optional[str] = "auto"
    adapter: Optional[str] = "auto"


class DebateResponse(BaseModel):
    id: str
    status: str
    message: str


class DebateArgument(BaseModel):
    side: str  # 'pro' or 'con'
    round: int
    content: str
    timestamp: str


class JudgeScore(BaseModel):
    winner: str  # 'pro', 'con', or 'tie'
    pro_score: int
    con_score: int
    reasoning: str
    fact_check_passed: bool


class DebateSession(BaseModel):
    id: str
    topic: str
    domain: str
    rounds: int
    status: str  # 'pending', 'running', 'completed', 'error', 'stopped'
    start_time: str
    end_time: Optional[str] = None
    current_round: int = 0
    current_step: str = "Initializing"
    progress: float = 0
    pro_arguments: List[DebateArgument] = []
    con_arguments: List[DebateArgument] = []
    current_argument: Optional[str] = None
    judge_score: Optional[JudgeScore] = None
    error: Optional[str] = None


class Settings(BaseModel):
    wallpaper: str = "bliss"
    theme: str = "bliss"
    default_rounds: int = 2
    use_internet: bool = False
    recommend_guests: bool = False
    auto_save_results: bool = True
    window_animation: bool = True
    sound_effects: bool = True
    api_endpoint: str = "http://localhost:8001/api"
    debug_mode: bool = False


class AdapterInfo(BaseModel):
    id: str
    name: str
    domain: str
    description: str
    path: str


# ============================================================================
# In-memory storage (replace with database in production)
# ============================================================================

debates: dict[str, DebateSession] = {}
debate_progress_queues: dict[str, asyncio.Queue] = {}
settings: Settings = Settings()

# Runs directory for persisting results
RUNS_DIR = PROJECT_ROOT / "runs" / "debates"
RUNS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Helper functions
# ============================================================================

def get_adapters() -> List[AdapterInfo]:
    """Get list of available domain adapters."""
    adapters_dir = PROJECT_ROOT / "models" / "adapters"
    adapters = []
    
    if adapters_dir.exists():
        for domain_dir in adapters_dir.iterdir():
            if domain_dir.is_dir():
                adapters.append(AdapterInfo(
                    id=domain_dir.name,
                    name=domain_dir.name.title(),
                    domain=domain_dir.name,
                    description=f"Domain adapter for {domain_dir.name} topics",
                    path=str(domain_dir)
                ))
    
    # Add fallback if no adapters found
    if not adapters:
        for domain in ["general", "education", "medicine", "ecology", "debate"]:
            adapters.append(AdapterInfo(
                id=domain,
                name=domain.title(),
                domain=domain,
                description=f"Domain adapter for {domain} topics",
                path=""
            ))
    
    return adapters


def save_debate_result(debate: DebateSession):
    """Save debate result to filesystem."""
    debate_dir = RUNS_DIR / debate.id
    debate_dir.mkdir(exist_ok=True)
    
    with open(debate_dir / "result.json", "w") as f:
        json.dump(debate.model_dump(), f, indent=2)


def load_debate_history() -> List[DebateSession]:
    """Load debate history from filesystem."""
    history = []
    
    for debate_dir in RUNS_DIR.iterdir():
        if debate_dir.is_dir():
            result_file = debate_dir / "result.json"
            if result_file.exists():
                with open(result_file) as f:
                    data = json.load(f)
                    history.append(DebateSession(**data))
    
    # Sort by start time descending
    history.sort(key=lambda d: d.start_time, reverse=True)
    return history


async def run_crewai_debate(debate_id: str, request: DebateRequest):
    """Run an actual debate using CrewAI with verbose progress logging."""
    debate = debates.get(debate_id)
    if not debate:
        print(f"[ERROR] Debate {debate_id} not found in store")
        return
    
    queue = debate_progress_queues.get(debate_id)
    
    print(f"\n{'='*60}")
    print(f"STARTING CREWAI DEBATE: {debate_id}")
    print(f"Topic: {request.topic}")
    print(f"Rounds: {request.rounds}")
    print(f"Use Internet: {request.use_internet}")
    print(f"{'='*60}\n")
    
    async def send_progress(step: str, round_num: int, progress: float, message: str, argument: dict = None):
        """Helper to send progress updates."""
        debate.current_step = step
        debate.current_round = round_num
        debate.progress = progress
        
        print(f"  [{step}] Round {round_num} - {progress:.1f}% - {message}")
        
        if argument:
            arg = DebateArgument(
                side=argument["side"],
                round=round_num,
                content=argument["content"],
                timestamp=datetime.now().isoformat()
            )
            if argument["side"] == "pro":
                debate.pro_arguments.append(arg)
            else:
                debate.con_arguments.append(arg)
            debate.current_argument = arg.content
            print(f"    → {argument['side'].upper()} argument: {argument['content'][:100]}...")
        
        if queue:
            await queue.put({
                "debate_id": debate_id,
                "status": debate.status,
                "step": step,
                "round": round_num,
                "progress": progress,
                "message": message,
                "argument": argument,
            })
    
    try:
        # Update status to running
        debate.status = "running"
        await send_progress("Initializing", 0, 0, "Loading CrewAI...")
        
        # Initialize CrewAI debate crew
        print("[1/6] Initializing DebateCrew...")
        crew = DebateCrew(
            use_internet=request.use_internet,
            output_dir=PROJECT_ROOT / "runs" / "debates",
            verbose=True,
        )
        
        await send_progress("Routing to Domain", 0, 5, "Classifying domain...")
        
        # Run the debate synchronously in a thread pool
        import concurrent.futures
        loop = asyncio.get_event_loop()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                crew.run_debate,
                request.topic,
                request.rounds,
                request.recommend_guests,
            )
        
        # Process results
        print(f"\n[RESULT] Debate completed!")
        print(f"  Winner: {result.judge_score.winner}")
        print(f"  Pro Score: {result.judge_score.pro_score}")
        print(f"  Con Score: {result.judge_score.con_score}")
        
        # Update debate with results
        for i, pro_arg in enumerate(result.pro_arguments):
            arg = DebateArgument(
                side="pro",
                round=i + 1,
                content=pro_arg,
                timestamp=datetime.now().isoformat()
            )
            if arg not in debate.pro_arguments:
                debate.pro_arguments.append(arg)
                if queue:
                    await queue.put({
                        "debate_id": debate_id,
                        "status": "running",
                        "step": "Pro Argument",
                        "round": i + 1,
                        "progress": 20 + (i * 30 / max(1, len(result.pro_arguments))),
                        "message": f"Pro argument round {i+1}",
                        "argument": {"side": "pro", "content": pro_arg},
                    })
        
        for i, con_arg in enumerate(result.con_arguments):
            arg = DebateArgument(
                side="con",
                round=i + 1,
                content=con_arg,
                timestamp=datetime.now().isoformat()
            )
            if arg not in debate.con_arguments:
                debate.con_arguments.append(arg)
                if queue:
                    await queue.put({
                        "debate_id": debate_id,
                        "status": "running",
                        "step": "Con Argument",
                        "round": i + 1,
                        "progress": 50 + (i * 30 / max(1, len(result.con_arguments))),
                        "message": f"Con argument round {i+1}",
                        "argument": {"side": "con", "content": con_arg},
                    })
        
        # Update final status
        debate.status = "completed"
        debate.end_time = datetime.now().isoformat()
        debate.progress = 100
        debate.current_step = "Completed"
        debate.judge_score = JudgeScore(
            winner=result.judge_score.winner,
            pro_score=result.judge_score.pro_score,
            con_score=result.judge_score.con_score,
            reasoning=result.judge_score.reasoning,
            fact_check_passed=True
        )
        
        # Send completion
        if queue:
            await queue.put({
                "debate_id": debate_id,
                "status": "completed",
                "step": "Completed",
                "round": request.rounds,
                "progress": 100,
                "message": f"Debate completed! Winner: {result.judge_score.winner.upper()}",
            })
        
        save_debate_result(debate)
        print(f"\n{'='*60}")
        print(f"DEBATE COMPLETE: {debate_id}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        import traceback
        print(f"\n[ERROR] Debate failed: {e}")
        traceback.print_exc()
        
        debate.status = "error"
        debate.error = str(e)
        if queue:
            await queue.put({
                "debate_id": debate_id,
                "status": "error",
                "step": "Error",
                "round": 0,
                "progress": 0,
                "message": f"Error: {str(e)}",
            })


# ============================================================================
# FastAPI App
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Load saved debates on startup
    global debates
    for saved_debate in load_debate_history():
        debates[saved_debate.id] = saved_debate
    print(f"Loaded {len(debates)} debates from history")
    yield
    # Cleanup on shutdown
    print("Shutting down...")


app = FastAPI(
    title="Debate Simulator XP API",
    description="Backend API for the Windows XP-themed Debate Simulator",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy" if CREWAI_AVAILABLE else "degraded",
        "crewai_available": CREWAI_AVAILABLE,
        "crewai_error": CREWAI_ERROR,
        "debates_count": len(debates),
    }


@app.get("/api/crewai/status")
async def crewai_status():
    """Get detailed CrewAI status information."""
    status = {
        "available": CREWAI_AVAILABLE,
        "error": CREWAI_ERROR,
        "packages": {},
        "gpu": None,
        "venv_active": os.environ.get("VIRTUAL_ENV") is not None,
        "python_version": sys.version,
    }
    
    # Check package versions
    try:
        import pkg_resources
        packages_to_check = [
            "crewai", "openai", "pydantic", "transformers", 
            "torch", "peft", "tokenizers"
        ]
        for pkg in packages_to_check:
            try:
                version = pkg_resources.get_distribution(pkg).version
                status["packages"][pkg] = {"installed": True, "version": version}
            except pkg_resources.DistributionNotFound:
                status["packages"][pkg] = {"installed": False, "version": None}
    except Exception as e:
        status["packages_error"] = str(e)
    
    # Check GPU status
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free", 
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            if len(parts) >= 4:
                status["gpu"] = {
                    "name": parts[0],
                    "memory_total_mb": int(float(parts[1])),
                    "memory_used_mb": int(float(parts[2])),
                    "memory_free_mb": int(float(parts[3])),
                }
    except Exception:
        status["gpu"] = None
    
    # Check if vLLM server is running (could cause conflicts)
    try:
        import requests
        resp = requests.get("http://localhost:8000/health", timeout=1)
        status["vllm_server_running"] = resp.status_code == 200
    except Exception:
        status["vllm_server_running"] = False
    
    return status


@app.post("/api/debates", response_model=DebateResponse)
async def create_debate(request: DebateRequest, background_tasks: BackgroundTasks):
    """Create and start a new debate using CrewAI."""
    if not CREWAI_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail=f"CrewAI is not available: {CREWAI_ERROR}. Please check the server logs."
        )
    
    debate_id = f"debate-{uuid.uuid4().hex[:12]}"
    
    # Determine domain
    domain = request.domain if request.domain != "auto" else "general"
    
    debate = DebateSession(
        id=debate_id,
        topic=request.topic,
        domain=domain,
        rounds=request.rounds,
        status="pending",
        start_time=datetime.now().isoformat(),
    )
    
    debates[debate_id] = debate
    debate_progress_queues[debate_id] = asyncio.Queue()
    
    # Start CrewAI debate in background
    background_tasks.add_task(run_crewai_debate, debate_id, request)
    
    return DebateResponse(
        id=debate_id,
        status="created",
        message="Debate created and starting..."
    )


@app.get("/api/debates/{debate_id}", response_model=DebateSession)
async def get_debate(debate_id: str):
    """Get debate details."""
    if debate_id not in debates:
        raise HTTPException(status_code=404, detail="Debate not found")
    return debates[debate_id]


@app.get("/api/debates", response_model=List[DebateSession])
async def list_debates(limit: int = 50, offset: int = 0):
    """List all debates with pagination."""
    all_debates = list(debates.values())
    all_debates.sort(key=lambda d: d.start_time, reverse=True)
    return all_debates[offset:offset + limit]


@app.delete("/api/debates/{debate_id}")
async def delete_debate(debate_id: str):
    """Delete a debate."""
    if debate_id not in debates:
        raise HTTPException(status_code=404, detail="Debate not found")
    
    # Remove from memory
    del debates[debate_id]
    if debate_id in debate_progress_queues:
        del debate_progress_queues[debate_id]
    
    # Remove from filesystem
    debate_dir = RUNS_DIR / debate_id
    if debate_dir.exists():
        import shutil
        shutil.rmtree(debate_dir)
    
    return {"status": "deleted"}


@app.post("/api/debates/{debate_id}/stop")
async def stop_debate(debate_id: str):
    """Stop a running debate."""
    if debate_id not in debates:
        raise HTTPException(status_code=404, detail="Debate not found")
    
    debate = debates[debate_id]
    if debate.status == "running":
        debate.status = "stopped"
        debate.end_time = datetime.now().isoformat()
        save_debate_result(debate)
    
    return {"status": "stopped"}


@app.get("/api/debates/{debate_id}/stream")
async def stream_debate_progress(debate_id: str):
    """Server-Sent Events stream for real-time debate progress."""
    if debate_id not in debates:
        raise HTTPException(status_code=404, detail="Debate not found")
    
    async def event_stream() -> AsyncGenerator[str, None]:
        queue = debate_progress_queues.get(debate_id)
        if not queue:
            queue = asyncio.Queue()
            debate_progress_queues[debate_id] = queue
        
        try:
            while True:
                try:
                    # Wait for progress update with timeout
                    progress = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(progress)}\n\n"
                    
                    if progress.get("status") in ["completed", "error", "stopped"]:
                        break
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f": keepalive\n\n"
        except asyncio.CancelledError:
            pass
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/api/settings", response_model=Settings)
async def get_settings():
    """Get current settings."""
    return settings


@app.put("/api/settings", response_model=Settings)
async def update_settings(new_settings: Settings):
    """Update settings."""
    global settings
    settings = new_settings
    return settings


@app.get("/api/adapters", response_model=List[AdapterInfo])
async def list_adapters():
    """List available domain adapters."""
    return get_adapters()


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("Debate Simulator XP - API Server")
    print("=" * 60)
    print(f"CrewAI Available: {CREWAI_AVAILABLE}")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Runs Directory: {RUNS_DIR}")
    print(f"Server Port: 5040")
    print("=" * 60)
    
    uvicorn.run(
        "run_xp_server:app",
        host="0.0.0.0",
        port=5040,
        reload=True,
        reload_dirs=[str(PROJECT_ROOT / "scripts")],
    )
