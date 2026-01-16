import type { FastifyInstance } from "fastify";
import { z } from "zod";
import { ZodTypeProvider } from "fastify-type-provider-zod";
import {
  CreateDebateRequestSchema,
  CreateDebateResponseSchema,
  DebateGetResponseSchema,
  CreateTurnRequestSchema,
  CreateTurnResponseSchema,
  RunDebateRequestSchema,
  RunDebateResponseSchema,
  ScoreDebateResponseSchema
} from "@debate/contracts";
import { prisma } from "../services/db";
import { createDebate, createTurn, runAiVsAiDebate, cancelDebateRun } from "../services/debates";
import { debaterAgent } from "../agents/debaterAgent";
import { researchAgent } from "../agents/researchAgent";
import { scoreTurn, aggregateScores } from "../services/scoring";
import { judgeAgent } from "../agents/judgeAgent";
import { eventBus } from "../services/eventBus";
import { updatePlayerAfterMatch } from "../services/gamification";

// Frontend compatibility schema - accepts the format sent by the React frontend
const FrontendDebateRequestSchema = z.object({
  topicId: z.string().optional(),
  topicTitle: z.string().min(1).max(200),
  stance: z.enum(["pro", "con", "neutral"]),
  mode: z.enum(["human-vs-ai", "cops-vs-ai", "ai-vs-ai"]),
  difficulty: z.enum(["easy", "medium", "hard"]).optional(),
  participants: z.array(z.object({
    name: z.string(),
    type: z.enum(["human", "ai", "judge"])
  })),
  timerSeconds: z.number().int().min(30).max(900).optional()
});

// Transform frontend format to backend format
const transformFrontendRequest = (frontendReq: z.infer<typeof FrontendDebateRequestSchema>) => {
  const modeMap: Record<string, "HUMAN_VS_AI" | "COPS_VS_AI" | "AI_VS_AI" | "HUMAN_VS_HUMAN"> = {
    "human-vs-ai": "HUMAN_VS_AI",
    "cops-vs-ai": "COPS_VS_AI",
    "ai-vs-ai": "AI_VS_AI"
  };

  const stanceMap: Record<string, "PRO" | "CON"> = {
    "pro": "PRO",
    "con": "CON",
    "neutral": "PRO" // Default to PRO if neutral
  };

  // Assign stances to participants - humans get the user's stance, AI gets opposite
  const userStance = stanceMap[frontendReq.stance] || "PRO";
  const aiStance = userStance === "PRO" ? "CON" : "PRO";

  // For AI vs AI, alternate stances between participants
  const isAiVsAi = frontendReq.mode === "ai-vs-ai";
  let aiIndex = 0;

  return {
    mode: modeMap[frontendReq.mode] || "HUMAN_VS_AI",
    topic: frontendReq.topicTitle,
    rounds: 3, // Default rounds
    turnSeconds: frontendReq.timerSeconds || 120,
    participants: frontendReq.participants.map((p, index) => {
      if (p.type === "ai") {
        // For AI vs AI, first AI is PRO, second is CON
        const stance = isAiVsAi ? (aiIndex++ === 0 ? "PRO" : "CON") : aiStance;
        return { type: "AI" as const, name: p.name, stance };
      }
      return { type: "HUMAN" as const, name: p.name, stance: userStance };
    })
  };
};

// Combined schema that accepts either format
const CombinedDebateRequestSchema = z.union([
  CreateDebateRequestSchema,
  FrontendDebateRequestSchema
]);

// Frontend turn request schema - frontend sends {message, role} instead of {participantId, content}
const FrontendTurnRequestSchema = z.object({
  debateId: z.string().optional(), // Sometimes included in body
  message: z.string().min(1).max(4000),
  role: z.string()
});

// Combined turn request schema
const CombinedTurnRequestSchema = z.union([
  CreateTurnRequestSchema,
  FrontendTurnRequestSchema
]);

export const registerDebateRoutes = (app: FastifyInstance) => {
  const api = app.withTypeProvider<ZodTypeProvider>();
  const ErrorSchema = z.object({ error: z.string() });

  api.post(
    "/debates",
    {
      schema: {
        body: CombinedDebateRequestSchema,
        response: { 200: CreateDebateResponseSchema }
      }
    },
    async (request) => {
      const playerId = request.headers["x-player-id"] as string | undefined;

      // Detect and transform frontend format if necessary
      let body = request.body as z.infer<typeof CombinedDebateRequestSchema>;

      // Check if this is frontend format (has topicTitle instead of topic)
      if ("topicTitle" in body && typeof body.topicTitle === "string") {
        body = transformFrontendRequest(body as z.infer<typeof FrontendDebateRequestSchema>);
      }

      const debate = await createDebate({ ...body as z.infer<typeof CreateDebateRequestSchema>, playerId });
      if (debate.mode === "AI_VS_AI") {
        runAiVsAiDebate(debate.id).catch((error) => {
          request.log.error(error, "AI_VS_AI run failed");
        });
      }
      return {
        debateId: debate.id,
        debate: {
          id: debate.id,
          mode: debate.mode,
          topic: debate.topic,
          rounds: debate.rounds,
          turnSeconds: debate.turnSeconds,
          status: debate.status,
          participants: debate.participants.map((participant) => ({
            id: participant.id,
            type: participant.type,
            name: participant.name,
            stance: participant.stance,
            roleLabel: participant.roleLabel
          })),
          createdAt: debate.createdAt.toISOString(),
          updatedAt: debate.updatedAt.toISOString()
        }
      };
    }
  );

  api.get(
    "/debates/:id",
    {
      schema: {
        response: { 200: DebateGetResponseSchema, 404: ErrorSchema }
      }
    },
    async (request, reply) => {
      const id = (request.params as { id: string }).id;
      const debate = await prisma.debate.findUnique({
        where: { id },
        include: { participants: true, turns: { include: { scores: true } } }
      });
      if (!debate) {
        reply.code(404);
        return { error: "Debate not found" };
      }
      const liveScores = debate.turns.reduce<Record<string, ReturnType<typeof scoreTurn>>>(
        (acc, turn) => {
          const score = turn.scores[0];
          if (score) {
            acc[turn.id] = scoreTurn(turn.content);
          }
          return acc;
        },
        {}
      );
      return {
        debate: {
          id: debate.id,
          mode: debate.mode,
          topic: debate.topic,
          rounds: debate.rounds,
          turnSeconds: debate.turnSeconds,
          status: debate.status,
          participants: debate.participants.map((participant) => ({
            id: participant.id,
            type: participant.type,
            name: participant.name,
            stance: participant.stance,
            roleLabel: participant.roleLabel
          })),
          createdAt: debate.createdAt.toISOString(),
          updatedAt: debate.updatedAt.toISOString()
        },
        turns: debate.turns.map((turn) => ({
          id: turn.id,
          debateId: turn.debateId,
          participantId: turn.participantId,
          roleLabel: turn.roleLabel,
          content: turn.content,
          createdAt: turn.createdAt.toISOString()
        })),
        liveScores
      };
    }
  );

  api.post(
    "/debates/:id/turns",
    {
      schema: {
        body: CombinedTurnRequestSchema,
        response: { 200: CreateTurnResponseSchema, 404: ErrorSchema },
        config: {
          rateLimit: { max: 20, timeWindow: "1 minute" }
        }
      }
    },
    async (request, reply) => {
      const debateId = (request.params as { id: string }).id;
      const debate = await prisma.debate.findUnique({
        where: { id: debateId },
        include: { participants: true, turns: true }
      });
      if (!debate) {
        reply.code(404);
        return { error: "Debate not found" };
      }

      // Detect and transform frontend format if necessary
      let participantId: string;
      let content: string;

      const body = request.body as z.infer<typeof CombinedTurnRequestSchema>;

      if ("message" in body && typeof body.message === "string") {
        // Frontend format - lookup participant by role/name
        const frontendBody = body as z.infer<typeof FrontendTurnRequestSchema>;
        content = frontendBody.message;

        // Find participant by name/role
        const participant = debate.participants.find(
          (p) => p.name === frontendBody.role || p.roleLabel === frontendBody.role
        ) || debate.participants.find((p) => p.type === "HUMAN");

        if (!participant) {
          reply.code(400);
          return { error: "Could not find participant for role: " + frontendBody.role };
        }
        participantId = participant.id;
      } else {
        // Backend format
        const backendBody = body as z.infer<typeof CreateTurnRequestSchema>;
        participantId = backendBody.participantId;
        content = backendBody.content;
      }

      const { turn, scores } = await createTurn({ debateId, participantId, content });

      const aiParticipant = debate.participants.find((p) => p.type === "AI");
      const aiTurns = [] as Array<typeof turn>;
      const events: string[] = [];

      if (aiParticipant && debate.mode !== "HUMAN_VS_HUMAN") {
        const research = await researchAgent({
          topic: debate.topic,
          stance: aiParticipant.stance === "PRO" ? "PRO" : "CON",
          opponentRecentClaims: [content],
          difficulty: "medium"
        });
        const debater = await debaterAgent({
          topic: debate.topic,
          stance: aiParticipant.stance === "PRO" ? "PRO" : "CON",
          transcript: debate.turns.map((t) => t.content).concat(content),
          researchBriefing: JSON.stringify(research),
          difficulty: "medium",
          style: "polite"
        });
        const aiTurn = await createTurn({
          debateId,
          participantId: aiParticipant.id,
          content: debater.message
        });
        aiTurns.push(aiTurn.turn);
        events.push("ai.responded");
      }

      return {
        acceptedTurn: {
          id: turn.id,
          debateId: turn.debateId,
          participantId: turn.participantId,
          roleLabel: turn.roleLabel,
          content: turn.content,
          createdAt: turn.createdAt.toISOString()
        },
        aiTurns: aiTurns.length
          ? aiTurns.map((ai) => ({
            id: ai.id,
            debateId: ai.debateId,
            participantId: ai.participantId,
            roleLabel: ai.roleLabel,
            content: ai.content,
            createdAt: ai.createdAt.toISOString()
          }))
          : undefined,
        updatedScores: scores,
        events
      };
    }
  );

  api.post(
    "/debates/:id/run",
    {
      schema: {
        body: RunDebateRequestSchema,
        response: { 200: RunDebateResponseSchema }
      }
    },
    async (request) => {
      const debateId = (request.params as { id: string }).id;
      await runAiVsAiDebate(debateId, request.body.autoRounds);
      return { started: true };
    }
  );

  api.post(
    "/debates/:id/cancel",
    async (request) => {
      const debateId = (request.params as { id: string }).id;
      cancelDebateRun(debateId);
      return { cancelled: true };
    }
  );

  api.post(
    "/debates/:id/score",
    {
      schema: {
        response: { 200: ScoreDebateResponseSchema, 404: ErrorSchema },
        config: {
          rateLimit: { max: 6, timeWindow: "1 minute" }
        }
      }
    },
    async (request, reply) => {
      const debateId = (request.params as { id: string }).id;
      const playerId = request.headers["x-player-id"] as string | undefined;
      const debate = await prisma.debate.findUnique({
        where: { id: debateId },
        include: { participants: true, turns: { include: { scores: true } } }
      });
      if (!debate) {
        reply.code(404);
        return { error: "Debate not found" };
      }
      const transcript = debate.turns.map((turn) => ({
        roleLabel: turn.roleLabel,
        content: turn.content
      }));
      const judge = await judgeAgent({
        topic: debate.topic,
        participants: debate.participants.map((p) => ({
          id: p.id,
          name: p.name,
          stance: p.stance
        })),
        transcript
      });

      const scoreList = debate.turns.map((turn) => scoreTurn(turn.content));
      const aggregate = aggregateScores(scoreList);
      const finalScore = Math.round(
        (aggregate.clarity + aggregate.logic + aggregate.evidence + aggregate.rebuttal + aggregate.civility + aggregate.relevance) /
        6
      );

      await prisma.finalScore.upsert({
        where: { debateId },
        update: {
          overallScore: finalScore,
          winnerParticipantId: judge.winnerParticipantId,
          explanation: judge.explanation,
          highlights: JSON.stringify(judge.highlights),
          fallacies: JSON.stringify(judge.fallacies)
        },
        create: {
          debateId,
          overallScore: finalScore,
          winnerParticipantId: judge.winnerParticipantId,
          explanation: judge.explanation,
          highlights: JSON.stringify(judge.highlights),
          fallacies: JSON.stringify(judge.fallacies)
        }
      });

      if (playerId) {
        await updatePlayerAfterMatch({
          playerId,
          topic: debate.topic,
          mode: debate.mode,
          score: finalScore,
          didWin: debate.participants.some((p) => p.id === judge.winnerParticipantId && p.playerId === playerId)
        });
      }

      await prisma.debate.update({ where: { id: debateId }, data: { status: "ENDED" } });

      eventBus.emit(debateId, "judge.final", { judge });
      eventBus.emit(debateId, "debate.ended", { status: "ENDED" });

      return {
        finalScore,
        breakdown: aggregate,
        winner: judge.winnerParticipantId,
        judgeReport: {
          explanation: judge.explanation,
          highlights: judge.highlights,
          fallacies: judge.fallacies
        },
        achievementsUnlocked: judge.achievements
      };
    }
  );

  api.get(
    "/debates/:id/stream",
    async (request, reply) => {
      const debateId = (request.params as { id: string }).id;
      reply.raw.writeHead(200, {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
        "X-Accel-Buffering": "no"
      });
      reply.raw.write("event: connected\ndata: {}\n\n");
      eventBus.subscribe(debateId, reply.raw);
      request.raw.on("close", () => {
        eventBus.unsubscribe(debateId, reply.raw);
      });
      reply.hijack();
      return reply;
    }
  );
};
