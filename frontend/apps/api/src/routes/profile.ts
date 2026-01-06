import type { FastifyInstance } from "fastify";
import { ZodTypeProvider } from "@fastify/type-provider-zod";
import { LeaderboardResponseSchema, PlayerProfileSchema, UpdateProfileRequestSchema } from "@debate/contracts";
import { prisma } from "../services/db";
import { createPlayerIfMissing } from "../services/gamification";

const mapProfile = (player: Awaited<ReturnType<typeof createPlayerIfMissing>>) => {
  const stats = player.stats;
  return {
    playerId: player.id,
    username: player.username,
    avatar: player.avatar,
    level: player.level,
    xp: player.xp,
    xpNext: player.level * 500,
    rankTitle: player.rankTitle,
    stats: {
      wins: stats?.wins ?? 0,
      losses: stats?.losses ?? 0,
      winRate: stats?.winRate ?? 0,
      averageScore: stats?.averageScore ?? 0,
      bestStreak: stats?.bestStreak ?? 0,
      topicsPlayed: stats?.topicsPlayed ?? 0
    },
    achievements: player.achievements.map((item) => ({
      id: item.achievement.id,
      title: item.achievement.title,
      description: item.achievement.description,
      unlocked: item.unlocked
    })),
    history: player.history.map((match) => ({
      id: match.id,
      topic: match.topic,
      mode: match.mode,
      date: match.date.toISOString(),
      score: match.score,
      result: match.result
    }))
  };
};

export const registerProfileRoutes = (app: FastifyInstance) => {
  const api = app.withTypeProvider<ZodTypeProvider>();

  api.get(
    "/profile",
    {
      schema: {
        response: { 200: PlayerProfileSchema }
      }
    },
    async (request) => {
      const playerId = request.query && (request.query as { playerId?: string }).playerId;
      const player = await createPlayerIfMissing(playerId);
      return mapProfile(player);
    }
  );

  api.post(
    "/profile",
    {
      schema: {
        body: UpdateProfileRequestSchema,
        response: { 200: PlayerProfileSchema }
      }
    },
    async (request) => {
      const { playerId, username, avatar } = request.body;
      const player = await createPlayerIfMissing(playerId);
      const updated = await prisma.player.update({
        where: { id: player.id },
        data: {
          username: username ?? player.username,
          avatar: avatar ?? player.avatar
        },
        include: { stats: true, achievements: { include: { achievement: true } }, history: true }
      });
      return mapProfile(updated);
    }
  );

  api.get(
    "/leaderboard",
    {
      schema: {
        response: { 200: LeaderboardResponseSchema }
      }
    },
    async () => {
      const players = await prisma.player.findMany({
        include: { stats: true, achievements: { include: { achievement: true } }, history: true },
        orderBy: { xp: "desc" },
        take: 10
      });
      return { players: players.map(mapProfile) };
    }
  );
};
