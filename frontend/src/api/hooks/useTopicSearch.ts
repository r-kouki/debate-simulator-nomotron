import { useQuery } from "@tanstack/react-query";
import { getApiAdapter } from "../adapter";

export const useTopicSearch = (query: string) => {
  return useQuery({
    queryKey: ["topics", "search", query],
    queryFn: () => getApiAdapter().searchTopics(query),
    enabled: query.trim().length > 0
  });
};
