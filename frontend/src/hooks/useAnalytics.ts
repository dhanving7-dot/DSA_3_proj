import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { AnalyticsOverview } from "@/types"

export function useAnalyticsOverview(runId?: number | null) {
  return useQuery({
    queryKey: ["analytics", "overview", runId],
    queryFn: async () => {
      const { data } = await api.get<AnalyticsOverview>("/analytics/overview", { params: runId ? { run_id: runId } : {} })
      return data
    },
    refetchInterval: 15000,
  })
}
