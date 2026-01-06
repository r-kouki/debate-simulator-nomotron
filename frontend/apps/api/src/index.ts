import "dotenv/config";
import { buildServer } from "./server";
import { getEnv } from "./utils/env";
import { seedAchievements } from "./services/gamification";

const start = async () => {
  const env = getEnv();
  const app = buildServer();

  await seedAchievements();

  try {
    await app.listen({ port: env.port, host: "0.0.0.0" });
    app.log.info(`API listening on port ${env.port}`);
  } catch (error) {
    app.log.error(error, "Failed to start server");
    process.exit(1);
  }
};

start();
