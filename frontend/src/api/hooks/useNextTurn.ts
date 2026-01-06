import { useMutation } from "@tanstack/react-query";
import { getApiAdapter } from "../adapter";

export const useNextTurn = () => {
  return useMutation({
    mutationFn: (debateId: string) => getApiAdapter().nextTurn(debateId)
  });
};
