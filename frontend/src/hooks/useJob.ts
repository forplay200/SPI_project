import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";

const terminal = new Set(["COMPLETED", "FAILED", "CANCELLED"]);

export function useJob(jobId: string | null | undefined) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: () => api.getJob(jobId as string),
    enabled: Boolean(jobId),
    refetchInterval: (query) =>
      terminal.has(query.state.data?.status ?? "") ? false : 1000,
  });
}
