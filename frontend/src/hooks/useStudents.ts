import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { Student, StudentPreference } from "@/types"

export interface StudentFilters {
  department?: string
  year?: number
  search?: string
}

export function useStudents(filters: StudentFilters = {}) {
  return useQuery({
    queryKey: ["students", filters],
    queryFn: async () => {
      const { data } = await api.get<Student[]>("/students", { params: filters })
      return data
    },
  })
}

export function useCreateStudent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: Record<string, unknown>) => {
      const { data } = await api.post<Student>("/students", payload)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["students"] }),
  })
}

export function useUpdateStudent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Record<string, unknown> }) => {
      const { data } = await api.put<Student>(`/students/${id}`, payload)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["students"] }),
  })
}

export function useDeleteStudent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/students/${id}`)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["students"] }),
  })
}

export function useAddSkill() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ studentId, skill_name, proficiency_level }: { studentId: number; skill_name: string; proficiency_level: number }) => {
      const { data } = await api.post<Student>(`/students/${studentId}/skills`, { skill_name, proficiency_level })
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["students"] }),
  })
}

export function useRemoveSkill() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ studentId, skillId }: { studentId: number; skillId: number }) => {
      const { data } = await api.delete<Student>(`/students/${studentId}/skills/${skillId}`)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["students"] }),
  })
}

export function useSetPreferences() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ studentId, preferences }: { studentId: number; preferences: Omit<StudentPreference, "id">[] }) => {
      const { data } = await api.put<Student>(`/students/${studentId}/preferences`, preferences)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["students"] }),
  })
}

export function useImportStudentsCsv() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData()
      form.append("file", file)
      const { data } = await api.post<{ created: number; errors: string[] }>("/students/import", form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["students"] }),
  })
}

export async function downloadStudentsCsv() {
  const { data } = await api.get("/students/export", { responseType: "blob" })
  const url = URL.createObjectURL(data as Blob)
  const link = document.createElement("a")
  link.href = url
  link.download = "students_export.csv"
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
