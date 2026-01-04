"""
Pydantic models for the debate simulator API.

These models match the TypeScript types in frontend/src/api/types.ts
"""

from pydantic import BaseModel, Field
from typing import Literal


# Topic models
class TopicSummary(BaseModel):
    id: str
    title: str
    category: str
    summary: str


class TopicDetail(TopicSummary):
    description: str
    keyPoints: list[str] = Field(alias="key_points", default_factory=list)
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    fallacies: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class TopicSearchResponse(BaseModel):
    results: list[TopicSummary]


# Debate models
class Participant(BaseModel):
    name: str
    type: Literal["human", "ai", "judge"]


class StartDebateRequest(BaseModel):
    topicId: str | None = Field(default=None, alias="topic_id")
    topicTitle: str = Field(alias="topic_title")
    stance: Literal["pro", "con", "neutral"]
    mode: Literal["human-vs-ai", "cops-vs-ai"]
    difficulty: Literal["easy", "medium", "hard"]
    participants: list[Participant]
    timerSeconds: int = Field(alias="timer_seconds", default=180)

    class Config:
        populate_by_name = True


class StartDebateResponse(BaseModel):
    debateId: str = Field(alias="debate_id")
    initialState: dict = Field(alias="initial_state")

    class Config:
        populate_by_name = True


class SendTurnRequest(BaseModel):
    debateId: str = Field(alias="debate_id")
    message: str
    role: str

    class Config:
        populate_by_name = True


class UpdatedScores(BaseModel):
    argumentStrength: int = Field(alias="argument_strength")
    evidenceUse: int = Field(alias="evidence_use")
    civility: int
    relevance: int

    class Config:
        populate_by_name = True


class SendTurnResponse(BaseModel):
    aiMessage: str = Field(alias="ai_message")
    updatedScores: UpdatedScores = Field(alias="updated_scores")
    events: list[str] | None = None

    class Config:
        populate_by_name = True


class ScoreDebateRequest(BaseModel):
    debateId: str = Field(alias="debate_id")

    class Config:
        populate_by_name = True


class ScoreBreakdown(BaseModel):
    argumentStrength: int = Field(alias="argument_strength")
    evidenceUse: int = Field(alias="evidence_use")
    civility: int
    relevance: int

    class Config:
        populate_by_name = True


class ScoreDebateResponse(BaseModel):
    finalScore: int = Field(alias="final_score")
    breakdown: ScoreBreakdown
    achievementsUnlocked: list[str] | None = Field(default=None, alias="achievements_unlocked")

    class Config:
        populate_by_name = True


# Profile models
class PlayerStats(BaseModel):
    wins: int = 0
    losses: int = 0
    winRate: float = Field(default=0.0, alias="win_rate")
    averageScore: float = Field(default=0.0, alias="average_score")
    bestStreak: int = Field(default=0, alias="best_streak")
    topicsPlayed: int = Field(default=0, alias="topics_played")

    class Config:
        populate_by_name = True


class Achievement(BaseModel):
    id: str
    title: str
    description: str
    unlocked: bool = False


class MatchHistory(BaseModel):
    id: str
    topic: str
    mode: str
    date: str
    score: int
    result: Literal["Win", "Loss", "Draw"]


class PlayerProfile(BaseModel):
    username: str = "Debater"
    avatar: str = "default"
    level: int = 1
    xp: int = 0
    xpNext: int = Field(default=100, alias="xp_next")
    rankTitle: str = Field(default="Novice", alias="rank_title")
    stats: PlayerStats = Field(default_factory=PlayerStats)
    achievements: list[Achievement] = Field(default_factory=list)
    history: list[MatchHistory] = Field(default_factory=list)

    class Config:
        populate_by_name = True


# Health check
class HealthResponse(BaseModel):
    ok: bool
    version: str = "1.0.0"
