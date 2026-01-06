"""
Pydantic models for the debate simulator API.

These models match the TypeScript types in frontend/src/api/types.ts

IMPORTANT: Field names are in camelCase to match frontend expectations.
Aliases are in snake_case for accepting snake_case input (optional).
By default, responses serialize using field names (camelCase).
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Literal


# Base config for all models - ensures camelCase serialization
class CamelCaseModel(BaseModel):
    """Base model that serializes to camelCase (field names, not aliases)."""
    model_config = ConfigDict(
        populate_by_name=True,  # Accept both camelCase and snake_case input
        # Serialization uses field names by default (camelCase), not aliases
    )


# Topic models
class TopicSummary(CamelCaseModel):
    id: str
    title: str
    category: str
    summary: str


class TopicDetail(TopicSummary):
    description: str
    keyPoints: list[str] = Field(default_factory=list)
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    fallacies: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class TopicSearchResponse(CamelCaseModel):
    results: list[TopicSummary]


# Debate models
class Participant(CamelCaseModel):
    name: str
    type: Literal["human", "ai", "judge"]


class StartDebateRequest(CamelCaseModel):
    topicId: str | None = Field(default=None)
    topicTitle: str
    stance: Literal["pro", "con", "neutral"]
    mode: Literal["human-vs-ai", "cops-vs-ai", "ai-vs-ai"]
    difficulty: Literal["easy", "medium", "hard"]
    participants: list[Participant]
    timerSeconds: int = Field(default=180)


class StartDebateResponse(CamelCaseModel):
    debateId: str
    initialState: dict


class SendTurnRequest(CamelCaseModel):
    debateId: str
    message: str
    role: str


class UpdatedScores(CamelCaseModel):
    argumentStrength: int
    evidenceUse: int
    civility: int
    relevance: int


class SendTurnResponse(CamelCaseModel):
    aiMessage: str
    updatedScores: UpdatedScores
    events: list[str] | None = None


class ScoreDebateRequest(CamelCaseModel):
    debateId: str


class ScoreBreakdown(CamelCaseModel):
    argumentStrength: int
    evidenceUse: int
    civility: int
    relevance: int


class ScoreDebateResponse(CamelCaseModel):
    finalScore: int
    breakdown: ScoreBreakdown
    achievementsUnlocked: list[str] | None = Field(default=None)


# Profile models
class PlayerStats(CamelCaseModel):
    wins: int = 0
    losses: int = 0
    winRate: float = Field(default=0.0)
    averageScore: float = Field(default=0.0)
    bestStreak: int = Field(default=0)
    topicsPlayed: int = Field(default=0)


class Achievement(CamelCaseModel):
    id: str
    title: str
    description: str
    unlocked: bool = False


class MatchHistory(CamelCaseModel):
    id: str
    topic: str
    mode: str
    date: str
    score: int
    result: Literal["Win", "Loss", "Draw"]


class PlayerProfile(CamelCaseModel):
    username: str = "Debater"
    avatar: str = "default"
    level: int = 1
    xp: int = 0
    xpNext: int = Field(default=100)
    rankTitle: str = Field(default="Novice")
    stats: PlayerStats = Field(default_factory=PlayerStats)
    achievements: list[Achievement] = Field(default_factory=list)
    history: list[MatchHistory] = Field(default_factory=list)


# Health check
class HealthResponse(CamelCaseModel):
    ok: bool
    version: str = "1.0.0"
