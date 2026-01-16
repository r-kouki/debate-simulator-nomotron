import { getEnv } from "../utils/env";

export type ChatRole = "system" | "user" | "assistant" | "tool";

export type ChatMessage = {
  role: ChatRole;
  content: string;
  name?: string;
  tool_call_id?: string;
  tool_calls?: ToolCall[];
};

export type ToolDefinition = {
  type: "function";
  function: {
    name: string;
    description: string;
    parameters: Record<string, unknown>;
  };
};

export type ToolCall = {
  id: string;
  type: "function";
  function: {
    name: string;
    arguments: string;
  };
};

export type ChatCompletionResult = {
  content: string;
  toolCalls?: ToolCall[];
};

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const retry = async <T>(fn: () => Promise<T>, retries = 3): Promise<T> => {
  let attempt = 0;
  let lastError: unknown;
  while (attempt < retries) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      attempt += 1;
      await sleep(300 * attempt);
    }
  }
  throw lastError instanceof Error ? lastError : new Error("OpenRouter request failed");
};

export const openRouterChat = async (payload: {
  messages: ChatMessage[];
  tools?: ToolDefinition[];
  toolChoice?: "auto" | "none";
  modelOverride?: string;
  temperature?: number;
  maxTokens?: number;
}): Promise<ChatCompletionResult> => {
  const env = getEnv();
  const model = payload.modelOverride || env.openRouterModel;
  const apiKey = env.openRouterApiKey;
  if (!apiKey) {
    throw new Error("OPENROUTER_API_KEY is required for LLM calls");
  }

  const body = {
    model,
    messages: payload.messages,
    tools: payload.tools,
    tool_choice: payload.toolChoice ?? "auto",
    temperature: payload.temperature ?? 0.4,
    max_tokens: payload.maxTokens ?? 1024
  };

  return retry(async () => {
    const response = await fetch(OPENROUTER_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
        ...(env.openRouterSiteUrl ? { "HTTP-Referer": env.openRouterSiteUrl } : {}),
        ...(env.openRouterAppName ? { "X-Title": env.openRouterAppName } : {})
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `OpenRouter error ${response.status}`);
    }

    const json = (await response.json()) as {
      choices: Array<{ message: { content: string; tool_calls?: ToolCall[] } }>;
    };

    const message = json.choices[0]?.message;
    return {
      content: message?.content ?? "",
      toolCalls: message?.tool_calls
    };
  });
};
