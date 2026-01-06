import type { FastifyInstance } from "fastify";
import { HealthResponseSchema } from "@debate/contracts";
import { getEnv } from "../utils/env";

export const registerHealthRoutes = (app: FastifyInstance) => {
  const env = getEnv();
  app.get(
    "/health",
    {
      schema: {
        response: {
          200: HealthResponseSchema
        }
      }
    },
    async () => {
      return {
        ok: true,
        version: env.openRouterModel,
        time: new Date().toISOString()
      };
    }
  );
};
