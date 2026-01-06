import type { z } from "zod";
import {
  DebateModeSchema,
  DebateStatusSchema,
  ParticipantTypeSchema,
  StanceSchema,
  CreateDebateRequestSchema,
  CreateDebateResponseSchema,
  CreateTurnRequestSchema,
  CreateTurnResponseSchema,
  DebateGetResponseSchema,
  DebateSchema,
  DebaterOutputSchema,
  HealthResponseSchema,
  JudgeOutputSchema,
  LeaderboardResponseSchema,
  PlayerProfileSchema,
  ResearchOutputSchema,
  RunDebateRequestSchema,
  RunDebateResponseSchema,
  ScoreDebateResponseSchema,
  TopicBriefRequestSchema,
  TopicBriefResponseSchema,
  TopicDetailSchema,
  TopicSearchResponseSchema,
  TopicSummarySchema,
  UpdateProfileRequestSchema
} from "./schemas";

export type DebateMode = z.infer<typeof DebateModeSchema>;
export type DebateStatus = z.infer<typeof DebateStatusSchema>;
export type ParticipantType = z.infer<typeof ParticipantTypeSchema>;
export type Stance = z.infer<typeof StanceSchema>;
export type HealthResponse = z.infer<typeof HealthResponseSchema>;
export type TopicSummary = z.infer<typeof TopicSummarySchema>;
export type TopicDetail = z.infer<typeof TopicDetailSchema>;
export type TopicSearchResponse = z.infer<typeof TopicSearchResponseSchema>;
export type TopicBriefRequest = z.infer<typeof TopicBriefRequestSchema>;
export type TopicBriefResponse = z.infer<typeof TopicBriefResponseSchema>;
export type CreateDebateRequest = z.infer<typeof CreateDebateRequestSchema>;
export type CreateDebateResponse = z.infer<typeof CreateDebateResponseSchema>;
export type Debate = z.infer<typeof DebateSchema>;
export type DebateGetResponse = z.infer<typeof DebateGetResponseSchema>;
export type CreateTurnRequest = z.infer<typeof CreateTurnRequestSchema>;
export type CreateTurnResponse = z.infer<typeof CreateTurnResponseSchema>;
export type RunDebateRequest = z.infer<typeof RunDebateRequestSchema>;
export type RunDebateResponse = z.infer<typeof RunDebateResponseSchema>;
export type ScoreDebateResponse = z.infer<typeof ScoreDebateResponseSchema>;
export type PlayerProfile = z.infer<typeof PlayerProfileSchema>;
export type UpdateProfileRequest = z.infer<typeof UpdateProfileRequestSchema>;
export type LeaderboardResponse = z.infer<typeof LeaderboardResponseSchema>;
export type ResearchOutput = z.infer<typeof ResearchOutputSchema>;
export type DebaterOutput = z.infer<typeof DebaterOutputSchema>;
export type JudgeOutput = z.infer<typeof JudgeOutputSchema>;
