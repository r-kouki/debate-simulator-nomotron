import type {
  LeaderboardResponse,
  PlayerProfileResponse,
  ScoreDebateRequest,
  ScoreDebateResponse,
  SendTurnRequest,
  SendTurnResponse,
  StartDebateRequest,
  StartDebateResponse,
  TopicDetail,
  TopicSearchResponse
} from "../types";
import type { ApiAdapter } from "../adapter";
import { useProfileStore } from "../../state/profileStore";

const topics: TopicDetail[] = [
  {
    id: "ai-education",
    title: "AI in Education",
    category: "Technology",
    summary: "Should AI tutors be integrated into classrooms?",
    description:
      "AI tools can personalize learning but raise concerns about privacy and equity.",
    keyPoints: ["Personalization", "Teacher workload", "Data privacy"],
    pros: ["Adaptive learning", "Accessibility", "Scalable tutoring"],
    cons: ["Data privacy", "Bias risk", "Dependency on tech"],
    fallacies: ["Appeal to novelty", "False dilemma"],
    sources: ["https://example.com/ai-edu-report", "https://example.com/education-policy"]
  },
  {
    id: "ubi",
    title: "Universal Basic Income",
    category: "Policy",
    summary: "Is universal basic income a viable safety net?",
    description:
      "UBI proposes unconditional cash payments to all citizens to reduce poverty.",
    keyPoints: ["Economic security", "Labor market shifts", "Funding models"],
    pros: ["Reduces poverty", "Supports automation transition"],
    cons: ["Funding challenges", "Inflation concerns"],
    fallacies: ["Slippery slope", "Cherry picking"],
    sources: ["https://example.com/ubi-study", "https://example.com/ubi-pilot"]
  }
];

const debates = new Map<string, StartDebateRequest>();

const delay = async (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const randomScore = () => Math.floor(70 + Math.random() * 30);

// Mock leaderboard data
const mockLeaderboardPlayers = [
  { username: "DebateMaster", level: 25, wins: 150, losses: 30 },
  { username: "LogicKing", level: 22, wins: 120, losses: 40 },
  { username: "ArgumentAce", level: 20, wins: 100, losses: 35 },
  { username: "ReasonRuler", level: 18, wins: 90, losses: 45 },
  { username: "FactFinder", level: 16, wins: 75, losses: 50 }
];

export const mockAdapter: ApiAdapter = {
  health: async () => {
    await delay(200);
    return { ok: true, version: "mock" };
  },
  searchTopics: async (query: string): Promise<TopicSearchResponse> => {
    await delay(200);
    const results = topics
      .filter((topic) => topic.title.toLowerCase().includes(query.toLowerCase()))
      .map(({ id, title, category, summary }) => ({ id, title, category, summary }));
    return { results };
  },
  getTopic: async (id: string): Promise<TopicDetail> => {
    await delay(200);
    const detail = topics.find((topic) => topic.id === id);
    if (!detail) {
      throw new Error("Topic not found");
    }
    return detail;
  },
  startDebate: async (payload: StartDebateRequest): Promise<StartDebateResponse> => {
    await delay(300);
    const debateId = `debate-${Math.random().toString(36).slice(2, 8)}`;
    debates.set(debateId, payload);
    return { debateId, initialState: { judgeEnabled: true } };
  },
  sendTurn: async (_payload: SendTurnRequest): Promise<SendTurnResponse> => {
    await delay(500);
    return {
      aiMessage:
        "Acknowledged. Here is a counterpoint with evidence and a civility boost.",
      updatedScores: {
        argumentStrength: randomScore(),
        evidenceUse: randomScore(),
        civility: randomScore(),
        relevance: randomScore()
      },
      events: ["combo+1"]
    };
  },
  scoreDebate: async (_payload: ScoreDebateRequest): Promise<ScoreDebateResponse> => {
    await delay(400);
    return {
      finalScore: randomScore(),
      breakdown: {
        argumentStrength: randomScore(),
        evidenceUse: randomScore(),
        civility: randomScore(),
        relevance: randomScore()
      },
      achievementsUnlocked: ["first-win", "combo-king"]
    };
  },
  getProfile: async (): Promise<PlayerProfileResponse> => {
    await delay(200);
    const state = useProfileStore.getState();
    return {
      username: state.username,
      avatar: state.avatar,
      level: state.level,
      xp: state.xp,
      xpNext: state.xpNext,
      rankTitle: state.rankTitle,
      stats: state.stats,
      achievements: state.achievements,
      history: state.history
    };
  },
  updateProfile: async (payload): Promise<PlayerProfileResponse> => {
    await delay(200);
    useProfileStore.getState().setProfile(payload);
    return mockAdapter.getProfile();
  },
  getLeaderboard: async (params): Promise<LeaderboardResponse> => {
    await delay(300);
    const page = params?.page ?? 1;
    const pageSize = params?.pageSize ?? 10;

    const players = mockLeaderboardPlayers.map((p, idx) => ({
      rank: idx + 1,
      playerId: `player-${idx + 1}`,
      username: p.username,
      avatar: "🎯",
      level: p.level,
      stats: {
        wins: p.wins,
        losses: p.losses,
        winRate: Math.round((p.wins / (p.wins + p.losses)) * 100),
        averageScore: 75 + Math.floor(Math.random() * 20),
        bestStreak: Math.floor(Math.random() * 10) + 3,
        topicsPlayed: p.wins + p.losses
      },
      achievements: [{ id: "veteran", title: "Veteran", description: "100+ debates", unlocked: true }],
      recentMatches: [
        { topic: "AI Ethics", result: "Win" as const, score: 85, date: new Date().toISOString() }
      ]
    }));

    return {
      players,
      totalPlayers: players.length,
      page,
      pageSize
    };
  }
};
