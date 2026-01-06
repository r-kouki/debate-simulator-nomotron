import { describe, it, expect } from "vitest";
import { buildServer } from "../src/server";

describe("health", () => {
  it("returns ok", async () => {
    const app = buildServer();
    const response = await app.inject({
      method: "GET",
      url: "/health"
    });
    expect(response.statusCode).toBe(200);
    const body = response.json();
    expect(body.ok).toBe(true);
    await app.close();
  });
});
