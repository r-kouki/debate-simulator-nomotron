import { prisma } from "./db";
import { randomUUID } from "node:crypto";

export const achievementSeed = [
  { id: "first-win", title: "First Win", description: "Win your first debate" },
  { id: "perfect-100", title: "Perfect 100", description: "Score a perfect 100" },
  { id: "streak-5", title: "Five Streak", description: "Win five in a row" },
  { id: "evidence-master", title: "Evidence Master", description: "Score 90+ on evidence" },
  { id: "calm-debater", title: "Calm Debater", description: "Score 90+ on civility" },
  { id: "topic-explorer", title: "Explorer", description: "Research 5 topics" },
  { id: "speed-run", title: "Speed Run", description: "Win a debate in under 2 minutes" },
  { id: "combo-king", title: "Combo King", description: "Hit a 3x combo" },
  { id: "judge-pleaser", title: "Judge Pleaser", description: "Get 90+ relevance" },
  { id: "team-player", title: "Team Player", description: "Complete a Cops vs AI match" },
  { id: "steady-hand", title: "Steady Hand", description: "No forfeits in 3 matches" },
  { id: "night-owl", title: "Night Owl", description: "Debate after midnight" }
];

export const seedAchievements = async () => {
  for (const achievement of achievementSeed) {
    await prisma.achievement.upsert({
      where: { id: achievement.id },
      update: {},
      create: achievement
    });
  }
};

export const createPlayerIfMissing = async (playerId?: string) => {
  const id = playerId || randomUUID();
  const existing = await prisma.player.findUnique({
    where: { id },
    include: { stats: true, achievements: { include: { achievement: true } }, history: true }
  });
  if (existing) {
    return existing;
  }
  const player = await prisma.player.create({
    data: {
      id,
      username: "Player",
      avatar: "profile",
      level: 1,
      xp: 0,
      rankTitle: "Rookie",
      stats: {
        create: {
          wins: 0,
          losses: 0,
          winRate: 0,
          averageScore: 0,
          bestStreak: 0,
          topicsPlayed: 0
        }
      },
      achievements: {
        create: achievementSeed.map((achievement) => ({
          achievement: { connect: { id: achievement.id } },
          unlocked: false
        }))
      }
    },
    include: { stats: true, achievements: { include: { achievement: true } }, history: true }
  });
  return player;
};

export const computeXp = (finalScore: number, didWin: boolean) => {
  const base = 50;
  const scoreBonus = Math.round(finalScore * 0.5);
  const winBonus = didWin ? 40 : 10;
  return base + scoreBonus + winBonus;
};

export const updatePlayerAfterMatch = async (input: {
  playerId: string;
  topic: string;
  mode: string;
  score: number;
  didWin: boolean;
}) => {
  const player = await createPlayerIfMissing(input.playerId);
  const stats = player.stats;
  const wins = stats?.wins ?? 0;
  const losses = stats?.losses ?? 0;
  const totalMatches = wins + losses;
  const nextWins = wins + (input.didWin ? 1 : 0);
  const nextLosses = losses + (input.didWin ? 0 : 1);
  const nextTotal = nextWins + nextLosses;
  const averageScore = stats
    ? Math.round((stats.averageScore * totalMatches + input.score) / Math.max(nextTotal, 1))
    : input.score;
  const xpEarned = computeXp(input.score, input.didWin);
  const nextXp = player.xp + xpEarned;
  const xpNext = player.level * 500;
  const levelUp = nextXp >= xpNext;

  await prisma.player.update({
    where: { id: input.playerId },
    data: {
      xp: nextXp,
      level: levelUp ? player.level + 1 : player.level,
      rankTitle: levelUp ? "Rising Debater" : player.rankTitle,
      stats: {
        update: {
          wins: nextWins,
          losses: nextLosses,
          winRate: nextTotal > 0 ? (nextWins / nextTotal) * 100 : 0,
          averageScore,
          topicsPlayed: (stats?.topicsPlayed ?? 0) + 1,
          bestStreak: Math.max(stats?.bestStreak ?? 0, input.didWin ? nextWins : 0)
        }
      },
      history: {
        create: {
          topic: input.topic,
          mode: input.mode,
          date: new Date(),
          score: input.score,
          result: input.didWin ? "Win" : "Loss"
        }
      }
    }
  });

  const unlocked: string[] = [];
  if (input.didWin) {
    unlocked.push("first-win");
  }
  if (input.score >= 100) {
    unlocked.push("perfect-100");
  }

  for (const id of unlocked) {
    await prisma.playerAchievement.updateMany({
      where: { playerId: input.playerId, achievementId: id },
      data: { unlocked: true, unlockedAt: new Date() }
    });
  }

  return { xpEarned, achievementsUnlocked: unlocked };
};
