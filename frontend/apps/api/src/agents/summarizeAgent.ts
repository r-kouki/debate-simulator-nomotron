/**
 * Summarize Agent - Generates concise summaries of text
 */

import type { AgentHandler } from "./registry";
import { openRouterChat, type ChatMessage } from "../services/openRouterClient";
import { z } from "zod";

const SummarizeInputSchema = z.object({
  text: z.string().min(1),
  maxLength: z.number().optional(),
  style: z.enum(["brief", "detailed", "bullet"]).optional()
});

export const summarizeAgentHandler: AgentHandler = async (req) => {
  try {
    const parsed = SummarizeInputSchema.safeParse(req.input);
    if (!parsed.success) {
      return {
        ok: false,
        error: {
          code: "INVALID_INPUT",
          message: `Invalid input: ${parsed.error.message}`
        }
      };
    }

    const { text, maxLength = 200, style = "brief" } = parsed.data;

    const styleInstructions: Record<string, string> = {
      brief: "Provide a very brief, one-paragraph summary.",
      detailed: "Provide a comprehensive summary with key points.",
      bullet: "Provide a summary as bullet points of the main ideas."
    };

    const systemPrompt = `You are a summarization assistant. ${styleInstructions[style]} Keep it under ${maxLength} words.`;
    const userPrompt = `Summarize the following text:\n\n${text}`;

    const messages: ChatMessage[] = [
      { role: "system", content: systemPrompt },
      { role: "user", content: userPrompt }
    ];

    const response = await openRouterChat({
      messages,
      temperature: 0.3
    });

    const summary = response.content.trim();
    if (!summary) {
      return {
        ok: false,
        error: {
          code: "EMPTY_RESPONSE",
          message: "Generated summary was empty"
        }
      };
    }

    return {
      ok: true,
      data: {
        summary,
        style,
        originalLength: text.length,
        summaryLength: summary.length
      }
    };
  } catch (error) {
    return {
      ok: false,
      error: {
        code: "INTERNAL_ERROR",
        message: error instanceof Error ? error.message : "Unknown error"
      }
    };
  }
};
