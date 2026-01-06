import type { FastifyInstance } from "fastify";
import { z } from "zod";
import { ZodTypeProvider } from "@fastify/type-provider-zod";
import {
  TopicSearchQuerySchema,
  TopicSearchResponseSchema,
  TopicDetailSchema,
  TopicBriefRequestSchema,
  TopicBriefResponseSchema
} from "@debate/contracts";
import { searchTopics, getTopicDetail, cacheTopicBrief } from "../services/topics";
import { researchAgent } from "../agents/researchAgent";
import { searchWikipedia } from "../services/researchTools";

export const registerTopicRoutes = (app: FastifyInstance) => {
  const api = app.withTypeProvider<ZodTypeProvider>();
  const ErrorSchema = z.object({ error: z.string() });

  api.get(
    "/topics/search",
    {
      schema: {
        querystring: TopicSearchQuerySchema,
        response: { 200: TopicSearchResponseSchema }
      }
    },
    async (request) => {
      const results = await searchTopics(request.query.q);
      return { results };
    }
  );

  api.get(
    "/topics/:id",
    {
      schema: {
        response: { 200: TopicDetailSchema, 404: ErrorSchema }
      }
    },
    async (request, reply) => {
      const id = (request.params as { id: string }).id;
      const detail = await getTopicDetail(id);
      if (!detail) {
        reply.code(404);
        return { error: "Topic not found" };
      }
      return detail;
    }
  );

  api.post(
    "/topics/brief",
    {
      schema: {
        body: TopicBriefRequestSchema,
        response: { 200: TopicBriefResponseSchema },
        config: {
          rateLimit: { max: 10, timeWindow: "1 minute" }
        }
      }
    },
    async (request) => {
      const { topic, stance, depth } = request.body;
      const briefing = await researchAgent({
        topic,
        stance,
        opponentRecentClaims: [],
        difficulty: depth === "deep" ? "hard" : "medium"
      });

      const sources = briefing.sources.length > 0 ? briefing.sources : await searchWikipedia(topic);

      await cacheTopicBrief(topic, briefing.keyFacts[0] ?? topic, {
        id: topic.toLowerCase().replace(/\s+/g, "-"),
        title: topic,
        category: "Research",
        summary: briefing.keyFacts[0] ?? topic,
        description: briefing.keyFacts.join(" "),
        keyPoints: briefing.keyFacts,
        pros: briefing.proArguments,
        cons: briefing.conArguments,
        fallacies: [],
        sources
      });

      return {
        topic,
        briefing: {
          keyFacts: briefing.keyFacts,
          proArguments: briefing.proArguments,
          conArguments: briefing.conArguments,
          counterArguments: briefing.counterArguments,
          questions: briefing.questions
        },
        sources
      };
    }
  );
};
