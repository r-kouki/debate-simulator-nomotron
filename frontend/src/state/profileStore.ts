import { create } from "zustand";

export type Achievement = {
  id: string;
  title: string;
  description: string;
  unlocked: boolean;
};

export type MatchHistory = {
  id: string;
  topic: string;
  mode: string;
  date: string;
  score: number;
  result: "Win" | "Loss" | "Draw";
};

export type ProfileStats = {
  wins: number;
  losses: number;
  winRate: number;
  averageScore: number;
  bestStreak: number;
  topicsPlayed: number;
};

export type PlayerProfileState = {
  username: string;
  avatar: string;
  level: number;
  xp: number;
  xpNext: number;
  rankTitle: string;
  stats: ProfileStats;
  achievements: Achievement[];
  history: MatchHistory[];
  setProfile: (partial: Partial<PlayerProfileState>) => void;
  unlockAchievements: (ids: string[]) => void;
  addMatch: (match: MatchHistory) => void;
};

const defaultAchievements: Achievement[] = [
  { id: "first-win", title: "First Win", description: "Win your first debate", unlocked: false },
  { id: "perfect-100", title: "Perfect 100", description: "Score a perfect 100", unlocked: false },
  { id: "streak-5", title: "Five Streak", description: "Win five in a row", unlocked: false },
  { id: "evidence-master", title: "Evidence Master", description: "Score 90+ on evidence", unlocked: false },
  { id: "calm-debater", title: "Calm Debater", description: "Score 90+ on civility", unlocked: false },
  { id: "topic-explorer", title: "Explorer", description: "Research 5 topics", unlocked: false },
  { id: "speed-run", title: "Speed Run", description: "Win a debate in under 2 minutes", unlocked: false },
  { id: "combo-king", title: "Combo King", description: "Hit a 3x combo", unlocked: false },
  { id: "judge-pleaser", title: "Judge Pleaser", description: "Get 90+ relevance", unlocked: false },
  { id: "team-player", title: "Team Player", description: "Complete a Cops vs AI match", unlocked: false },
  { id: "steady-hand", title: "Steady Hand", description: "No forfeits in 3 matches", unlocked: false },
  { id: "night-owl", title: "Night Owl", description: "Debate after midnight", unlocked: false }
];

export const useProfileStore = create<PlayerProfileState>((set) => ({
  username: "Player1",
  avatar: "profile",
  level: 4,
  xp: 320,
  xpNext: 500,
  rankTitle: "Silver Debater",
  stats: {
    wins: 12,
    losses: 5,
    winRate: 70,
    averageScore: 82,
    bestStreak: 4,
    topicsPlayed: 9
  },
  achievements: defaultAchievements,
  history: [
    {
      id: "match-1",
      topic: "AI in Education",
      mode: "Human vs AI",
      date: "2024-08-12",
      score: 86,
      result: "Win"
    },
    {
      id: "match-2",
      topic: "Universal Basic Income",
      mode: "Cops vs AI",
      date: "2024-08-10",
      score: 78,
      result: "Loss"
    }
  ],
  setProfile: (partial) => set((state) => ({ ...state, ...partial })),
  unlockAchievements: (ids) =>
    set((state) => ({
      achievements: state.achievements.map((item) =>
        ids.includes(item.id) ? { ...item, unlocked: true } : item
      )
    })),
  addMatch: (match) =>
    set((state) => {
      const wins = state.stats.wins + (match.result === "Win" ? 1 : 0);
      const losses = state.stats.losses + (match.result === "Loss" ? 1 : 0);
      const totalMatches = wins + losses;
      const averageScore = Math.round(
        (state.stats.averageScore * state.history.length + match.score) /
          Math.max(state.history.length + 1, 1)
      );
      return {
        history: [match, ...state.history].slice(0, 10),
        stats: {
          ...state.stats,
          wins,
          losses,
          winRate: totalMatches > 0 ? Math.round((wins / totalMatches) * 100) : 0,
          averageScore,
          topicsPlayed: state.stats.topicsPlayed + 1
        }
      };
    })
}));
