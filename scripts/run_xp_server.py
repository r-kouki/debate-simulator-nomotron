#!/usr/bin/env python3
"""
FastAPI server for the Windows XP-themed Debate Simulator frontend.
Provides API endpoints for debate management, real-time progress streaming,
and settings management.
"""

import asyncio
import json
import os
import sys
import uuid
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

# Import CrewAI components if available
try:
    from src.crew.debate_crew import DebateCrew
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    print("Warning: CrewAI not available, using simulation mode")


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


async def run_simulated_debate(debate_id: str, request: DebateRequest):
    """Simulate a debate (used when CrewAI is not available)."""
    debate = debates.get(debate_id)
    if not debate:
        return
    
    queue = debate_progress_queues.get(debate_id)
    
    # Update status to running
    debate.status = "running"
    
    steps = [
        ("routing", "Routing to Domain"),
        ("research", "Research Phase"),
        ("pro-argument", "Pro Argument"),
        ("con-argument", "Con Argument"),
        ("fact-check", "Fact Checking"),
        ("judge", "Judge Evaluation"),
    ]
    
    try:
        for round_num in range(1, request.rounds + 1):
            for step_idx, (step_id, step_name) in enumerate(steps):
                if debate.status == "stopped":
                    return
                
                debate.current_round = round_num
                debate.current_step = step_name
                debate.progress = ((round_num - 1) * len(steps) + step_idx + 1) / (request.rounds * len(steps)) * 100
                
                # Notify progress
                if queue:
                    await queue.put({
                        "debate_id": debate_id,
                        "status": debate.status,
                        "step": step_name,
                        "round": round_num,
                        "progress": debate.progress,
                        "message": f"Round {round_num}: {step_name}",
                    })
                
                # Simulate argument generation
                if step_id == "pro-argument":
                    await asyncio.sleep(1.5)
                    arg = DebateArgument(
                        side="pro",
                        round=round_num,
                        content=f"[Simulated Pro Argument - Round {round_num}]\n\nThis is a simulated argument in favor of the topic: \"{request.topic}\"\n\nKey points:\n1. Evidence supporting this position\n2. Historical precedents\n3. Logical reasoning",
                        timestamp=datetime.now().isoformat()
                    )
                    debate.pro_arguments.append(arg)
                    debate.current_argument = arg.content
                    
                    if queue:
                        await queue.put({
                            "debate_id": debate_id,
                            "status": debate.status,
                            "step": step_name,
                            "round": round_num,
                            "progress": debate.progress,
                            "message": f"Pro argument generated",
                            "argument": {"side": "pro", "content": arg.content}
                        })
                
                elif step_id == "con-argument":
                    await asyncio.sleep(1.5)
                    arg = DebateArgument(
                        side="con",
                        round=round_num,
                        content=f"[Simulated Con Argument - Round {round_num}]\n\nThis is a simulated argument against the topic: \"{request.topic}\"\n\nCounter-points:\n1. Alternative evidence\n2. Potential drawbacks\n3. Opposing perspective",
                        timestamp=datetime.now().isoformat()
                    )
                    debate.con_arguments.append(arg)
                    debate.current_argument = arg.content
                    
                    if queue:
                        await queue.put({
                            "debate_id": debate_id,
                            "status": debate.status,
                            "step": step_name,
                            "round": round_num,
                            "progress": debate.progress,
                            "message": f"Con argument generated",
                            "argument": {"side": "con", "content": arg.content}
                        })
                
                else:
                    await asyncio.sleep(0.8)
        
        # Complete the debate
        import random
        winner = random.choice(["pro", "con"])
        debate.status = "completed"
        debate.end_time = datetime.now().isoformat()
        debate.progress = 100
        debate.current_step = "Completed"
        debate.judge_score = JudgeScore(
            winner=winner,
            pro_score=random.randint(70, 95),
            con_score=random.randint(70, 95),
            reasoning="Based on the quality and coherence of arguments presented, logical consistency, evidence cited, and overall persuasiveness...",
            fact_check_passed=True
        )
        
        # Notify completion
        if queue:
            await queue.put({
                "debate_id": debate_id,
                "status": "completed",
                "step": "Completed",
                "round": request.rounds,
                "progress": 100,
                "message": "Debate completed!",
            })
        
        # Save result
        save_debate_result(debate)
        
    except Exception as e:
        debate.status = "error"
        debate.error = str(e)
        if queue:
            await queue.put({
                "debate_id": debate_id,
                "status": "error",
                "message": str(e),
            })


async def run_crewai_debate(debate_id: str, request: DebateRequest):
    """Run an actual debate using CrewAI."""
    debate = debates.get(debate_id)
    if not debate:
        return
    
    queue = debate_progress_queues.get(debate_id)
    
    try:
        # Update status to running
        debate.status = "running"
        
        # Initialize CrewAI debate crew
        crew = DebateCrew(
            topic=request.topic,
            rounds=request.rounds,
            use_internet=request.use_internet,
        )
        
        # Run the debate with progress callbacks
        def on_progress(step: str, round_num: int, message: str, argument: dict = None):
            debate.current_step = step
            debate.current_round = round_num
            
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
            
            if queue:
                asyncio.create_task(queue.put({
                    "debate_id": debate_id,
                    "status": debate.status,
                    "step": step,
                    "round": round_num,
                    "progress": debate.progress,
                    "message": message,
                    "argument": argument,
                }))
        
        result = await crew.run(on_progress=on_progress)
        
        # Update with results
        debate.status = "completed"
        debate.end_time = datetime.now().isoformat()
        debate.progress = 100
        debate.current_step = "Completed"
        
        if result.get("judge"):
            debate.judge_score = JudgeScore(
                winner=result["judge"].get("winner", "tie"),
                pro_score=result["judge"].get("pro_score", 75),
                con_score=result["judge"].get("con_score", 75),
                reasoning=result["judge"].get("reasoning", ""),
                fact_check_passed=result["judge"].get("fact_check_passed", True)
            )
        
        save_debate_result(debate)
        
    except Exception as e:
        debate.status = "error"
        debate.error = str(e)
        if queue:
            await queue.put({
                "debate_id": debate_id,
                "status": "error",
                "message": str(e),
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
        "status": "healthy",
        "crewai_available": CREWAI_AVAILABLE,
        "debates_count": len(debates),
    }


@app.post("/api/debates", response_model=DebateResponse)
async def create_debate(request: DebateRequest, background_tasks: BackgroundTasks):
    """Create and start a new debate."""
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
    
    # Start debate in background
    if CREWAI_AVAILABLE:
        background_tasks.add_task(run_crewai_debate, debate_id, request)
    else:
        background_tasks.add_task(run_simulated_debate, debate_id, request)
    
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
    print("=" * 60)
    
    uvicorn.run(
        "run_xp_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        reload_dirs=[str(PROJECT_ROOT / "scripts")],
    )
