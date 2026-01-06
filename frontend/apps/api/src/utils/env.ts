export const getEnv = () => {
  const nodeEnv = process.env.NODE_ENV || "development";
  return {
    nodeEnv,
    port: Number(process.env.PORT || 4000),
    frontendOrigin: process.env.FRONTEND_ORIGIN || "http://localhost:5173",
    openRouterApiKey: process.env.OPENROUTER_API_KEY || "",
    openRouterModel: process.env.OPENROUTER_MODEL || "nvidia/nemotron-nano-9b-v2:free",
    openRouterSiteUrl: process.env.OPENROUTER_SITE_URL,
    openRouterAppName: process.env.OPENROUTER_APP_NAME,
    openRouterUseWeb: process.env.OPENROUTER_USE_WEB === "true",
    databaseUrl: process.env.DATABASE_URL || "file:./dev.db"
  };
};
