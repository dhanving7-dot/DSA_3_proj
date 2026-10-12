import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { Laboratory } from "@/types"

export function useLabs(department?: string) {
  return useQuery({
    queryKey: ["labs", department],
    queryFn: async () => {
      const { data } = await api.get<Laboratory[]>("/labs", { params: department ? { department } : {} })
      return data
    },
  })
}

export function useCreateLab() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: Record<string, unknown>) => {
      const { data } = await api.post<Laboratory>("/labs", payload)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["labs"] }),
  })
}

export function useUpdateLab() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Record<string, unknown> }) => {
      const { data } = await api.put<Laboratory>(`/labs/${id}`, payload)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["labs"] }),
  })
}

export function useDeleteLab() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/labs/${id}`)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["labs"] }),
  })
}

export function useAddLabSkill() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ labId, ...payload }: { labId: number; skill_name: string; min_proficiency: number; required: boolean }) => {
      const { data } = await api.post<Laboratory>(`/labs/${labId}/skills`, payload)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["labs"] }),
  })
}

export function useAddLabEquipment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ labId, ...payload }: { labId: number; equipment_name: string; quantity: number }) => {
      const { data } = await api.post<Laboratory>(`/labs/${labId}/equipment`, payload)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["labs"] }),
  })
}

export function useAddLabTimeSlot() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ labId, ...payload }: { labId: number; day_of_week: number; start_time: string; end_time: string; is_available: boolean }) => {
      const { data } = await api.post<Laboratory>(`/labs/${labId}/time-slots`, payload)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["labs"] }),
  })
}
