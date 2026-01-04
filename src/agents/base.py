"""
Base classes for the multi-agent debate system.

Implements a state machine architecture where each agent
processes and transforms the debate context.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AgentState(Enum):
    """States in the debate orchestration pipeline."""
    INIT = "init"
    ROUTING = "routing"
    RESEARCHING = "researching"
    DEBATING_PRO = "debating_pro"
    DEBATING_CON = "debating_con"
    FACT_CHECKING = "fact_checking"
    JUDGING = "judging"
    LOGGING = "logging"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class DebateTurn:
    """Single turn in a debate."""
    stance: str  # "pro" or "con"
    argument: str
    sources: list[str] = field(default_factory=list)
    fact_check_result: dict | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class JudgeScore:
    """Structured scoring from the judge."""
    pro_score: float  # 0-10
    con_score: float  # 0-10
    winner: str  # "pro", "con", or "tie"
    reasoning: str
    criteria_scores: dict[str, dict[str, float]] = field(default_factory=dict)


@dataclass
class DebateContext:
    """
    Shared context passed between agents in the pipeline.

    This is the "state" that flows through the state machine,
    accumulating information as each agent processes it.
    """
    # Input
    topic: str
    domain: str | None = None
    num_rounds: int = 2

    # State tracking
    current_state: AgentState = AgentState.INIT
    current_round: int = 0
    error_message: str | None = None

    # Research
    retrieved_passages: list[dict] = field(default_factory=list)
    corpus_stats: dict = field(default_factory=dict)

    # Debate turns
    pro_turns: list[DebateTurn] = field(default_factory=list)
    con_turns: list[DebateTurn] = field(default_factory=list)

    # Judgment
    judge_score: JudgeScore | None = None

    # Metrics and logging
    metrics: dict = field(default_factory=dict)
    agent_logs: list[dict] = field(default_factory=list)

    # Timestamps
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None

    def log_agent_action(self, agent_name: str, action: str, details: dict | None = None):
        """Log an agent's action for debugging and metrics."""
        self.agent_logs.append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "action": action,
            "state": self.current_state.value,
            "details": details or {},
        })


class Agent(ABC):
    """
    Abstract base class for debate agents.

    Each agent:
    1. Receives a DebateContext
    2. Performs its specific function
    3. Updates the context
    4. Returns the updated context with a new state
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def process(self, context: DebateContext) -> DebateContext:
        """
        Process the debate context and return updated context.

        Args:
            context: Current debate context

        Returns:
            Updated context with new state
        """
        pass

    def _log(self, context: DebateContext, action: str, details: dict | None = None):
        """Helper to log agent actions."""
        context.log_agent_action(self.name, action, details)
