import type { TopicDetail, TopicSummary } from "@debate/contracts";
import { prisma } from "./db";

const staticTopics: TopicDetail[] = [
  {
    id: "ai-education",
    title: "AI in Education",
    category: "Technology",
    summary: "Should AI tutors be integrated into classrooms?",
    description: "AI tools can personalize learning but raise concerns about privacy and equity.",
    keyPoints: ["Personalization", "Teacher workload", "Data privacy"],
    pros: ["Adaptive learning", "Accessibility", "Scalable tutoring"],
    cons: ["Data privacy", "Bias risk", "Dependency on tech"],
    fallacies: ["Appeal to novelty", "False dilemma"],
    sources: [
      {
        url: "https://example.com/ai-edu-report",
        title: "AI in Education Report",
        snippet: "Overview of AI-assisted learning outcomes and risks.",
        usedFor: "briefing"
      }
    ]
  },
  {
    id: "ubi",
    title: "Universal Basic Income",
    category: "Policy",
    summary: "Is universal basic income a viable safety net?",
    description: "UBI proposes unconditional cash payments to all citizens to reduce poverty.",
    keyPoints: ["Economic security", "Labor market shifts", "Funding models"],
    pros: ["Reduces poverty", "Supports automation transition"],
    cons: ["Funding challenges", "Inflation concerns"],
    fallacies: ["Slippery slope", "Cherry picking"],
    sources: [
      {
        url: "https://example.com/ubi-study",
        title: "UBI Pilot Study",
        snippet: "Findings from multiple UBI pilot programs.",
        usedFor: "briefing"
      }
    ]
  }
];

const slugify = (value: string) =>
  value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");

export const searchTopics = async (query: string): Promise<TopicSummary[]> => {
  const dbTopics = await prisma.topicCache.findMany({
    where: { topic: { contains: query, mode: "insensitive" } },
    take: 10
  });

  const cacheResults = dbTopics.map((topic) => ({
    id: slugify(topic.topic),
    title: topic.topic,
    category: "Cached",
    summary: topic.summary
  }));

  const staticResults = staticTopics
    .filter((topic) => topic.title.toLowerCase().includes(query.toLowerCase()))
    .map(({ id, title, category, summary }) => ({ id, title, category, summary }));

  return [...cacheResults, ...staticResults].slice(0, 10);
};

export const getTopicDetail = async (id: string): Promise<TopicDetail | null> => {
  const staticMatch = staticTopics.find((topic) => topic.id === id);
  if (staticMatch) {
    return staticMatch;
  }
  const cacheMatch = await prisma.topicCache.findFirst({
    where: { topic: { contains: id.replace(/-/g, " "), mode: "insensitive" } }
  });
  if (!cacheMatch) {
    return null;
  }
  try {
    const detail = JSON.parse(cacheMatch.detail) as TopicDetail;
    return { ...detail, id: slugify(cacheMatch.topic), title: cacheMatch.topic };
  } catch {
    return {
      id: slugify(cacheMatch.topic),
      title: cacheMatch.topic,
      category: "Cached",
      summary: cacheMatch.summary,
      description: cacheMatch.summary,
      keyPoints: [],
      pros: [],
      cons: [],
      fallacies: [],
      sources: []
    };
  }
};

export const cacheTopicBrief = async (topic: string, summary: string, detail: TopicDetail) => {
  await prisma.topicCache.upsert({
    where: { topic },
    update: {
      summary,
      detail: JSON.stringify(detail)
    },
    create: {
      topic,
      summary,
      detail: JSON.stringify(detail)
    }
  });
};
