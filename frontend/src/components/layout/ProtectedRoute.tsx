import { Navigate } from "react-router-dom"
import { useAuthStore } from "@/store/authStore"
import type { UserRole } from "@/types"

export function ProtectedRoute({ children, roles }: { children: React.ReactNode; roles?: UserRole[] }) {
  const token = useAuthStore((s) => s.token)
  const user = useAuthStore((s) => s.user)

  if (!token || !user) {
    return <Navigate to="/login" replace />
  }
  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/app/dashboard" replace />
  }
  return <>{children}</>
}
