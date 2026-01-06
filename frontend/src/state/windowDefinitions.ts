import type { IconName } from "../components/Icon";

export type WindowType =
  | "new-debate"
  | "debate-session"
  | "match-results"
  | "topic-explorer"
  | "scoreboard"
  | "settings"
  | "help"
  | "about"
  | "connection-status"
  | "login"
  | "leaderboard";

export type WindowDefinition = {
  title: string;
  icon: IconName;
  defaultRect: { x: number; y: number; width: number; height: number };
};

export const windowDefinitions: Record<WindowType, WindowDefinition> = {
  "new-debate": {
    title: "New Debate",
    icon: "debate",
    defaultRect: { x: 60, y: 80, width: 420, height: 420 }
  },
  "debate-session": {
    title: "Debate Session",
    icon: "chat",
    defaultRect: { x: 120, y: 90, width: 620, height: 520 }
  },
  "match-results": {
    title: "Match Results",
    icon: "trophy",
    defaultRect: { x: 180, y: 120, width: 520, height: 420 }
  },
  "topic-explorer": {
    title: "Topic Explorer",
    icon: "search",
    defaultRect: { x: 80, y: 100, width: 700, height: 460 }
  },
  scoreboard: {
    title: "Scoreboard",
    icon: "score",
    defaultRect: { x: 140, y: 70, width: 560, height: 460 }
  },
  settings: {
    title: "Settings",
    icon: "gear",
    defaultRect: { x: 180, y: 90, width: 420, height: 380 }
  },
  help: {
    title: "Help",
    icon: "help",
    defaultRect: { x: 200, y: 120, width: 420, height: 340 }
  },
  about: {
    title: "About",
    icon: "info",
    defaultRect: { x: 240, y: 140, width: 360, height: 260 }
  },
  "connection-status": {
    title: "Connection Status",
    icon: "network",
    defaultRect: { x: 260, y: 160, width: 340, height: 220 }
  },
  login: {
    title: "Login",
    icon: "score",
    defaultRect: { x: 200, y: 100, width: 380, height: 320 }
  },
  leaderboard: {
    title: "Leaderboard",
    icon: "trophy",
    defaultRect: { x: 100, y: 60, width: 600, height: 460 }
  }
};

