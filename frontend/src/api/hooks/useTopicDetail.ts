import { useQuery } from "@tanstack/react-query";
import { getApiAdapter } from "../adapter";

export const useTopicDetail = (id?: string) => {
  return useQuery({
    queryKey: ["topics", id],
    queryFn: () => getApiAdapter().getTopic(id as string),
    enabled: Boolean(id)
  });
};
