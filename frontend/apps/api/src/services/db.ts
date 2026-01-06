import { PrismaClient } from "@prisma/client";
import { getEnv } from "../utils/env";

const env = getEnv();

export const prisma = new PrismaClient({
  datasources: {
    db: { url: env.databaseUrl }
  }
});
