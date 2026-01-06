/**
 * Agent Routes - Unified endpoint for all registered agents
 *
 * POST /api/agents/:agentId
 * Body: { input: string, context?: object }
 * Response: { ok: true, data: <agent-specific> } | { ok: false, error: { code, message } }
 */

import type { FastifyInstance } from "fastify";
import { z } from "zod";
import type { ZodTypeProvider } from "fastify-type-provider-zod";
import { AgentRequestSchema, AgentResponseSchema } from "@debate/contracts";
import { getAgent, getRegisteredAgentIds, hasAgent } from "../agents/registry";

// Register all agents
import { registerAgent } from "../agents/registry";
import { themeAgentHandler } from "../agents/themeAgent";
import { summarizeAgentHandler } from "../agents/summarizeAgent";

// Register the theme agent
registerAgent("theme", themeAgentHandler);
registerAgent("summarize", summarizeAgentHandler);

export const registerAgentRoutes = (app: FastifyInstance) => {
  const api = app.withTypeProvider<ZodTypeProvider>();

  // List available agents
  api.get(
    "/api/agents",
    {
      schema: {
        response: {
          200: z.object({
            agents: z.array(z.string())
          })
        }
      }
    },
    async () => {
      return { agents: getRegisteredAgentIds() };
    }
  );

  // Execute agent
  api.post(
    "/api/agents/:agentId",
    {
      schema: {
        params: z.object({
          agentId: z.string().min(1).max(50)
        }),
        body: AgentRequestSchema,
        response: {
          200: AgentResponseSchema,
          404: AgentResponseSchema
        }
      }
    },
    async (request, reply) => {
      const { agentId } = request.params;

      if (!hasAgent(agentId)) {
        return reply.status(404).send({
          ok: false,
          error: {
            code: "AGENT_NOT_FOUND",
            message: `Agent "${agentId}" is not registered`
          }
        });
      }

      const handler = getAgent(agentId)!;

      try {
        const result = await handler(request.body);
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error";
        return {
          ok: false,
          error: {
            code: "SERVER_ERROR",
            message
          }
        };
      }
    }
  );
};
