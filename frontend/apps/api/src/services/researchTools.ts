import { z } from "zod";
import type { SourceSchema } from "@debate/contracts";

export type Source = z.infer<typeof SourceSchema>;

const defaultSources: Source[] = [
  {
    url: "https://example.com/ai-education",
    title: "AI in Education Overview",
    snippet: "AI tools can personalize learning but raise concerns about privacy and equity.",
    usedFor: "briefing"
  },
  {
    url: "https://example.com/ubi",
    title: "Universal Basic Income Summary",
    snippet: "UBI proposes unconditional cash payments to support citizens in economic transitions.",
    usedFor: "briefing"
  }
];

const parseWikipediaSource = (topic: string, summary: string, url?: string): Source => ({
  url: url || `https://en.wikipedia.org/wiki/${encodeURIComponent(topic)}`,
  title: topic,
  snippet: summary.slice(0, 240),
  usedFor: "briefing"
});

export const searchWikipedia = async (topic: string): Promise<Source[]> => {
  try {
    const summaryResponse = await fetch(
      `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(topic)}`
    );
    if (!summaryResponse.ok) {
      throw new Error("Wikipedia summary not found");
    }
    const summaryJson = (await summaryResponse.json()) as {
      extract?: string;
      content_urls?: { desktop?: { page?: string } };
    };
    if (!summaryJson.extract) {
      throw new Error("No summary extract");
    }
    const url = summaryJson.content_urls?.desktop?.page;
    return [parseWikipediaSource(topic, summaryJson.extract, url)];
  } catch {
    return defaultSources;
  }
};

export const buildFallbackBriefing = (topic: string, stance?: "PRO" | "CON" | null) => {
  const keyFacts = [
    `${topic} has multiple perspectives; consider evidence, ethics, and feasibility.`,
    "Define key terms and ground the debate in shared facts."
  ];
  return {
    keyFacts,
    proArguments: ["Potential benefits include efficiency, equity, or innovation."],
    conArguments: ["Potential risks include bias, cost, or unintended consequences."],
    counterArguments: [
      `Acknowledge the ${stance === "PRO" ? "benefits" : "risks"} while noting tradeoffs.`
    ],
    questions: ["What evidence supports your claim?", "What are the long-term impacts?"]
  };
};
