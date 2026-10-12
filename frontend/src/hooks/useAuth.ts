import { useMutation } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { useAuthStore } from "@/store/authStore"
import type { User, UserRole } from "@/types"

interface TokenResponse {
  access_token: string
  user: User
}

export function useLogin() {
  const setAuth = useAuthStore((s) => s.setAuth)
  return useMutation({
    mutationFn: async (payload: { email: string; password: string }) => {
      const { data } = await api.post<TokenResponse>("/auth/login", payload)
      return data
    },
    onSuccess: (data) => setAuth(data.access_token, data.user),
  })
}

export function useRegister() {
  const setAuth = useAuthStore((s) => s.setAuth)
  return useMutation({
    mutationFn: async (payload: { email: string; password: string; full_name: string; role: UserRole }) => {
      const { data } = await api.post<TokenResponse>("/auth/register", payload)
      return data
    },
    onSuccess: (data) => setAuth(data.access_token, data.user),
  })
}
