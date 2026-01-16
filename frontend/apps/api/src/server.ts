import Fastify from "fastify";
import cors from "@fastify/cors";
import rateLimit from "@fastify/rate-limit";
import swagger from "@fastify/swagger";
import swaggerUi from "@fastify/swagger-ui";
import {
  validatorCompiler,
  serializerCompiler,
  jsonSchemaTransform
} from "fastify-type-provider-zod";
import { randomUUID } from "node:crypto";
import { getEnv } from "./utils/env";
import { registerHealthRoutes } from "./routes/health";
import { registerTopicRoutes } from "./routes/topics";
import { registerDebateRoutes } from "./routes/debates";
import { registerProfileRoutes } from "./routes/profile";
import { registerAuthRoutes } from "./routes/auth";

export const buildServer = () => {
  const env = getEnv();
  const app = Fastify({
    logger: {
      level: "info"
    },
    genReqId: () => randomUUID()
  });

  app.setValidatorCompiler(validatorCompiler);
  app.setSerializerCompiler(serializerCompiler);

  app.register(cors, {
    origin: env.frontendOrigin,
    credentials: true
  });

  app.register(rateLimit, {
    global: false
  });

  app.addHook("onRequest", async (request, reply) => {
    reply.header("x-request-id", request.id);
  });

  app.register(swagger, {
    openapi: {
      info: {
        title: "Debate Simulator API",
        version: "0.1.0"
      }
    },
    transform: jsonSchemaTransform
  });

  app.register(swaggerUi, {
    routePrefix: "/docs"
  });

  registerHealthRoutes(app);
  registerTopicRoutes(app);
  registerDebateRoutes(app);
  registerProfileRoutes(app);
  registerAuthRoutes(app);

  return app;
};
