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

# Import TeacherCrew for lesson generation
try:
    from src.crew.teacher_crew import TeacherCrew
    TEACHER_AVAILABLE = True
    TEACHER_ERROR = None
except ImportError as e:
    TEACHER_AVAILABLE = False
    TEACHER_ERROR = str(e)
    print(f"WARNING: TeacherCrew not available: {e}")
except Exception as e:
    TEACHER_AVAILABLE = False
    TEACHER_ERROR = str(e)
    print(f"WARNING: Failed to import TeacherCrew: {e}")


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
    mode: Optional[str] = "ai_vs_ai"  # 'ai_vs_ai' or 'human_vs_ai'
    human_side: Optional[str] = "pro"  # 'pro' or 'con' when mode='human_vs_ai'


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
    pro_score: float  # Changed from int to float
    con_score: float  # Changed from int to float
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


class HumanTurnRequest(BaseModel):
    """Request body for submitting a human argument."""
    argument: str


class LessonRequest(BaseModel):
    """Request body for creating a new lesson."""
    topic: str
    detail_level: str = "intermediate"  # beginner, intermediate, advanced
    use_internet: bool = True


class LessonResponse(BaseModel):
    """Response when a lesson is created."""
    id: str
    status: str
    message: str


class LessonSection(BaseModel):
    """Structured lesson content."""
    topic: str
    overview: str
    key_concepts: List[str] = []
    examples: List[str] = []
    quiz_questions: List[str] = []


class LessonSession(BaseModel):
    """A lesson session with status and content."""
    id: str
    topic: str
    domain: str
    detail_level: str
    status: str  # 'pending', 'running', 'completed', 'error'
    start_time: str
    end_time: Optional[str] = None
    progress: float = 0
    current_step: str = "Initializing"
    lesson: Optional[LessonSection] = None
    error: Optional[str] = None


# ============================================================================
# In-memory storage (replace with database in production)
# ============================================================================

debates: dict[str, DebateSession] = {}
debate_progress_queues: dict[str, asyncio.Queue] = {}
settings: Settings = Settings()

# Lessons storage
lessons: dict[str, LessonSession] = {}
lesson_progress_queues: dict[str, asyncio.Queue] = {}

# Pre-loaded CrewAI debate crew with models loaded in memory
preloaded_crew: Optional[DebateCrew] = None
preloaded_teacher_crew: Optional["TeacherCrew"] = None

# Runs directories for persisting results
RUNS_DIR = PROJECT_ROOT / "runs" / "debates"
RUNS_DIR.mkdir(parents=True, exist_ok=True)
LESSONS_DIR = PROJECT_ROOT / "runs" / "lessons"
LESSONS_DIR.mkdir(parents=True, exist_ok=True)


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
    """Load debate history from filesystem with backward compatibility."""
    history = []

    for debate_dir in RUNS_DIR.iterdir():
        if debate_dir.is_dir():
            result_file = debate_dir / "result.json"
            if result_file.exists():
                try:
                    with open(result_file) as f:
                        data = json.load(f)

                    # Handle old format (from original run_debate_crew.py)
                    if "id" not in data:
                        # Migrate old format to new format
                        debate_id = debate_dir.name

                        # Convert arguments from strings to DebateArgument objects
                        pro_arguments = []
                        for i, arg_text in enumerate(data.get("pro_arguments", [])):
                            if isinstance(arg_text, str):
                                pro_arguments.append(DebateArgument(
                                    side="pro",
                                    round=i + 1,
                                    content=arg_text,
                                    timestamp=datetime.now().isoformat()
                                ))
                            else:
                                # Already in new format
                                pro_arguments.append(DebateArgument(**arg_text))

                        con_arguments = []
                        for i, arg_text in enumerate(data.get("con_arguments", [])):
                            if isinstance(arg_text, str):
                                con_arguments.append(DebateArgument(
                                    side="con",
                                    round=i + 1,
                                    content=arg_text,
                                    timestamp=datetime.now().isoformat()
                                ))
                            else:
                                # Already in new format
                                con_arguments.append(DebateArgument(**arg_text))

                        # Convert judge score
                        judge_data = data.get("judge", {})
                        judge_score = None
                        if judge_data:
                            judge_score = JudgeScore(
                                winner=judge_data.get("winner", "tie"),
                                pro_score=float(judge_data.get("pro_score", 0)),
                                con_score=float(judge_data.get("con_score", 0)),
                                reasoning=judge_data.get("reasoning", ""),
                                fact_check_passed=True  # Assume passed for old debates
                            )

                        # Create migrated session
                        migrated = DebateSession(
                            id=debate_id,
                            topic=data.get("topic", "Unknown"),
                            domain=data.get("domain", "general"),
                            rounds=data.get("rounds", 2),
                            status="completed",
                            start_time=datetime.now().isoformat(),
                            end_time=datetime.now().isoformat(),
                            current_round=data.get("rounds", 2),
                            current_step="Completed",
                            progress=100,
                            pro_arguments=pro_arguments,
                            con_arguments=con_arguments,
                            judge_score=judge_score,
                        )
                        history.append(migrated)
                    else:
                        # New format - load directly
                        history.append(DebateSession(**data))

                except Exception as e:
                    print(f"Warning: Failed to load debate from {debate_dir}: {e}")
                    continue

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
    
    async def send_progress(event_type: str, step: str, round_num: int, progress: float, message: str, argument: dict = None, extra: dict = None):
        """Helper to send progress updates with proper event types."""
        debate.current_step = step
        debate.current_round = round_num
        debate.progress = progress
        
        print(f"  [{step}] Round {round_num} - {progress:.1f}% - {message}")
        
        if argument:
            arg = DebateArgument(
                side=argument["side"],
                round=argument.get("round", round_num),
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
            event_data = {
                "type": event_type,  # Required field for frontend
                "debate_id": debate_id,
                "status": debate.status,
                "step": step,
                "round": round_num,
                "progress": progress,
                "message": message,
            }
            if argument:
                event_data["side"] = argument["side"]
                event_data["content"] = argument["content"]
            if extra:
                event_data.update(extra)
            await queue.put(event_data)
    
    try:
        # Update status to running
        debate.status = "running"
        await send_progress("debate_started", "Initializing", 0, 0, "Loading CrewAI...", extra={"topic": request.topic})

        # Use preloaded crew or create new one
        crew = preloaded_crew
        if crew is None:
            print("[WARNING] No preloaded crew available, creating new one...")
            crew = DebateCrew(
                use_internet=request.use_internet,
                output_dir=PROJECT_ROOT / "runs" / "debates",
                verbose=True,
            )
        else:
            print(f"[INFO] Using preloaded crew (models already in memory)")
            # Update internet setting for this debate
            if request.use_internet:
                crew.enable_internet()
            else:
                crew.disable_internet()

        # Get event loop first before defining callback
        import concurrent.futures
        loop = asyncio.get_event_loop()

        # Create a thread-safe callback wrapper
        def progress_callback_sync(event_type, step, round_num, progress, message, data):
            """Thread-safe callback that schedules async progress updates."""
            try:
                # Schedule the coroutine in the event loop from the executor thread
                future = asyncio.run_coroutine_threadsafe(
                    send_progress(
                        event_type=event_type,
                        step=step,
                        round_num=round_num,
                        progress=progress,
                        message=message,
                        argument=data if event_type == "argument" else None,
                        extra=data if event_type != "argument" else None
                    ),
                    loop
                )
                # Wait briefly for the event to be queued
                try:
                    future.result(timeout=0.5)  # Increased timeout slightly
                    if event_type == "argument":
                        print(f"  → [CALLBACK] Sent {data.get('side', '?').upper()} argument via SSE")
                except asyncio.TimeoutError:
                    print(f"  ⚠ [CALLBACK] Timeout sending {event_type} event")
                except Exception as e:
                    print(f"  ✗ [CALLBACK] Error in future.result(): {e}")
            except Exception as e:
                print(f"  ✗ [CALLBACK] Failed to schedule {event_type}: {e}")

        # Run the debate synchronously in a thread pool with callback

        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                crew.run_debate,
                request.topic,
                request.rounds,
                request.recommend_guests,
                progress_callback_sync,
            )
        
        # Process results
        print(f"\n[RESULT] Debate completed!")
        print(f"  Winner: {result.judge_score.winner}")
        print(f"  Pro Score: {result.judge_score.pro_score}")
        print(f"  Con Score: {result.judge_score.con_score}")

        # Arguments were already sent via callback in real-time
        # Just ensure they're stored in the debate session
        for i, pro_arg in enumerate(result.pro_arguments):
            if i >= len(debate.pro_arguments):
                debate.pro_arguments.append(DebateArgument(
                    side="pro",
                    round=i + 1,
                    content=pro_arg,
                    timestamp=datetime.now().isoformat()
                ))

        for i, con_arg in enumerate(result.con_arguments):
            if i >= len(debate.con_arguments):
                debate.con_arguments.append(DebateArgument(
                    side="con",
                    round=i + 1,
                    content=con_arg,
                    timestamp=datetime.now().isoformat()
                ))
        
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
        
        # Send completion with proper type
        await send_progress(
            "debate_complete", "Completed", request.rounds, 100,
            f"Debate completed! Winner: {result.judge_score.winner.upper()}",
            extra={
                "winner": result.judge_score.winner,
                "judgeScore": {
                    "winner": result.judge_score.winner,
                    "proScore": result.judge_score.pro_score,
                    "conScore": result.judge_score.con_score,
                    "reasoning": result.judge_score.reasoning,
                }
            }
        )
        
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
                "type": "error",
                "debate_id": debate_id,
                "status": "error",
                "step": "Error",
                "round": 0,
                "message": str(e),
            })


# ============================================================================
# FastAPI App
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global debates, preloaded_crew

    # Load saved debates on startup
    for saved_debate in load_debate_history():
        debates[saved_debate.id] = saved_debate
    print(f"Loaded {len(debates)} debates from history")

    # Preload CrewAI models in memory for faster debate startup
    if CREWAI_AVAILABLE:
        print("\n" + "="*60)
        print("PRELOADING CREWAI MODELS...")
        print("="*60)
        try:
            preloaded_crew = DebateCrew(
                use_internet=False,  # Can be changed per debate
                output_dir=RUNS_DIR,
                verbose=True,
            )
            # Trigger lazy model loading
            _ = preloaded_crew.model_manager
            print("✓ Models preloaded successfully!")
            print("="*60 + "\n")
        except Exception as e:
            print(f"✗ Failed to preload models: {e}")
            print("Debates will load models on demand.")
            print("="*60 + "\n")
            preloaded_crew = None

    yield

    # Cleanup on shutdown
    print("Shutting down...")
    if preloaded_crew and preloaded_crew._model_manager:
        print("Unloading models...")
        # Models will be automatically garbage collected


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
# Human vs AI Debate Endpoints
# ============================================================================

@app.post("/api/debates/{debate_id}/human-turn")
async def submit_human_turn(debate_id: str, request: HumanTurnRequest):
    """Submit a human's argument in human_vs_ai mode."""
    if debate_id not in debates:
        raise HTTPException(status_code=404, detail="Debate not found")
    
    debate = debates[debate_id]
    
    # Validate debate state
    if debate.status not in ["running", "waiting_for_human", "pending"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Debate not accepting input, current status: {debate.status}"
        )
    
    if not request.argument.strip():
        raise HTTPException(status_code=400, detail="Argument cannot be empty")
    
    # Store the human argument - this is a simplified implementation
    # Full turn-taking would require refactoring DebateCrew.run_debate()
    # For now, we acknowledge the submission
    print(f"[HUMAN TURN] Debate {debate_id}: received argument ({len(request.argument)} chars)")
    
    return {
        "status": "submitted",
        "message": "Argument received successfully. Note: Full human vs AI turn-taking is not yet implemented."
    }


# ============================================================================
# Lesson (Teacher) Endpoints
# ============================================================================

async def run_teacher_lesson(lesson_id: str, request: LessonRequest):
    """Run lesson generation using TeacherCrew in background."""
    lesson = lessons.get(lesson_id)
    if not lesson:
        print(f"[ERROR] Lesson {lesson_id} not found")
        return
    
    queue = lesson_progress_queues.get(lesson_id)
    
    print(f"\n{'='*60}")
    print(f"STARTING LESSON GENERATION: {lesson_id}")
    print(f"Topic: {request.topic}")
    print(f"Level: {request.detail_level}")
    print(f"{'='*60}\n")
    
    async def send_progress(step: str, progress: float, message: str):
        """Send lesson progress update."""
        lesson.current_step = step
        lesson.progress = progress
        print(f"  [{step}] {progress:.1f}% - {message}")
        
        if queue:
            await queue.put({
                "type": "lesson_progress",
                "lesson_id": lesson_id,
                "status": lesson.status,
                "step": step,
                "progress": progress,
                "message": message,
            })
    
    try:
        lesson.status = "running"
        # Send lesson_started event so frontend can set topic and status
        if queue:
            await queue.put({
                "type": "lesson_started",
                "lesson_id": lesson_id,
                "topic": request.topic,
                "status": "running",
            })
        await send_progress("Initializing", 0, "Loading TeacherCrew...")
        
        # Use preloaded teacher crew or create new one
        if TEACHER_AVAILABLE:
            teacher = preloaded_teacher_crew
            if teacher is None:
                await send_progress("Loading", 10, "Creating TeacherCrew instance...")
                teacher = TeacherCrew(
                    use_internet=request.use_internet,
                    output_dir=LESSONS_DIR,
                    verbose=True,
                )
            else:
                if request.use_internet:
                    teacher.enable_internet()
                else:
                    teacher.disable_internet()
            
            await send_progress("Researching", 20, "Gathering research on topic...")
            
            # Run teaching in thread pool
            import concurrent.futures
            loop = asyncio.get_event_loop()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor,
                    teacher.teach,
                    request.topic,
                    request.detail_level,
                )
            
            await send_progress("Generating", 80, "Structuring lesson content...")
            
            # Convert result to our model
            lesson.domain = result.domain
            lesson.lesson = LessonSection(
                topic=result.lesson.topic,
                overview=result.lesson.overview,
                key_concepts=result.lesson.key_concepts or [],
                examples=result.lesson.examples or [],
                quiz_questions=result.lesson.quiz_questions or [],
            )
            lesson.end_time = datetime.now().isoformat()
            lesson.progress = 100
            lesson.current_step = "Completed"
            
            # Send completion progress (while status is still "running" so SSE doesn't close)
            await send_progress("Completed", 100, "Lesson generation complete!")
            
            # Now send the lesson_complete event with the lesson data
            # This will trigger SSE stream to close after client receives the lesson
            lesson.status = "completed"
            if queue:
                await queue.put({
                    "type": "lesson_complete",
                    "lesson_id": lesson_id,
                    "status": "completed",
                    "lesson": lesson.lesson.model_dump() if lesson.lesson else None,
                })
        else:
            raise Exception(f"TeacherCrew not available: {TEACHER_ERROR}")
            
    except Exception as e:
        import traceback
        print(f"[ERROR] Lesson generation failed: {e}")
        traceback.print_exc()
        
        lesson.status = "error"
        lesson.error = str(e)
        
        if queue:
            await queue.put({
                "type": "error",
                "lesson_id": lesson_id,
                "status": "error",
                "message": str(e),
            })


@app.post("/api/lessons", response_model=LessonResponse)
async def create_lesson(request: LessonRequest, background_tasks: BackgroundTasks):
    """Create and generate a new lesson using TeacherCrew."""
    if not TEACHER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail=f"TeacherCrew is not available: {TEACHER_ERROR}"
        )
    
    lesson_id = f"lesson-{uuid.uuid4().hex[:12]}"
    
    lesson = LessonSession(
        id=lesson_id,
        topic=request.topic,
        domain="unknown",  # Will be determined during generation
        detail_level=request.detail_level,
        status="pending",
        start_time=datetime.now().isoformat(),
    )
    
    lessons[lesson_id] = lesson
    lesson_progress_queues[lesson_id] = asyncio.Queue()
    
    # Start lesson generation in background
    background_tasks.add_task(run_teacher_lesson, lesson_id, request)
    
    return LessonResponse(
        id=lesson_id,
        status="created",
        message="Lesson created and generation starting..."
    )


@app.get("/api/lessons/{lesson_id}", response_model=LessonSession)
async def get_lesson(lesson_id: str):
    """Get lesson details."""
    if lesson_id not in lessons:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lessons[lesson_id]


@app.get("/api/lessons", response_model=List[LessonSession])
async def list_lessons(limit: int = 50, offset: int = 0):
    """List all lessons with pagination."""
    all_lessons = list(lessons.values())
    all_lessons.sort(key=lambda l: l.start_time, reverse=True)
    return all_lessons[offset:offset + limit]


@app.get("/api/lessons/{lesson_id}/stream")
async def stream_lesson_progress(lesson_id: str):
    """Server-Sent Events stream for real-time lesson generation progress."""
    if lesson_id not in lessons:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    async def event_stream() -> AsyncGenerator[str, None]:
        queue = lesson_progress_queues.get(lesson_id)
        if not queue:
            queue = asyncio.Queue()
            lesson_progress_queues[lesson_id] = queue
        
        try:
            while True:
                try:
                    progress = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(progress)}\n\n"
                    
                    if progress.get("status") in ["completed", "error"]:
                        break
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield ": keepalive\n\n"
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


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("Debate Simulator XP - API Server")
    print("=" * 60)
    print(f"CrewAI Available: {CREWAI_AVAILABLE}")
    print(f"TeacherCrew Available: {TEACHER_AVAILABLE}")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Runs Directory: {RUNS_DIR}")
    print(f"Lessons Directory: {LESSONS_DIR}")
    print(f"Server Port: 5040")
    print("=" * 60)
    
    uvicorn.run(
        "run_xp_server:app",
        host="0.0.0.0",
        port=5040,
        reload=True,
        reload_dirs=[str(PROJECT_ROOT / "scripts")],
    )
