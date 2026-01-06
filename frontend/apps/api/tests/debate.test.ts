import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { buildServer } from "../src/server";

const mockResponses = [
  {
    choices: [
      {
        message: {
          content: JSON.stringify({
            keyFacts: ["Fact 1"],
            proArguments: ["Pro"],
            conArguments: ["Con"],
            counterArguments: ["Counter"],
            questions: ["Q1"],
            sources: [
              {
                url: "https://example.com",
                title: "Example",
                snippet: "Snippet",
                usedFor: "briefing"
              }
            ]
          })
        }
      }
    ]
  },
  {
    choices: [
      {
        message: {
          content: JSON.stringify({
            message: "AI response",
            citations: []
          })
        }
      }
    ]
  }
];

describe("debate flow", () => {
  const originalFetch = global.fetch;
  let callCount = 0;

  beforeEach(() => {
    process.env.OPENROUTER_API_KEY = "test";
    callCount = 0;
    global.fetch = vi.fn(async () => {
      const body = mockResponses[Math.min(callCount, mockResponses.length - 1)];
      callCount += 1;
      return {
        ok: true,
        json: async () => body
      } as Response;
    });
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it("creates a debate and returns an AI response", async () => {
    const app = buildServer();
    const createResponse = await app.inject({
      method: "POST",
      url: "/debates",
      payload: {
        mode: "HUMAN_VS_AI",
        topic: "Test Topic",
        rounds: 1,
        participants: [
          { type: "HUMAN", name: "Player", stance: "PRO" },
          { type: "AI", name: "Bot", stance: "CON" }
        ]
      }
    });
    expect(createResponse.statusCode).toBe(200);
    const createBody = createResponse.json();
    const human = createBody.debate.participants.find((p: { type: string }) => p.type === "HUMAN");

    const turnResponse = await app.inject({
      method: "POST",
      url: `/debates/${createBody.debateId}/turns`,
      payload: {
        participantId: human.id,
        content: "Here is my argument."
      }
    });

    expect(turnResponse.statusCode).toBe(200);
    const turnBody = turnResponse.json();
    expect(turnBody.aiTurns?.length).toBe(1);
    await app.close();
  });
});
