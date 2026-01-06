import { useMutation } from "@tanstack/react-query";
import { getApiAdapter } from "../adapter";
import type { StartDebateRequest } from "../types";

export const useStartDebate = () => {
  return useMutation({
    mutationFn: (payload: StartDebateRequest) => getApiAdapter().startDebate(payload)
  });
};
