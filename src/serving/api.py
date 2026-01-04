"""
FastAPI server for the debate simulator.

Provides REST API endpoints for the React frontend.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.serving.models import (
    HealthResponse,
    TopicSearchResponse,
    TopicDetail,
    StartDebateRequest,
    StartDebateResponse,
    SendTurnRequest,
    SendTurnResponse,
    ScoreDebateRequest,
    ScoreDebateResponse,
    PlayerProfile,
)
from src.serving.topics import search_topics, get_topic
from src.serving.profile import load_profile, update_profile, add_match_result
from src.serving.debate_service import debate_service

# Create FastAPI app
app = FastAPI(
    title="Debate Simulator API",
    description="Backend API for the multi-agent debate simulator",
    version="1.0.0",
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Health Check
# ============================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if the API is running and model is loaded."""
    model_loaded = debate_service._model is not None
    return HealthResponse(
        ok=True,
        version="1.0.0" + (" (model loaded)" if model_loaded else " (no model)"),
    )


# ============================================================
# Topics
# ============================================================

@app.get("/topics/search", response_model=TopicSearchResponse)
async def search_topics_endpoint(q: str = Query(default="", description="Search query")):
    """Search for debate topics."""
    return search_topics(q)


@app.get("/topics/{topic_id}", response_model=TopicDetail)
async def get_topic_endpoint(topic_id: str):
    """Get detailed information about a topic."""
    topic = get_topic(topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail=f"Topic not found: {topic_id}")
    return topic


# ============================================================
# Debates
# ============================================================

@app.post("/debates", response_model=StartDebateResponse)
async def start_debate(request: StartDebateRequest):
    """Start a new debate session."""
    return debate_service.start_debate(request)


@app.post("/debates/{debate_id}/turns", response_model=SendTurnResponse)
async def send_turn(debate_id: str, request: SendTurnRequest):
    """Send a debate turn and get AI response."""
    # Ensure debate_id matches
    if request.debateId != debate_id:
        request.debateId = debate_id

    try:
        return debate_service.send_turn(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/debates/{debate_id}/score", response_model=ScoreDebateResponse)
async def score_debate(debate_id: str, request: ScoreDebateRequest):
    """Get final score for a completed debate."""
    # Ensure debate_id matches
    if request.debateId != debate_id:
        request.debateId = debate_id

    try:
        result = debate_service.score_debate(request)

        # Update player profile with result
        session = debate_service.get_session(debate_id)
        if session:
            won = result.finalScore >= 75  # Win threshold
            add_match_result(
                username="default",  # TODO: Get from auth
                topic=session.topic_title,
                mode=session.mode,
                score=result.finalScore,
                won=won,
                achievements_unlocked=result.achievementsUnlocked,
            )

        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================
# Profile
# ============================================================

@app.get("/profile", response_model=PlayerProfile)
async def get_profile():
    """Get the current player's profile."""
    return load_profile("default")


@app.post("/profile", response_model=PlayerProfile)
async def update_profile_endpoint(request: dict):
    """Update the player's profile."""
    return update_profile("default", request)


# ============================================================
# Startup Event
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Log startup message."""
    print("=" * 50)
    print("Debate Simulator API Started")
    print("=" * 50)
    print("Endpoints:")
    print("  GET  /health")
    print("  GET  /topics/search?q=...")
    print("  GET  /topics/{id}")
    print("  POST /debates")
    print("  POST /debates/{id}/turns")
    print("  POST /debates/{id}/score")
    print("  GET  /profile")
    print("  POST /profile")
    print("=" * 50)
