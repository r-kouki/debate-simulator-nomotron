import { useMutation } from "@tanstack/react-query";
import { getApiAdapter } from "../adapter";
import type { PlayerProfileResponse } from "../types";

export const useUpdateProfile = () => {
  return useMutation({
    mutationFn: (payload: Partial<PlayerProfileResponse>) => getApiAdapter().updateProfile(payload)
  });
};
