import type {
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
import type { ApiAdapter } from "./adapter";
import { getEnv } from "../utils/env";
import { mockAdapter } from "./mocks/mockAdapter";
import { useDebateStore } from "../state/debateStore";

type ChatMessage = {
  role: "system" | "user" | "assistant";
  content: string;
};

const debates = new Map<string, StartDebateRequest>();

const difficultyGuidance = {
  easy: {
    temperature: 0.6,
    maxTokens: 180,
    guidance: "Keep replies short (2-3 sentences) and easy to follow."
  },
  medium: {
    temperature: 0.7,
    maxTokens: 240,
    guidance: "Use clear arguments with light evidence in 2-4 sentences."
  },
  hard: {
    temperature: 0.85,
    maxTokens: 320,
    guidance: "Use rigorous rebuttals with evidence in 3-5 sentences."
  }
};

const getGuidance = (difficulty?: StartDebateRequest["difficulty"]) => {
  if (difficulty && difficultyGuidance[difficulty]) {
    return difficultyGuidance[difficulty];
  }
  return difficultyGuidance.medium;
};

const getAiStance = (stance?: StartDebateRequest["stance"]) => {
  if (stance === "pro") {
    return "con";
  }
  if (stance === "con") {
    return "pro";
  }
  return "balanced";
};

const buildSystemPrompt = (payload?: StartDebateRequest) => {
  const state = useDebateStore.getState();
  const topic = payload?.topicTitle || state.topicTitle || "the current topic";
  const stance = payload?.stance || state.stance;
  const difficulty = payload?.difficulty || state.difficulty;
  const mode = payload?.mode || state.mode;
  const aiStance = getAiStance(stance);
  const guidance = getGuidance(difficulty);

  return [
    "You are the AI Opponent in a debate simulation.",
    `Topic: ${topic}.`,
    `Human stance: ${stance || "neutral"}.`,
    `Your stance: ${aiStance}.`,
    `Mode: ${mode || "human-vs-ai"}.`,
    guidance.guidance,
    "Be civil, concise, and specific. Offer rebuttals and a follow-up question."
  ].join(" ");
};

const isAiRole = (role: string, payload?: StartDebateRequest) => {
  const participant = payload?.participants.find((item) => item.name === role);
  if (participant) {
    return participant.type === "ai";
  }
  return role.toLowerCase().includes("ai");
};

const buildMessages = (payload: StartDebateRequest | undefined, request: SendTurnRequest) => {
  const state = useDebateStore.getState();
  const transcript = state.transcript.slice(-12);
  const messages: ChatMessage[] = [
    {
      role: "system",
      content: buildSystemPrompt(payload)
    }
  ];

  transcript.forEach((message) => {
    if (!message.content.trim()) {
      return;
    }
    const role = isAiRole(message.role, payload) ? "assistant" : "user";
    const content = role === "user" ? `${message.role}: ${message.content}` : message.content;
    messages.push({ role, content });
  });

  const last = transcript[transcript.length - 1];
  if (!last || last.content.trim() !== request.message.trim()) {
    messages.push({
      role: "user",
      content: `${request.role}: ${request.message}`
    });
  }

  return messages;
};

const getScoreRange = (difficulty: StartDebateRequest["difficulty"] | undefined) => {
  switch (difficulty) {
    case "easy":
      return { min: 55, max: 85 };
    case "hard":
      return { min: 75, max: 95 };
    default:
      return { min: 65, max: 90 };
  }
};

const clampScore = (value: number) => Math.max(0, Math.min(100, value));

const rollScore = (min: number, max: number, bonus: number) => {
  const score = Math.floor(min + Math.random() * (max - min + 1) + bonus);
  return clampScore(score);
};

const buildScores = (difficulty: StartDebateRequest["difficulty"] | undefined, input: string) => {
  const { min, max } = getScoreRange(difficulty);
  const bonus = Math.min(8, Math.floor(input.trim().length / 80));
  return {
    argumentStrength: rollScore(min, max, bonus),
    evidenceUse: rollScore(min, max, bonus),
    civility: rollScore(min, max, bonus),
    relevance: rollScore(min, max, bonus)
  };
};

export const openRouterAdapter: ApiAdapter = {
  health: async () => ({ ok: true, version: "openrouter" }),
  searchTopics: async (query: string): Promise<TopicSearchResponse> =>
    mockAdapter.searchTopics(query),
  getTopic: async (id: string): Promise<TopicDetail> => mockAdapter.getTopic(id),
  startDebate: async (payload: StartDebateRequest): Promise<StartDebateResponse> => {
    const response = await mockAdapter.startDebate(payload);
    debates.set(response.debateId, payload);
    return response;
  },
  sendTurn: async (payload: SendTurnRequest): Promise<SendTurnResponse> => {
    const env = getEnv();
    const apiKey = env.openRouterApiKey;
    if (!apiKey) {
      throw new Error("Missing VITE_OPENROUTER_API_KEY");
    }
    const debatePayload = debates.get(payload.debateId);
    const difficulty = debatePayload?.difficulty || useDebateStore.getState().difficulty;
    const guidance = getGuidance(difficulty);
    const baseUrl = env.openRouterBaseUrl || "https://openrouter.ai/api/v1";
    const model = env.openRouterModel || "nvidia/nemotron-nano-9b-v2:free";
    const messages = buildMessages(debatePayload, payload);

    const response = await fetch(`${baseUrl}/chat/completions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model,
        messages,
        temperature: guidance.temperature,
        max_tokens: guidance.maxTokens
      })
    });

    const data = (await response.json()) as {
      choices?: { message?: { content?: string } }[];
      error?: { message?: string };
    };

    if (!response.ok) {
      const message = data?.error?.message || "OpenRouter request failed.";
      throw new Error(message);
    }

    const aiMessage = data.choices?.[0]?.message?.content?.trim();
    if (!aiMessage) {
      throw new Error("OpenRouter returned no message content.");
    }

    return {
      aiMessage,
      updatedScores: buildScores(difficulty, payload.message)
    };
  },
  scoreDebate: async (_payload: ScoreDebateRequest): Promise<ScoreDebateResponse> =>
    mockAdapter.scoreDebate(_payload),
  getProfile: async (): Promise<PlayerProfileResponse> => mockAdapter.getProfile(),
  updateProfile: async (payload): Promise<PlayerProfileResponse> => mockAdapter.updateProfile(payload)
};
