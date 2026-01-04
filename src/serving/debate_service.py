"""
Debate service - bridges the API with the LLM for real-time debate.

Manages active debate sessions and generates AI responses.
"""

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

import torch
from transformers import GenerationConfig

from src.serving.models import (
    StartDebateRequest,
    StartDebateResponse,
    SendTurnRequest,
    SendTurnResponse,
    UpdatedScores,
    ScoreDebateRequest,
    ScoreDebateResponse,
    ScoreBreakdown,
)
from src.serving.topics import get_topic, get_topic_by_title


@dataclass
class DebateMessage:
    """A single message in the debate."""
    role: str  # "human" or "ai"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    scores: dict | None = None


@dataclass
class DebateSession:
    """Active debate session state."""
    id: str
    topic_id: str | None
    topic_title: str
    stance: str
    mode: str
    difficulty: str
    timer_seconds: int
    messages: list[DebateMessage] = field(default_factory=list)
    combo_streak: int = 0
    total_scores: dict = field(default_factory=lambda: {
        "argument_strength": [],
        "evidence_use": [],
        "civility": [],
        "relevance": [],
    })
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ended: bool = False


class DebateService:
    """
    Service for managing debate sessions and generating AI responses.

    Holds a reference to the loaded model for efficient inference.
    """

    def __init__(self, model=None, tokenizer=None):
        """
        Initialize the debate service.

        Args:
            model: Pre-loaded LLM model
            tokenizer: Pre-loaded tokenizer
        """
        self._model = model
        self._tokenizer = tokenizer
        self._sessions: dict[str, DebateSession] = {}

    def set_model(self, model, tokenizer):
        """Set the model and tokenizer after initialization."""
        self._model = model
        self._tokenizer = tokenizer

    def _get_difficulty_params(self, difficulty: str) -> dict:
        """Get generation parameters based on difficulty."""
        params = {
            "easy": {
                "temperature": 0.8,
                "max_new_tokens": 150,
                "style": "casual and accessible",
            },
            "medium": {
                "temperature": 0.7,
                "max_new_tokens": 200,
                "style": "balanced and reasoned",
            },
            "hard": {
                "temperature": 0.6,
                "max_new_tokens": 250,
                "style": "rigorous and evidence-based",
            },
        }
        return params.get(difficulty, params["medium"])

    def _build_prompt(
        self,
        session: DebateSession,
        human_message: str,
    ) -> str:
        """Build the prompt for the AI response."""
        # Get topic info if available
        topic_info = ""
        if session.topic_id:
            topic = get_topic(session.topic_id)
            if topic:
                topic_info = f"\nKey points: {', '.join(topic.keyPoints[:3])}"

        # AI takes opposite stance
        ai_stance = "con" if session.stance == "pro" else "pro"
        stance_desc = "in favor" if ai_stance == "pro" else "against"

        difficulty_params = self._get_difficulty_params(session.difficulty)

        system_msg = f"""You are an expert debate opponent. The topic is: {session.topic_title}

You are arguing {stance_desc} (the {ai_stance.upper()} position).{topic_info}

Your style should be {difficulty_params['style']}.
Respond directly to your opponent's arguments with a single focused counterargument.
Be concise (2-3 sentences max). Do not use bullet points or lists."""

        # Build conversation history
        history = ""
        for msg in session.messages[-4:]:  # Last 4 messages for context
            role = "Human" if msg.role == "human" else "AI"
            history += f"\n{role}: {msg.content}"

        user_msg = f"""Previous exchange:{history}

Human's latest argument: {human_message}

Respond with your counterargument:"""

        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{system_msg}<|eot_id|><|start_header_id|>user<|end_header_id|>

{user_msg}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
        return prompt

    def _generate_response(
        self,
        prompt: str,
        difficulty: str,
    ) -> str:
        """Generate AI response using the model."""
        if self._model is None or self._tokenizer is None:
            # Fallback for when model isn't loaded
            return "I acknowledge your point. However, we must consider the broader implications and evidence that suggests a different perspective."

        params = self._get_difficulty_params(difficulty)

        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)

        generation_config = GenerationConfig(
            max_new_tokens=params["max_new_tokens"],
            temperature=params["temperature"],
            top_p=0.9,
            do_sample=True,
            pad_token_id=self._tokenizer.pad_token_id,
            eos_token_id=self._tokenizer.eos_token_id,
        )

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                generation_config=generation_config,
            )

        full_response = self._tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract just the assistant's response
        if "Respond with your counterargument:" in full_response:
            response = full_response.split("Respond with your counterargument:")[-1].strip()
        else:
            response = full_response[len(prompt):].strip()

        # Clean up common artifacts
        response = response.split("<|")[0].strip()  # Remove any remaining tokens
        response = response.split("\n\n")[0].strip()  # Take first paragraph

        return response if response else "I see your point, but let me offer an alternative perspective based on the evidence available."

    def _score_argument(self, message: str, session: DebateSession) -> UpdatedScores:
        """
        Score a human argument.

        Uses heuristics similar to JudgeAgent but adapted for live scoring.
        """
        message_lower = message.lower()
        word_count = len(message.split())

        # Argument strength (based on length and structure)
        length_score = min(word_count / 30, 1.0) * 40 + 50
        logical_markers = ['because', 'therefore', 'thus', 'however', 'furthermore', 'moreover']
        logic_bonus = sum(5 for m in logical_markers if m in message_lower)
        argument_strength = min(int(length_score + logic_bonus), 100)

        # Evidence use (citations and data references)
        evidence_markers = ['study', 'research', 'data', 'percent', '%', 'according', 'evidence', 'shows']
        evidence_count = sum(1 for m in evidence_markers if m in message_lower)
        evidence_use = min(60 + evidence_count * 15, 100)

        # Civility (absence of hostile language)
        hostile_markers = ['stupid', 'idiot', 'wrong', 'nonsense', 'ridiculous', 'dumb']
        hostile_count = sum(1 for m in hostile_markers if m in message_lower)
        civility = max(95 - hostile_count * 20, 50)

        # Relevance (topic keywords)
        topic_words = set(session.topic_title.lower().split())
        topic_words.discard('should')
        topic_words.discard('be')
        topic_words.discard('the')
        message_words = set(message_lower.split())
        overlap = len(topic_words & message_words)
        relevance = min(60 + overlap * 15, 100)

        # Add some randomness for variety
        import random
        argument_strength = max(50, min(100, argument_strength + random.randint(-5, 5)))
        evidence_use = max(50, min(100, evidence_use + random.randint(-5, 5)))
        civility = max(50, min(100, civility + random.randint(-3, 3)))
        relevance = max(50, min(100, relevance + random.randint(-5, 5)))

        return UpdatedScores(
            argumentStrength=argument_strength,
            evidenceUse=evidence_use,
            civility=civility,
            relevance=relevance,
        )

    def start_debate(self, request: StartDebateRequest) -> StartDebateResponse:
        """
        Start a new debate session.

        Args:
            request: Debate configuration

        Returns:
            StartDebateResponse with session ID
        """
        session_id = f"debate-{uuid.uuid4().hex[:8]}"

        session = DebateSession(
            id=session_id,
            topic_id=request.topicId,
            topic_title=request.topicTitle,
            stance=request.stance,
            mode=request.mode,
            difficulty=request.difficulty,
            timer_seconds=request.timerSeconds,
        )

        self._sessions[session_id] = session

        return StartDebateResponse(
            debateId=session_id,
            initialState={"judgeEnabled": True},
        )

    def send_turn(self, request: SendTurnRequest) -> SendTurnResponse:
        """
        Process a human turn and generate AI response.

        Args:
            request: Human message and debate ID

        Returns:
            AI response with updated scores
        """
        session = self._sessions.get(request.debateId)
        if not session:
            raise ValueError(f"Debate session not found: {request.debateId}")

        # Record human message
        human_msg = DebateMessage(
            role="human",
            content=request.message,
        )
        session.messages.append(human_msg)

        # Score the human argument
        scores = self._score_argument(request.message, session)

        # Track scores for final calculation
        session.total_scores["argument_strength"].append(scores.argumentStrength)
        session.total_scores["evidence_use"].append(scores.evidenceUse)
        session.total_scores["civility"].append(scores.civility)
        session.total_scores["relevance"].append(scores.relevance)

        # Check combo (all scores >= 85)
        events = []
        if all(s >= 85 for s in [
            scores.argumentStrength,
            scores.evidenceUse,
            scores.civility,
            scores.relevance,
        ]):
            session.combo_streak += 1
            events.append(f"combo+{session.combo_streak}")
        else:
            session.combo_streak = 0

        # Generate AI response
        prompt = self._build_prompt(session, request.message)
        ai_response = self._generate_response(prompt, session.difficulty)

        # Record AI message
        ai_msg = DebateMessage(
            role="ai",
            content=ai_response,
        )
        session.messages.append(ai_msg)

        return SendTurnResponse(
            aiMessage=ai_response,
            updatedScores=scores,
            events=events if events else None,
        )

    def score_debate(self, request: ScoreDebateRequest) -> ScoreDebateResponse:
        """
        Calculate final debate score.

        Args:
            request: Debate ID to score

        Returns:
            Final scores and achievements
        """
        session = self._sessions.get(request.debateId)
        if not session:
            raise ValueError(f"Debate session not found: {request.debateId}")

        session.ended = True

        # Calculate average scores
        def avg(lst):
            return sum(lst) / len(lst) if lst else 70

        breakdown = ScoreBreakdown(
            argumentStrength=int(avg(session.total_scores["argument_strength"])),
            evidenceUse=int(avg(session.total_scores["evidence_use"])),
            civility=int(avg(session.total_scores["civility"])),
            relevance=int(avg(session.total_scores["relevance"])),
        )

        final_score = int((
            breakdown.argumentStrength +
            breakdown.evidenceUse +
            breakdown.civility +
            breakdown.relevance
        ) / 4)

        # Determine achievements
        achievements = []
        if session.combo_streak >= 3:
            achievements.append("combo-starter")
        if session.combo_streak >= 5:
            achievements.append("combo-king")
        if breakdown.evidenceUse >= 90:
            achievements.append("evidence-master")
        if breakdown.civility >= 95:
            achievements.append("civil-debater")

        return ScoreDebateResponse(
            finalScore=final_score,
            breakdown=breakdown,
            achievementsUnlocked=achievements if achievements else None,
        )

    def get_session(self, debate_id: str) -> DebateSession | None:
        """Get a debate session by ID."""
        return self._sessions.get(debate_id)


# Global service instance (will be initialized with model at startup)
debate_service = DebateService()
