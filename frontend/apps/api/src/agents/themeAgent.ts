/**
 * Theme Agent - Generates validated UI theme tokens from natural language
 *
 * Security:
 * - Only allows fonts from a strict allowlist
 * - Validates all colors as HEX or rgb()/rgba()
 * - Clamps numeric values to safe ranges
 * - No arbitrary CSS injection possible
 */

import { AiThemeSchema, type AgentRequest, type AgentResponse, type AiTheme } from "@debate/contracts";
import { openRouterChat, type ChatMessage } from "../services/openRouterClient";
import { getEnv } from "../utils/env";
import type { AgentHandler } from "./registry";

const SYSTEM_PROMPT = `You are a UI theme generator. You MUST respond with ONLY a valid JSON object, no markdown, no explanation.

Generate a theme based on the user's description. Output this exact JSON structure:

{
  "name": "Theme Name (max 50 chars)",
  "tokens": {
    "fontFamily": "Tahoma",
    "fontSizeBasePx": 14,
    "bg": "#RRGGBB",
    "panel": "#RRGGBB",
    "text": "#RRGGBB",
    "mutedText": "#RRGGBB",
    "primary": "#RRGGBB",
    "primaryText": "#RRGGBB",
    "border": "#RRGGBB",
    "radiusPx": 0,
    "shadow": "2px 2px 0 rgba(0,0,0,0.35)"
  }
}

RULES:
- fontFamily MUST be one of: "Tahoma", "Verdana", "Arial", "Trebuchet MS", "Courier New"
- fontSizeBasePx: 12-20 (integer)
- All colors MUST be valid HEX (#RGB or #RRGGBB) or rgb()/rgba()
- radiusPx: 0-16 (integer, 0 for sharp corners like Win98)
- shadow: simple box-shadow like "2px 2px 0 rgba(0,0,0,0.35)"
- Return ONLY the JSON object, nothing else`;

/**
 * Extract first JSON object from potentially messy LLM output
 */
const extractJson = (text: string): string => {
  const start = text.indexOf("{");
  if (start === -1) throw new Error("No JSON object found in response");

  let depth = 0;
  let end = -1;

  for (let i = start; i < text.length; i++) {
    if (text[i] === "{") depth++;
    if (text[i] === "}") depth--;
    if (depth === 0) {
      end = i + 1;
      break;
    }
  }

  if (end === -1) throw new Error("Malformed JSON in response");
  return text.slice(start, end);
};

export const themeAgentHandler: AgentHandler = async (request: AgentRequest): Promise<AgentResponse> => {
  const env = getEnv();

  if (!request.input?.trim()) {
    return {
      ok: false,
      error: { code: "BAD_REQUEST", message: "Input is required" }
    };
  }

  const userPrompt = request.input.trim();

  // Build context hint if provided
  const contextHint = request.context
    ? `\nContext: ${JSON.stringify(request.context)}`
    : "";

  const messages: ChatMessage[] = [
    { role: "system", content: SYSTEM_PROMPT },
    { role: "user", content: `Create a theme for: "${userPrompt}"${contextHint}` }
  ];

  let rawResponse: string;

  try {
    const result = await openRouterChat({
      messages,
      modelOverride: env.openRouterModel,
      temperature: 0.7
    });
    rawResponse = result.content;
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown LLM error";
    return {
      ok: false,
      error: { code: "LLM_ERROR", message }
    };
  }

  // Parse and validate
  let theme: AiTheme;
  try {
    const jsonStr = extractJson(rawResponse);
    const parsed = JSON.parse(jsonStr);
    theme = AiThemeSchema.parse(parsed);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Invalid theme format";
    return {
      ok: false,
      error: { code: "VALIDATION_FAILED", message: `Theme validation failed: ${message}` }
    };
  }

  // Add metadata
  theme.meta = {
    prompt: userPrompt,
    model: env.openRouterModel,
    createdAt: new Date().toISOString()
  };

  return {
    ok: true,
    data: theme
  };
};
