import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type {
  AlgorithmInfo,
  AlgorithmName,
  AllocationConfig,
  AllocationRun,
  AllocationRunDetail,
  MatchingResult,
  SimulationResult,
} from "@/types"

export function useAllocationRuns() {
  return useQuery({
    queryKey: ["allocation-runs"],
    queryFn: async () => {
      const { data } = await api.get<AllocationRun[]>("/allocation/runs")
      return data
    },
  })
}

export function useAllocationRun(runId: number | null) {
  return useQuery({
    queryKey: ["allocation-run", runId],
    queryFn: async () => {
      const { data } = await api.get<AllocationRunDetail>(`/allocation/runs/${runId}`)
      return data
    },
    enabled: runId != null,
  })
}

export function useGenerateAllocation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: {
      algorithm: AlgorithmName
      config: AllocationConfig
      student_ids?: number[] | null
      lab_ids?: number[] | null
      stream_progress?: boolean
    }) => {
      const { data } = await api.post<AllocationRunDetail>("/allocation/generate", payload)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["allocation-runs"] })
      qc.invalidateQueries({ queryKey: ["analytics"] })
    },
  })
}

export function useSimulateAllocation() {
  return useMutation({
    mutationFn: async (payload: Record<string, unknown>) => {
      const { data } = await api.post<SimulationResult>("/allocation/simulate", payload)
      return data
    },
  })
}

export function useAlgorithmInfo() {
  return useQuery({
    queryKey: ["algorithm-info"],
    queryFn: async () => {
      const { data } = await api.get<Record<AlgorithmName, AlgorithmInfo>>("/matching/algorithms")
      return data
    },
  })
}

export function useRunPlayground() {
  return useMutation({
    mutationFn: async (payload: {
      algorithm: AlgorithmName
      num_left: number
      num_right: number
      edge_probability: number
      seed?: number | null
      channel?: string
    }) => {
      const { channel, ...body } = payload
      const { data } = await api.post<{
        input_edges: [number, number][]
        num_left: number
        num_right: number
        edge_costs: number[] | null
        total_cost: number | null
        result: MatchingResult
      }>(
        "/matching/run",
        body,
        { params: channel ? { channel } : {} }
      )
      return data
    },
  })
}

export interface ComparisonRow {
  algorithm: AlgorithmName
  // present only when the algorithm cannot honour the config (e.g. Kuhn with a fairness cap)
  skipped_reason?: string
  run_id?: number
  matched_count?: number
  unmatched_count?: number
  execution_time_ms?: number
  preference_satisfaction?: number
  capacity_utilization?: number
  vertices?: number
  edges?: number
  iterations?: number
  time_complexity?: string
  total_score?: number
}

export function useCompareAlgorithms() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: { config: AllocationConfig; student_ids?: number[] | null; lab_ids?: number[] | null; algorithms?: AlgorithmName[] }) => {
      const { data } = await api.post<{ comparisons: ComparisonRow[] }>("/matching/compare", payload)
      return data.comparisons
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["allocation-runs"] })
      qc.invalidateQueries({ queryKey: ["analytics"] })
    },
  })
}
