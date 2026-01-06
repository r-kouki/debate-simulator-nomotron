export const getEnv = () => {
  return {
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL as string | undefined,
    useMocks: (import.meta.env.VITE_USE_MOCKS as string | undefined) === "true",
    openRouterApiKey: import.meta.env.VITE_OPENROUTER_API_KEY as string | undefined,
    openRouterModel: import.meta.env.VITE_OPENROUTER_MODEL as string | undefined,
    openRouterBaseUrl: import.meta.env.VITE_OPENROUTER_BASE_URL as string | undefined
  };
};
