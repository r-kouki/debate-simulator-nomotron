import { JudgeOutputSchema, TurnScoreSchema } from "@debate/contracts";
import { openRouterChat, type ChatMessage } from "../services/openRouterClient";
import { getEnv } from "../utils/env";

export const judgeAgent = async (input: {
  topic: string;
  participants: Array<{ id: string; name: string; stance: string }>;
  transcript: Array<{ roleLabel: string; content: string }>;
}) => {
  const env = getEnv();
  const system: ChatMessage = {
    role: "system",
    content:
      "You are a debate judge. Output ONLY strict JSON per schema. No reasoning or extra text."
  };

  const user: ChatMessage = {
    role: "user",
    content: JSON.stringify({
      topic: input.topic,
      participants: input.participants,
      transcript: input.transcript.slice(-12),
      outputSchema: JudgeOutputSchema.toString()
    })
  };

  const response = await openRouterChat({
    messages: [system, user],
    modelOverride: env.openRouterModel,
    temperature: 0.3
  });

  try {
    const parsed = JudgeOutputSchema.parse(JSON.parse(response.content));
    return parsed;
  } catch {
    const fallbackScores = TurnScoreSchema.parse({
      clarity: 70,
      logic: 70,
      evidence: 68,
      rebuttal: 65,
      civility: 75,
      relevance: 72
    });
    return {
      winnerParticipantId: input.participants[0]?.id ?? null,
      scores: Object.fromEntries(input.participants.map((p) => [p.id, fallbackScores])),
      explanation: "Fallback judge result due to invalid model output.",
      highlights: ["Consistent arguments", "Clear structure"],
      fallacies: ["Overgeneralization"],
      achievements: []
    };
  }
};
