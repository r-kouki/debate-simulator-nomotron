import { randomUUID } from "node:crypto";
import type { DebateMode } from "@debate/contracts";
import { prisma } from "./db";
import { eventBus } from "./eventBus";
import { researchAgent } from "../agents/researchAgent";
import { debaterAgent } from "../agents/debaterAgent";
import { scoreTurn } from "./scoring";

const runningControllers = new Map<string, AbortController>();

const buildRoleLabel = (index: number, type: string) => {
  if (type === "JUDGE") {
    return "Judge";
  }
  return `${type === "AI" ? "AI" : "Human"}${index}`;
};

export const createDebate = async (input: {
  mode: DebateMode;
  topic: string;
  rounds: number;
  turnSeconds?: number;
  participants: Array<{ type: "HUMAN" | "AI"; name: string; stance: "PRO" | "CON" }>;
  playerId?: string;
}) => {
  const debate = await prisma.debate.create({
    data: {
      mode: input.mode,
      topic: input.topic,
      rounds: input.rounds,
      turnSeconds: input.turnSeconds,
      status: "CREATED",
      participants: {
        create: input.participants.map((participant, index) => ({
          type: participant.type,
          name: participant.name,
          stance: participant.stance,
          roleLabel: buildRoleLabel(index + 1, participant.type),
          playerId: participant.type === "HUMAN" ? input.playerId : undefined
        }))
      }
    },
    include: { participants: true }
  });

  eventBus.emit(debate.id, "debate.started", { debateId: debate.id, mode: debate.mode });
  return debate;
};

export const createTurn = async (input: {
  debateId: string;
  participantId: string;
  content: string;
}) => {
  const participant = await prisma.participant.findUnique({ where: { id: input.participantId } });
  if (!participant) {
    throw new Error("Participant not found");
  }
  const turn = await prisma.turn.create({
    data: {
      debateId: input.debateId,
      participantId: input.participantId,
      roleLabel: participant.roleLabel,
      content: input.content
    }
  });
  const scores = scoreTurn(input.content);
  await prisma.turnScore.create({
    data: {
      turnId: turn.id,
      clarity: scores.clarity,
      logic: scores.logic,
      evidence: scores.evidence,
      rebuttal: scores.rebuttal,
      civility: scores.civility,
      relevance: scores.relevance
    }
  });

  eventBus.emit(input.debateId, "turn.created", { turn });
  eventBus.emit(input.debateId, "scores.updated", { turnId: turn.id, scores });
  return { turn, scores };
};

export const runAiVsAiDebate = async (debateId: string, autoRounds?: number) => {
  const debate = await prisma.debate.findUnique({
    where: { id: debateId },
    include: { participants: true }
  });
  if (!debate) {
    throw new Error("Debate not found");
  }
  if (debate.status === "RUNNING") {
    return;
  }
  const controller = new AbortController();
  runningControllers.set(debateId, controller);

  await prisma.debate.update({ where: { id: debateId }, data: { status: "RUNNING" } });
  const rounds = autoRounds ?? debate.rounds;
  const aiParticipants = debate.participants.filter((p) => p.type === "AI");

  for (let round = 0; round < rounds; round += 1) {
    for (const ai of aiParticipants) {
      if (controller.signal.aborted) {
        await prisma.debate.update({ where: { id: debateId }, data: { status: "CANCELLED" } });
        eventBus.emit(debateId, "debate.ended", { status: "CANCELLED" });
        return;
      }
      const research = await researchAgent({
        topic: debate.topic,
        stance: ai.stance === "PRO" ? "PRO" : "CON",
        opponentRecentClaims: [],
        difficulty: "medium"
      });
      const debater = await debaterAgent({
        topic: debate.topic,
        stance: ai.stance === "PRO" ? "PRO" : "CON",
        transcript: [],
        researchBriefing: JSON.stringify(research),
        difficulty: "medium",
        style: "socratic"
      });
      await createTurn({
        debateId: debate.id,
        participantId: ai.id,
        content: debater.message
      });
    }
  }

  await prisma.debate.update({ where: { id: debateId }, data: { status: "ENDED" } });
  eventBus.emit(debateId, "debate.ended", { status: "ENDED" });
  runningControllers.delete(debateId);
};

export const cancelDebateRun = (debateId: string) => {
  const controller = runningControllers.get(debateId);
  if (controller) {
    controller.abort();
    runningControllers.delete(debateId);
  }
};
