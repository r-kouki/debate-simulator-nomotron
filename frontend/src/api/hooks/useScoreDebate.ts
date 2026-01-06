import { useMutation } from "@tanstack/react-query";
import { getApiAdapter } from "../adapter";
import type { ScoreDebateRequest } from "../types";

export const useScoreDebate = () => {
  return useMutation({
    mutationFn: (payload: ScoreDebateRequest) => getApiAdapter().scoreDebate(payload)
  });
};
