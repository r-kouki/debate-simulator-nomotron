import {
  LeaderboardRequest,
  LeaderboardResponse,
  NextTurnResponse,
  PlayerProfileResponse,
  ScoreDebateRequest,
  ScoreDebateResponse,
  SendTurnRequest,
  SendTurnResponse,
  StartDebateRequest,
  StartDebateResponse,
  TopicDetail,
  TopicSearchResponse
} from "./types";
import { createClient } from "./client";
import { mockAdapter } from "./mocks/mockAdapter";
import { openRouterAdapter } from "./openRouterAdapter";
import { useSettingsStore } from "../state/settingsStore";
import { getEnv } from "../utils/env";
import { useApiStatusStore } from "../state/apiStatusStore";
import { useNotificationStore } from "../state/notificationStore";
import { useWindowStore } from "../state/windowStore";

export type ApiAdapter = {
  health: () => Promise<{ ok: boolean; version?: string }>;
  searchTopics: (query: string) => Promise<TopicSearchResponse>;
  getTopic: (id: string) => Promise<TopicDetail>;
  getDebate: (id: string) => Promise<any>;
  startDebate: (payload: StartDebateRequest) => Promise<StartDebateResponse>;
  sendTurn: (payload: SendTurnRequest) => Promise<SendTurnResponse>;
  nextTurn: (debateId: string) => Promise<NextTurnResponse>;
  scoreDebate: (payload: ScoreDebateRequest) => Promise<ScoreDebateResponse>;
  getProfile: () => Promise<PlayerProfileResponse>;
  updateProfile: (payload: Partial<PlayerProfileResponse>) => Promise<PlayerProfileResponse>;
  getLeaderboard: (params?: LeaderboardRequest) => Promise<LeaderboardResponse>;
};

const createFetchAdapter = (baseUrl: string): ApiAdapter => {
  const client = createClient(baseUrl);
  return {
    health: () => client.get("/health"),
    searchTopics: (query) => client.get(`/topics/search?q=${encodeURIComponent(query)}`),
    getTopic: (id) => client.get(`/topics/${id}`),
    getDebate: (id) => client.get(`/debates/${id}`),
    startDebate: (payload) => client.post("/debates", payload),
    sendTurn: async (payload) => {
      const backendResponse = await client.post<{
        acceptedTurn: { content: string };
        aiTurns?: Array<{ content: string }>;
        updatedScores: {
          clarity: number;
          logic: number;
          evidence: number;
          rebuttal: number;
          civility: number;
          relevance: number;
        };
        events?: string[];
      }>(`/debates/${payload.debateId}/turns`, payload);

      // Transform backend response to frontend format
      return {
        aiMessage: backendResponse.aiTurns?.[0]?.content ?? "",
        updatedScores: {
          argumentStrength: Math.round((backendResponse.updatedScores.clarity + backendResponse.updatedScores.logic) / 2),
          evidenceUse: backendResponse.updatedScores.evidence,
          civility: backendResponse.updatedScores.civility,
          relevance: backendResponse.updatedScores.relevance
        },
        events: backendResponse.events
      };
    },
    nextTurn: (debateId) => client.post(`/debates/${debateId}/next-turn`, {}),
    scoreDebate: (payload) => client.post(`/debates/${payload.debateId}/score`, payload),
    getProfile: () => client.get("/profile"),
    updateProfile: (payload) => client.post("/profile", payload),
    getLeaderboard: (params) => {
      const query = new URLSearchParams();
      if (params?.page) query.set("page", String(params.page));
      if (params?.pageSize) query.set("pageSize", String(params.pageSize));
      if (params?.sortBy) query.set("sortBy", params.sortBy);
      const qs = query.toString();
      return client.get(`/leaderboard${qs ? `?${qs}` : ""}`);
    }
  };
};

const withFallback = (primary: ApiAdapter, fallback: ApiAdapter): ApiAdapter => {
  const wrap = async <T>(fn: () => Promise<T>, fallbackFn: () => Promise<T>) => {
    try {
      return await fn();
    } catch (error) {
      const message = error instanceof Error ? error.message : "API unavailable";
      useApiStatusStore.getState().setStatus(false, message);
      useNotificationStore.getState().push({
        type: "error",
        title: "API Offline",
        message: "Falling back to mock data."
      });
      useWindowStore.getState().openWindow("connection-status");
      return fallbackFn();
    }
  };

  return {
    health: async () => {
      try {
        return await primary.health();
      } catch (error) {
        const message = error instanceof Error ? error.message : "API unavailable";
        useApiStatusStore.getState().setStatus(false, message);
        useWindowStore.getState().openWindow("connection-status");
        return { ok: false, version: "mock-fallback" };
      }
    },
    searchTopics: (query) => wrap(() => primary.searchTopics(query), () => fallback.searchTopics(query)),
    getTopic: (id) => wrap(() => primary.getTopic(id), () => fallback.getTopic(id)),
    getDebate: (id) => wrap(() => primary.getDebate(id), () => fallback.getDebate(id)),
    startDebate: (payload) => wrap(() => primary.startDebate(payload), () => fallback.startDebate(payload)),
    sendTurn: (payload) => wrap(() => primary.sendTurn(payload), () => fallback.sendTurn(payload)),
    nextTurn: (debateId) => wrap(() => primary.nextTurn(debateId), () => fallback.nextTurn(debateId)),
    scoreDebate: (payload) => wrap(() => primary.scoreDebate(payload), () => fallback.scoreDebate(payload)),
    getProfile: () => wrap(() => primary.getProfile(), () => fallback.getProfile()),
    updateProfile: (payload) => wrap(() => primary.updateProfile(payload), () => fallback.updateProfile(payload)),
    getLeaderboard: (params) => wrap(() => primary.getLeaderboard(params), () => fallback.getLeaderboard(params))
  };
};

export const getApiAdapter = (): ApiAdapter => {
  const env = getEnv();
  const { apiBaseUrlOverride, useMocks } = useSettingsStore.getState();
  const baseUrl = apiBaseUrlOverride || env.apiBaseUrl;
  if (useMocks || !baseUrl) {
    if (env.openRouterApiKey && !useMocks) {
      return withFallback(openRouterAdapter, mockAdapter);
    }
    return mockAdapter;
  }
  return withFallback(createFetchAdapter(baseUrl), mockAdapter);
};
