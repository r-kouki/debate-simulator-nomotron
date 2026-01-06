import { DebaterOutputSchema } from "@debate/contracts";
import { openRouterChat, type ChatMessage } from "../services/openRouterClient";
import { getEnv } from "../utils/env";

export const debaterAgent = async (input: {
  topic: string;
  stance: "PRO" | "CON";
  transcript: string[];
  researchBriefing: string;
  difficulty: "easy" | "medium" | "hard";
  style: "polite" | "aggressive" | "socratic";
}) => {
  const env = getEnv();
  const system: ChatMessage = {
    role: "system",
    content:
      "You are a debate AI. Respond with a single JSON object with a 'message' string. No extra text."
  };

  const user: ChatMessage = {
    role: "user",
    content: JSON.stringify({
      topic: input.topic,
      stance: input.stance,
      transcript: input.transcript.slice(-6),
      research: input.researchBriefing,
      difficulty: input.difficulty,
      style: input.style,
      outputSchema: DebaterOutputSchema.toString()
    })
  };

  const response = await openRouterChat({
    messages: [system, user],
    modelOverride: env.openRouterModel,
    temperature: 0.6
  });

  try {
    const parsed = DebaterOutputSchema.parse(JSON.parse(response.content));
    return parsed;
  } catch {
    return { message: response.content.trim() || "Acknowledged." };
  }
};
