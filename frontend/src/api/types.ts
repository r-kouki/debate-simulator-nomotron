export type TopicSummary = {
  id: string;
  title: string;
  category: string;
  summary: string;
};

export type TopicDetail = TopicSummary & {
  description: string;
  keyPoints: string[];
  pros: string[];
  cons: string[];
  fallacies: string[];
  sources: string[];
};

export type TopicSearchRequest = {
  query: string;
};

export type TopicSearchResponse = {
  results: TopicSummary[];
};

export type StartDebateRequest = {
  topicId?: string;
  topicTitle: string;
  stance: "pro" | "con" | "neutral";
  mode: "human-vs-ai" | "cops-vs-ai" | "ai-vs-ai";
  difficulty: "easy" | "medium" | "hard";
  participants: { name: string; type: "human" | "ai" | "judge" }[];
  timerSeconds: number;
};

export type StartDebateResponse = {
  debateId: string;
  initialState: {
    judgeEnabled: boolean;
  };
};

export type SendTurnRequest = {
  debateId: string;
  message: string;
  role: string;
};

export type SendTurnResponse = {
  aiMessage: string;
  updatedScores: {
    argumentStrength: number;
    evidenceUse: number;
    civility: number;
    relevance: number;
  };
  events?: string[];
};

export type ScoreDebateRequest = {
  debateId: string;
};

export type ScoreDebateResponse = {
  finalScore: number;
  breakdown: {
    argumentStrength: number;
    evidenceUse: number;
    civility: number;
    relevance: number;
  };
  achievementsUnlocked?: string[];
};

export type NextTurnResponse = {
  speaker: string;
  message: string;
  phase: string;
  turnNumber: number;
  isComplete: boolean;
};

export type PlayerProfile = {
  username: string;
  avatar: string;
  level: number;
  xp: number;
  xpNext: number;
  rankTitle: string;
  stats: {
    wins: number;
    losses: number;
    winRate: number;
    averageScore: number;
    bestStreak: number;
    topicsPlayed: number;
  };
  achievements: {
    id: string;
    title: string;
    description: string;
    unlocked: boolean;
  }[];
  history: {
    id: string;
    topic: string;
    mode: string;
    date: string;
    score: number;
    result: "Win" | "Loss" | "Draw";
  }[];
};

export type PlayerProfileResponse = PlayerProfile;

// Enhanced Leaderboard Types
export type LeaderboardEntry = {
  rank: number;
  playerId: string;
  username: string;
  avatar: string;
  level: number;
  stats: {
    wins: number;
    losses: number;
    winRate: number;
    averageScore: number;
    bestStreak: number;
    topicsPlayed: number;
  };
  achievements: {
    id: string;
    title: string;
    description: string;
    unlocked: boolean;
  }[];
  recentMatches: {
    topic: string;
    result: "Win" | "Loss" | "Draw";
    score: number;
    date: string;
  }[];
};

export type LeaderboardRequest = {
  page?: number;
  pageSize?: number;
  sortBy?: "xp" | "wins" | "winRate" | "averageScore";
};

export type LeaderboardResponse = {
  players: LeaderboardEntry[];
  totalPlayers: number;
  page: number;
  pageSize: number;
};

// =============================================
// Agent Framework Types
// =============================================

export type AgentRequest = {
  input: string;
  context?: Record<string, unknown>;
};

export type AgentSuccessResponse = {
  ok: true;
  data: unknown;
};

export type AgentErrorResponse = {
  ok: false;
  error: {
    code: string;
    message: string;
  };
};

export type AgentResponse = AgentSuccessResponse | AgentErrorResponse;

// =============================================
// AiTheme Types (Theme Agent)
// =============================================

export type AiThemeTokens = {
  fontFamily: "Tahoma" | "Verdana" | "Arial" | "Trebuchet MS" | "Courier New";
  fontSizeBasePx: number;
  bg: string;
  panel: string;
  text: string;
  mutedText: string;
  primary: string;
  primaryText: string;
  border: string;
  radiusPx: number;
  shadow: string;
};

export type AiThemeMeta = {
  prompt: string;
  model: string;
  createdAt: string;
};

export type AiTheme = {
  name: string;
  tokens: AiThemeTokens;
  meta?: AiThemeMeta;
};
