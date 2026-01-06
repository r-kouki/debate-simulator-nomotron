import { useQuery } from "@tanstack/react-query";
import { getApiAdapter } from "../adapter";

export const useProfile = () => {
  return useQuery({
    queryKey: ["profile"],
    queryFn: () => getApiAdapter().getProfile()
  });
};
