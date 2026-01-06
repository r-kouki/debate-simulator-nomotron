import { useQuery } from "@tanstack/react-query";
import { getApiAdapter } from "../adapter";
import { useApiStatusStore } from "../../state/apiStatusStore";

export const useHealth = () => {
  const setStatus = useApiStatusStore((state) => state.setStatus);
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const response = await getApiAdapter().health();
      setStatus(response.ok, response.ok ? undefined : "Health check failed");
      return response;
    },
    refetchInterval: 60_000,
    onError: (error) => {
      const message = error instanceof Error ? error.message : "Health check failed";
      setStatus(false, message);
    }
  });
};
