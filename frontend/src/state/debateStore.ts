import { create } from "zustand";
import type { Difficulty } from "./settingsStore";

export type DebateMode = "human-vs-ai" | "cops-vs-ai" | "ai-vs-ai";

export type DebateStance = "pro" | "con" | "neutral";

export type Participant = {
  id: string;
  name: string;
  type: "human" | "ai" | "judge";
};

export type LiveScore = {
  argumentStrength: number;
  evidenceUse: number;
  civility: number;
  relevance: number;
};

export type DebateMessage = {
  id: string;
  role: string;
  content: string;
  scores?: LiveScore;
  timestamp: string;
};

export type MatchResult = {
  finalScore: number;
  breakdown: LiveScore;
  achievementsUnlocked: string[];
};

export type DebateState = {
  mode: DebateMode;
  topicId?: string;
  topicTitle: string;
  stance: DebateStance;
  difficulty: Difficulty;
  timerSeconds: number;
  participants: Participant[];
  debateId?: string;
  transcript: DebateMessage[];
  combo: number;
  streakBest: number;
  isPaused: boolean;
  timeRemaining: number;
  sessionStatus: "idle" | "active" | "ended";
  matchResult?: MatchResult;
  setTopic: (id: string, title: string) => void;
  configure: (payload: Partial<Omit<DebateState, "transcript" | "participants" | "sessionStatus" | "combo" | "streakBest" | "isPaused" | "timeRemaining" | "matchResult">>) => void;
  setParticipants: (participants: Participant[]) => void;
  startSession: (debateId: string, timeSeconds: number) => void;
  addMessage: (message: DebateMessage) => void;
  setLiveScore: (messageId: string, scores: LiveScore) => void;
  setPaused: (value: boolean) => void;
  tick: () => void;
  updateCombo: (scores: LiveScore) => void;
  endSession: (result: MatchResult) => void;
  reset: () => void;
};

const makeId = () => Math.random().toString(36).slice(2, 10);

export const useDebateStore = create<DebateState>((set, get) => ({
  mode: "human-vs-ai",
  topicId: undefined,
  topicTitle: "",
  stance: "pro",
  difficulty: "medium",
  timerSeconds: 180,
  participants: [],
  debateId: undefined,
  transcript: [],
  combo: 0,
  streakBest: 0,
  isPaused: false,
  timeRemaining: 0,
  sessionStatus: "idle",
  matchResult: undefined,
  setTopic: (id, title) => set({ topicId: id, topicTitle: title }),
  configure: (payload) => set(payload),
  setParticipants: (participants) => set({ participants }),
  startSession: (debateId, timeSeconds) =>
    set({
      debateId,
      timeRemaining: timeSeconds,
      sessionStatus: "active",
      isPaused: false,
      transcript: [],
      combo: 0,
      streakBest: 0,
      matchResult: undefined
    }),
  addMessage: (message) =>
    set((state) => ({
      transcript: [...state.transcript, { ...message, id: message.id || makeId() }]
    })),
  setLiveScore: (messageId, scores) =>
    set((state) => ({
      transcript: state.transcript.map((msg) =>
        msg.id === messageId ? { ...msg, scores } : msg
      )
    })),
  setPaused: (value) => set({ isPaused: value }),
  tick: () => {
    const state = get();
    if (state.isPaused || state.sessionStatus !== "active") {
      return;
    }
    const next = Math.max(state.timeRemaining - 1, 0);
    set({ timeRemaining: next });
    if (next === 0) {
      set({ sessionStatus: "ended" });
    }
  },
  updateCombo: (scores) =>
    set((state) => {
      const qualifies = Object.values(scores).every((value) => value >= 85);
      const combo = qualifies ? state.combo + 1 : 0;
      return {
        combo,
        streakBest: Math.max(state.streakBest, combo)
      };
    }),
  endSession: (result) => set({ sessionStatus: "ended", matchResult: result }),
  reset: () =>
    set({
      debateId: undefined,
      transcript: [],
      sessionStatus: "idle",
      combo: 0,
      streakBest: 0,
      isPaused: false,
      timeRemaining: 0,
      matchResult: undefined
    })
}));
