import { QueryClient } from "@tanstack/react-query";
import { useNotificationStore } from "../state/notificationStore";
import { useApiStatusStore } from "../state/apiStatusStore";
import { useWindowStore } from "../state/windowStore";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      onError: (error: unknown) => {
        const message = error instanceof Error ? error.message : "Unknown error";
        useApiStatusStore.getState().setStatus(false, message);
        useNotificationStore.getState().push({
          type: "error",
          title: "API Error",
          message
        });
        useWindowStore.getState().openWindow("connection-status");
      }
    },
    mutations: {
      onError: (error: unknown) => {
        const message = error instanceof Error ? error.message : "Unknown error";
        useNotificationStore.getState().push({
          type: "error",
          title: "API Error",
          message
        });
      }
    }
  }
});
