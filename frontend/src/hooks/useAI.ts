import { useMutation, useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { AIAnalyticsQueryResponse, AICommandResponse, AIExplainResponse, Conflict } from "@/types"

export function useAICommand() {
  return useMutation({
    mutationFn: async (payload: { text: string; auto_execute: boolean }) => {
      const { data } = await api.post<AICommandResponse>("/ai/command", payload)
      return data
    },
  })
}

export function useAIExplain() {
  return useMutation({
    mutationFn: async (payload: { allocation_id?: number; student_id?: number; run_id?: number }) => {
      const { data } = await api.post<AIExplainResponse>("/ai/explain", payload)
      return data
    },
  })
}

export function useAIAnalyticsQuery() {
  return useMutation({
    mutationFn: async (payload: { question: string; run_id?: number | null }) => {
      const { data } = await api.post<AIAnalyticsQueryResponse>("/ai/analytics-query", payload)
      return data
    },
  })
}

export function useAIConflicts() {
  return useQuery({
    queryKey: ["ai-conflicts"],
    queryFn: async () => {
      const { data } = await api.get<{ conflicts: Conflict[] }>("/ai/conflicts")
      return data.conflicts
    },
  })
}

export function useAIReport(runId?: number | null) {
  return useQuery({
    queryKey: ["ai-report", runId],
    queryFn: async () => {
      const { data } = await api.get<{ report_markdown: string }>("/ai/report", { params: runId ? { run_id: runId } : {} })
      return data.report_markdown
    },
    enabled: false,
  })
}
