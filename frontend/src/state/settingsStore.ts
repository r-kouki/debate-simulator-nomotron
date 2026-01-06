import { create } from "zustand";
import { getEnv } from "../utils/env";

export type Difficulty = "easy" | "medium" | "hard";

export type SettingsState = {
  username: string;
  soundEnabled: boolean;
  difficultyDefault: Difficulty;
  timerSeconds: number;
  apiBaseUrlOverride: string;
  useMocks: boolean;
  setUsername: (value: string) => void;
  setSoundEnabled: (value: boolean) => void;
  setDifficultyDefault: (value: Difficulty) => void;
  setTimerSeconds: (value: number) => void;
  setApiBaseUrlOverride: (value: string) => void;
  setUseMocks: (value: boolean) => void;
};

const env = getEnv();

export const useSettingsStore = create<SettingsState>((set) => ({
  username: "Player1",
  soundEnabled: true,
  difficultyDefault: "medium",
  timerSeconds: 180,
  apiBaseUrlOverride: "",
  useMocks: env.useMocks,
  setUsername: (value) => set({ username: value }),
  setSoundEnabled: (value) => set({ soundEnabled: value }),
  setDifficultyDefault: (value) => set({ difficultyDefault: value }),
  setTimerSeconds: (value) => set({ timerSeconds: value }),
  setApiBaseUrlOverride: (value) => set({ apiBaseUrlOverride: value }),
  setUseMocks: (value) => set({ useMocks: value })
}));
