import { z } from "zod";

export const DebateModeSchema = z.enum(["HUMAN_VS_AI", "COPS_VS_AI", "AI_VS_AI", "HUMAN_VS_HUMAN"]);
export const DebateStatusSchema = z.enum(["CREATED", "RUNNING", "ENDED", "CANCELLED"]);
export const ParticipantTypeSchema = z.enum(["HUMAN", "AI", "JUDGE"]);
export const StanceSchema = z.enum(["PRO", "CON", "MODERATOR"]);

export const SourceSchema = z.object({
  url: z.string().url(),
  title: z.string(),
  snippet: z.string(),
  usedFor: z.enum(["briefing", "counterargument", "factcheck"]),
  turnId: z.string().optional()
});

export const TopicSummarySchema = z.object({
  id: z.string(),
  title: z.string(),
  category: z.string(),
  summary: z.string()
});

export const TopicDetailSchema = TopicSummarySchema.extend({
  description: z.string(),
  keyPoints: z.array(z.string()),
  pros: z.array(z.string()),
  cons: z.array(z.string()),
  fallacies: z.array(z.string()),
  sources: z.array(SourceSchema)
});

export const HealthResponseSchema = z.object({
  ok: z.boolean(),
  version: z.string(),
  time: z.string()
});

export const TopicSearchQuerySchema = z.object({
  q: z.string().min(1).max(200)
});

export const TopicSearchResponseSchema = z.object({
  results: z.array(TopicSummarySchema)
});

export const TopicBriefRequestSchema = z.object({
  topic: z.string().min(1).max(200),
  stance: z.enum(["PRO", "CON"]).nullable().optional(),
  depth: z.enum(["quick", "deep"]).optional().default("quick")
});

export const TopicBriefResponseSchema = z.object({
  topic: z.string(),
  briefing: z.object({
    keyFacts: z.array(z.string()),
    proArguments: z.array(z.string()),
    conArguments: z.array(z.string()),
    counterArguments: z.array(z.string()),
    questions: z.array(z.string())
  }),
  sources: z.array(SourceSchema)
});

export const ParticipantInputSchema = z.object({
  type: z.enum(["HUMAN", "AI"]),
  name: z.string().min(1).max(40),
  stance: z.enum(["PRO", "CON"])
});

export const CreateDebateRequestSchema = z.object({
  mode: DebateModeSchema,
  topic: z.string().min(1).max(200),
  rounds: z.number().int().min(1).max(10),
  turnSeconds: z.number().int().min(30).max(900).optional(),
  participants: z.array(ParticipantInputSchema).min(1).max(4)
});

export const DebateParticipantSchema = z.object({
  id: z.string(),
  type: ParticipantTypeSchema,
  name: z.string(),
  stance: StanceSchema,
  roleLabel: z.string()
});

export const DebateSchema = z.object({
  id: z.string(),
  mode: DebateModeSchema,
  topic: z.string(),
  rounds: z.number().int(),
  turnSeconds: z.number().int().nullable(),
  status: DebateStatusSchema,
  participants: z.array(DebateParticipantSchema),
  createdAt: z.string(),
  updatedAt: z.string()
});

export const CreateDebateResponseSchema = z.object({
  debateId: z.string(),
  debate: DebateSchema
});

export const TurnSchema = z.object({
  id: z.string(),
  debateId: z.string(),
  participantId: z.string(),
  roleLabel: z.string(),
  content: z.string(),
  createdAt: z.string()
});

export const TurnScoreSchema = z.object({
  clarity: z.number().int().min(0).max(100),
  logic: z.number().int().min(0).max(100),
  evidence: z.number().int().min(0).max(100),
  rebuttal: z.number().int().min(0).max(100),
  civility: z.number().int().min(0).max(100),
  relevance: z.number().int().min(0).max(100)
});

export const DebateGetResponseSchema = z.object({
  debate: DebateSchema,
  turns: z.array(TurnSchema),
  liveScores: z.record(z.string(), TurnScoreSchema).optional()
});

export const CreateTurnRequestSchema = z.object({
  participantId: z.string(),
  content: z.string().min(1).max(4000)
});

export const CreateTurnResponseSchema = z.object({
  acceptedTurn: TurnSchema,
  aiTurns: z.array(TurnSchema).optional(),
  updatedScores: TurnScoreSchema,
  events: z.array(z.string()).optional()
});

export const RunDebateRequestSchema = z.object({
  autoRounds: z.number().int().min(1).max(10).optional()
});

export const RunDebateResponseSchema = z.object({
  started: z.boolean()
});

export const ScoreDebateResponseSchema = z.object({
  finalScore: z.number().int(),
  breakdown: TurnScoreSchema,
  winner: z.string().nullable(),
  judgeReport: z.object({
    explanation: z.string(),
    highlights: z.array(z.string()),
    fallacies: z.array(z.string())
  }),
  achievementsUnlocked: z.array(z.string()).optional()
});

export const PlayerProfileSchema = z.object({
  playerId: z.string(),
  username: z.string(),
  avatar: z.string(),
  level: z.number().int(),
  xp: z.number().int(),
  xpNext: z.number().int(),
  rankTitle: z.string(),
  stats: z.object({
    wins: z.number().int(),
    losses: z.number().int(),
    winRate: z.number(),
    averageScore: z.number(),
    bestStreak: z.number().int(),
    topicsPlayed: z.number().int()
  }),
  achievements: z.array(
    z.object({
      id: z.string(),
      title: z.string(),
      description: z.string(),
      unlocked: z.boolean()
    })
  ),
  history: z.array(
    z.object({
      id: z.string(),
      topic: z.string(),
      mode: z.string(),
      date: z.string(),
      score: z.number().int(),
      result: z.string()
    })
  )
});

export const UpdateProfileRequestSchema = z.object({
  playerId: z.string().optional(),
  username: z.string().min(1).max(40).optional(),
  avatar: z.string().optional()
});

export const LeaderboardResponseSchema = z.object({
  players: z.array(PlayerProfileSchema)
});

export const ResearchOutputSchema = z.object({
  keyFacts: z.array(z.string()),
  proArguments: z.array(z.string()),
  conArguments: z.array(z.string()),
  counterArguments: z.array(z.string()),
  questions: z.array(z.string()),
  sources: z.array(SourceSchema)
});

export const DebaterOutputSchema = z.object({
  message: z.string().min(1),
  citations: z.array(z.string()).optional()
});

export const JudgeOutputSchema = z.object({
  winnerParticipantId: z.string().nullable(),
  scores: z.record(z.string(), TurnScoreSchema),
  explanation: z.string(),
  highlights: z.array(z.string()),
  fallacies: z.array(z.string()),
  achievements: z.array(z.string()).optional()
});

// =============================================
// Agent Framework Schemas
// =============================================

export const AgentRequestSchema = z.object({
  input: z.string().min(1).max(1000),
  context: z.record(z.string(), z.unknown()).optional()
});

export const AgentSuccessResponseSchema = z.object({
  ok: z.literal(true),
  data: z.unknown()
});

export const AgentErrorResponseSchema = z.object({
  ok: z.literal(false),
  error: z.object({
    code: z.enum(["BAD_REQUEST", "LLM_ERROR", "VALIDATION_FAILED", "SERVER_ERROR", "AGENT_NOT_FOUND"]),
    message: z.string()
  })
});

export const AgentResponseSchema = z.union([AgentSuccessResponseSchema, AgentErrorResponseSchema]);

// =============================================
// AiTheme Schema (Theme Agent)
// =============================================

// Safe font allowlist
const FONT_ALLOWLIST = ["Tahoma", "Verdana", "Arial", "Trebuchet MS", "Courier New"] as const;

// Color validation: HEX (#RGB, #RRGGBB) or rgb()/rgba()
const colorPattern = /^(#[0-9A-Fa-f]{3}|#[0-9A-Fa-f]{6}|rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)|rgba\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*[\d.]+\s*\))$/;

// Safe shadow pattern: simple box-shadow (e.g., "2px 2px 0 rgba(0,0,0,0.35)")
const shadowPattern = /^-?\d+px\s+-?\d+px\s+\d+px?\s+(#[0-9A-Fa-f]{3,6}|rgba?\([^)]+\))$/;

export const AiThemeTokensSchema = z.object({
  fontFamily: z.enum(FONT_ALLOWLIST),
  fontSizeBasePx: z.number().min(12).max(20).transform(v => Math.round(Math.min(20, Math.max(12, v)))),
  bg: z.string().regex(colorPattern, "Invalid color format"),
  panel: z.string().regex(colorPattern, "Invalid color format"),
  text: z.string().regex(colorPattern, "Invalid color format"),
  mutedText: z.string().regex(colorPattern, "Invalid color format"),
  primary: z.string().regex(colorPattern, "Invalid color format"),
  primaryText: z.string().regex(colorPattern, "Invalid color format"),
  border: z.string().regex(colorPattern, "Invalid color format"),
  radiusPx: z.number().min(0).max(16).transform(v => Math.round(Math.min(16, Math.max(0, v)))),
  shadow: z.string().regex(shadowPattern, "Invalid shadow format").catch("2px 2px 0 rgba(0,0,0,0.35)")
}).strict();

export const AiThemeMetaSchema = z.object({
  prompt: z.string(),
  model: z.string(),
  createdAt: z.string()
}).optional();

export const AiThemeSchema = z.object({
  name: z.string().min(1).max(50),
  tokens: AiThemeTokensSchema,
  meta: AiThemeMetaSchema
}).strict();
