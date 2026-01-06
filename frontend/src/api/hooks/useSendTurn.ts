import { useMutation } from "@tanstack/react-query";
import { getApiAdapter } from "../adapter";
import type { SendTurnRequest } from "../types";

export const useSendTurn = () => {
  return useMutation({
    mutationFn: (payload: SendTurnRequest) => getApiAdapter().sendTurn(payload)
  });
};
