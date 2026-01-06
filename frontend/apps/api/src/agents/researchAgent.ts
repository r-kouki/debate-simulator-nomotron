import { z } from "zod";
import { ResearchOutputSchema } from "@debate/contracts";
import { openRouterChat, type ChatMessage, type ToolDefinition } from "../services/openRouterClient";
import { buildFallbackBriefing, searchWikipedia } from "../services/researchTools";
import { getEnv } from "../utils/env";

const toolDefinitions: ToolDefinition[] = [
  {
    type: "function",
    function: {
      name: "search_web",
      description: "Search the web for recent sources about a topic and return citations.",
      parameters: {
        type: "object",
        properties: {
          query: { type: "string" }
        },
        required: ["query"]
      }
    }
  }
];

const toolCommandSchema = z.object({
  tool: z.string(),
  arguments: z.record(z.unknown())
});

const parseToolCommand = (content: string) => {
  try {
    const parsed = JSON.parse(content);
    const result = toolCommandSchema.safeParse(parsed);
    if (!result.success) {
      return null;
    }
    return result.data;
  } catch {
    return null;
  }
};

const executeTool = async (name: string, args: Record<string, unknown>) => {
  if (name === "search_web") {
    const query = typeof args.query === "string" ? args.query : "";
    const sources = await searchWikipedia(query);
    return { sources };
  }
  return { error: `Unknown tool ${name}` };
};

export const researchAgent = async (input: {
  topic: string;
  stance?: "PRO" | "CON" | null;
  opponentRecentClaims: string[];
  difficulty: "easy" | "medium" | "hard";
}) => {
  const env = getEnv();
  const modelOverride = env.openRouterUseWeb
    ? `${env.openRouterModel}:online`
    : env.openRouterModel;

  const system: ChatMessage = {
    role: "system",
    content:
      "You are a research agent. Use tools when available. Output ONLY valid JSON matching the schema. No extra commentary."
  };

  const user: ChatMessage = {
    role: "user",
    content: JSON.stringify({
      task: "Research debate topic with counterarguments.",
      topic: input.topic,
      stance: input.stance,
      opponentRecentClaims: input.opponentRecentClaims,
      difficulty: input.difficulty,
      outputSchema: ResearchOutputSchema.toString()
    })
  };

  const messages: ChatMessage[] = [system, user];

  for (let i = 0; i < 3; i += 1) {
    const response = await openRouterChat({
      messages,
      tools: toolDefinitions,
      toolChoice: "auto",
      modelOverride,
      temperature: 0.2
    });

    if (response.toolCalls && response.toolCalls.length > 0) {
      messages.push({ role: "assistant", content: response.content || "", tool_calls: response.toolCalls });
      for (const call of response.toolCalls) {
        let args: Record<string, unknown> = {};
        try {
          args = call.function.arguments ? JSON.parse(call.function.arguments) : {};
        } catch {
          args = {};
        }
        const result = await executeTool(call.function.name, args);
        messages.push({
          role: "tool",
          content: JSON.stringify(result),
          tool_call_id: call.id
        });
      }
      continue;
    }

    const manualTool = parseToolCommand(response.content);
    if (manualTool) {
      const result = await executeTool(manualTool.tool, manualTool.arguments);
      messages.push({ role: "assistant", content: response.content });
      messages.push({ role: "tool", content: JSON.stringify(result) });
      continue;
    }

    try {
      const parsed = ResearchOutputSchema.safeParse(JSON.parse(response.content));
      if (parsed.success) {
        return parsed.data;
      }
    } catch {
      // fall through to fallback
    }
    break;
  }

  const sources = await searchWikipedia(input.topic);
  const fallback = buildFallbackBriefing(input.topic, input.stance);
  return ResearchOutputSchema.parse({
    ...fallback,
    sources
  });
};
