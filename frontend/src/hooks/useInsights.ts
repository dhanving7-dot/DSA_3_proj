import { useMutation, useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type {
  AtlasResponse,
  AuditSample,
  BottleneckInsight,
  MonteCarloResult,
  OptimalityInsight,
  SearchAlgorithm,
  SearchResponse,
  SetCoverInsight,
  SkillSupplyInsight,
} from "@/types/insights"

function insightQuery<T>(key: string, path: string, runId?: number | null) {
  return {
    queryKey: ["insights", key, runId ?? null],
    queryFn: async () => {
      const { data } = await api.get<T>(path, { params: runId ? { run_id: runId } : {} })
      return data
    },
  }
}

export function useBottleneck(runId?: number | null) {
  return useQuery(insightQuery<BottleneckInsight>("bottleneck", "/insights/bottleneck", runId))
}

export function useSetCover(runId?: number | null) {
  return useQuery(insightQuery<SetCoverInsight>("set-cover", "/insights/set-cover", runId))
}

export function useOptimalityGap(runId?: number | null) {
  return useQuery(insightQuery<OptimalityInsight>("optimality", "/insights/optimality-gap", runId))
}

export function useSkillSupply() {
  return useQuery(insightQuery<SkillSupplyInsight>("skills", "/insights/skill-supply"))
}

export function useMonteCarlo() {
  return useMutation({
    mutationFn: async (payload: { trials: number; outage_probability: number; seed: number | null; algorithm: string }) => {
      const { data } = await api.post<MonteCarloResult>("/insights/monte-carlo", payload)
      return data
    },
  })
}

export function useAuditSample() {
  return useMutation({
    mutationFn: async (payload: { run_id: number | null; k: number; seed: number | null }) => {
      const { data } = await api.get<AuditSample>("/insights/audit-sample", {
        params: { k: payload.k, ...(payload.run_id ? { run_id: payload.run_id } : {}), ...(payload.seed != null ? { seed: payload.seed } : {}) },
      })
      return data
    },
  })
}

export function useAtlas() {
  return useQuery({
    queryKey: ["concepts", "atlas"],
    queryFn: async () => {
      const { data } = await api.get<AtlasResponse>("/concepts/atlas")
      return data
    },
    staleTime: Infinity,
  })
}

export function useEntitySearch(q: string, algorithm: SearchAlgorithm = "KMP", fuzzy = true) {
  const trimmed = q.trim()
  return useQuery({
    queryKey: ["search", trimmed, algorithm, fuzzy],
    queryFn: async () => {
      const { data } = await api.get<SearchResponse>("/search", { params: { q: trimmed, algorithm, fuzzy, limit: 8 } })
      return data
    },
    enabled: trimmed.length >= 2,
    staleTime: 30_000,
  })
}

/** Generic runner for Concept Lab demos: POST /concepts/<path> with the given body. */
export function useConceptDemo<TResponse, TBody = Record<string, unknown>>(path: string) {
  return useMutation({
    mutationFn: async (body: TBody) => {
      const { data } = await api.post<TResponse>(`/concepts${path}`, body)
      return data
    },
  })
}
