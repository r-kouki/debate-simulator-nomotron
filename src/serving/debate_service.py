"""
Debate service - bridges the API with the LLM for real-time debate.

Manages active debate sessions and generates AI responses.
Supports AI vs AI mode, web research, and structured debate phases.
"""

import re
import uuid
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from enum import Enum

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
from src.utils.web_search import quick_research, ResearchData


class DebatePhase(Enum):
    """Phases of a structured debate."""
    OPENING = "opening"
    REBUTTAL = "rebuttal"
    CLOSING = "closing"


@dataclass
class DebateMessage:
    """A single message in the debate."""
    role: str  # "human", "pro_ai", "con_ai"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    scores: dict | None = None
    phase: str = ""  # opening, rebuttal, closing


@dataclass
class DebateSession:
    """Active debate session state."""
    id: str
    topic_id: str | None
    topic_title: str
    stance: str
    mode: str  # "human-vs-ai", "cops-vs-ai", "ai-vs-ai"
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
    # New fields for enhanced debates
    current_phase: DebatePhase = DebatePhase.OPENING
    turn_number: int = 0
    research_data: ResearchData | None = None
    current_speaker: str = "pro"  # For AI vs AI: "pro" or "con"


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
                "max_new_tokens": 300,
                "style": "casual, conversational, and easy to understand",
            },
            "medium": {
                "temperature": 0.7,
                "max_new_tokens": 400,
                "style": "balanced, well-reasoned, using both logic and examples",
            },
            "hard": {
                "temperature": 0.6,
                "max_new_tokens": 500,
                "style": "rigorous, evidence-based, with sophisticated rhetorical techniques",
            },
        }
        return params.get(difficulty, params["medium"])

    def _get_phase_instructions(self, phase: DebatePhase, stance: str) -> str:
        """Get phase-specific debate instructions."""
        stance_word = "in favor of" if stance == "pro" else "against"
        
        instructions = {
            DebatePhase.OPENING: f"""
You are presenting your OPENING ARGUMENT {stance_word} the topic.

Structure your opening:
1. Start with a compelling hook or question
2. State your thesis clearly
3. Present 2-3 main supporting points with evidence
4. End with a preview of your key argument

Be persuasive and set the tone for the debate.""",
            
            DebatePhase.REBUTTAL: f"""
You are in the REBUTTAL phase, arguing {stance_word} the topic.

Your task:
1. Directly address and counter your opponent's main points
2. Expose weaknesses in their reasoning
3. Provide counter-evidence or alternative interpretations
4. Reinforce your own position with new evidence

Be respectful but firm in your disagreement.""",
            
            DebatePhase.CLOSING: f"""
You are presenting your CLOSING ARGUMENT {stance_word} the topic.

Structure your closing:
1. Summarize the key points of contention
2. Explain why your arguments were stronger
3. Address any remaining doubts
4. End with a powerful, memorable conclusion

Leave a lasting impression on the audience.""",
        }
        return instructions.get(phase, instructions[DebatePhase.REBUTTAL])

    def _build_prompt(
        self,
        session: DebateSession,
        human_message: str,
        is_ai_vs_ai: bool = False,
        ai_stance: str = "",
    ) -> str:
        """Build the prompt for the AI response."""
        # Determine stance
        if is_ai_vs_ai:
            stance = ai_stance
        else:
            # AI takes opposite stance in human vs AI
            stance = "con" if session.stance == "pro" else "pro"
        
        stance_desc = "in favor" if stance == "pro" else "against"
        difficulty_params = self._get_difficulty_params(session.difficulty)
        phase_instructions = self._get_phase_instructions(session.current_phase, stance)
        
        # Get research context
        research_context = ""
        if session.research_data:
            if stance == "pro" and session.research_data.pro_arguments:
                research_context = "\n\nRelevant research supporting your position:\n"
                for arg in session.research_data.pro_arguments[:2]:
                    research_context += f"- {arg}\n"
            elif stance == "con" and session.research_data.con_arguments:
                research_context = "\n\nRelevant research supporting your position:\n"
                for arg in session.research_data.con_arguments[:2]:
                    research_context += f"- {arg}\n"
            if session.research_data.facts:
                research_context += f"\nKey fact: {session.research_data.facts[0]}\n"
        
        # Build conversation history
        history = ""
        for msg in session.messages[-6:]:  # More context for better responses
            if msg.role == "human":
                history += f"\nOpponent: {msg.content}"
            elif msg.role in ["pro_ai", "con_ai", "ai"]:
                speaker = "You" if (stance == "pro" and msg.role == "pro_ai") or (stance == "con" and msg.role == "con_ai") else "Opponent"
                history += f"\n{speaker}: {msg.content}"
        
        system_msg = f"""You are an expert debater with years of experience in competitive debate.

TOPIC: {session.topic_title}
YOUR POSITION: {stance.upper()} ({stance_desc})
PHASE: {session.current_phase.value.upper()}

{phase_instructions}
{research_context}
STYLE REQUIREMENTS:
- Your style should be {difficulty_params['style']}
- Sound natural and human, not like a machine
- Use rhetorical questions, analogies, and emotional appeals where appropriate
- Vary your sentence structure and length
- Be confident and persuasive
- DO NOT use bullet points or numbered lists in your response
- Write in flowing paragraphs"""

        if is_ai_vs_ai:
            user_msg = f"""Debate history:{history}

Now present your {session.current_phase.value} argument:"""
        else:
            user_msg = f"""Debate exchange:{history}

Opponent's latest argument: {human_message}

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
        
        # Perform web research for the topic
        research_data = None
        try:
            print(f"[DebateService] Researching topic: {request.topicTitle}")
            research_data = quick_research(request.topicTitle)
            print(f"[DebateService] Found {len(research_data.pro_arguments)} pro, {len(research_data.con_arguments)} con arguments")
        except Exception as e:
            print(f"[DebateService] Web research failed: {e}")

        session = DebateSession(
            id=session_id,
            topic_id=request.topicId,
            topic_title=request.topicTitle,
            stance=request.stance,
            mode=request.mode,
            difficulty=request.difficulty,
            timer_seconds=request.timerSeconds,
            research_data=research_data,
        )

        self._sessions[session_id] = session

        return StartDebateResponse(
            debateId=session_id,
            initialState={
                "judgeEnabled": True,
                "mode": request.mode,
                "hasResearch": research_data is not None,
            },
        )

    def generate_next_turn(self, debate_id: str) -> dict:
        """
        Generate the next turn in AI vs AI mode.
        
        Args:
            debate_id: ID of the debate session
            
        Returns:
            Dict with the generated message and metadata
        """
        session = self._sessions.get(debate_id)
        if not session:
            raise ValueError(f"Debate session not found: {debate_id}")
        
        if session.mode != "ai-vs-ai":
            raise ValueError("generate_next_turn is only for ai-vs-ai mode")
        
        # Determine current speaker based on turn number
        current_speaker = "pro" if session.turn_number % 2 == 0 else "con"
        
        # Update phase based on turn number
        if session.turn_number < 2:
            session.current_phase = DebatePhase.OPENING
        elif session.turn_number < 6:
            session.current_phase = DebatePhase.REBUTTAL
        else:
            session.current_phase = DebatePhase.CLOSING
        
        # Build prompt for current speaker
        prompt = self._build_prompt(
            session=session,
            human_message="",
            is_ai_vs_ai=True,
            ai_stance=current_speaker,
        )
        
        # Generate response
        response = self._generate_response(prompt, session.difficulty)
        
        # Store message
        role = f"{current_speaker}_ai"
        msg = DebateMessage(
            role=role,
            content=response,
            phase=session.current_phase.value,
        )
        session.messages.append(msg)
        session.turn_number += 1
        
        # Update speaker for next turn
        session.current_speaker = "con" if current_speaker == "pro" else "pro"
        
        # Check if debate should end (after closing arguments)
        is_complete = session.turn_number >= 8
        if is_complete:
            session.ended = True
        
        return {
            "speaker": current_speaker.upper(),
            "message": response,
            "phase": session.current_phase.value,
            "turnNumber": session.turn_number,
            "isComplete": is_complete,
        }

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
