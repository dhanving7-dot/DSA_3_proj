import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { Network, ArrowRight } from "lucide-react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card } from "@/components/ui/card"
import { useLogin } from "@/hooks/useAuth"
import { apiErrorMessage } from "@/lib/api"

export default function LoginPage() {
  const [email, setEmail] = useState("admin@campus.edu")
  const [password, setPassword] = useState("")
  const navigate = useNavigate()
  const login = useLogin()

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    try {
      await login.mutateAsync({ email, password })
      toast.success("Welcome back")
      navigate("/app/dashboard")
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas bg-grid px-4">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-2">
          <Link to="/" className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-violet-500">
            <Network className="h-5 w-5 text-white" />
          </Link>
          <h1 className="text-xl font-semibold text-ink">Sign in to AllocateX</h1>
          <p className="text-xs text-ink-muted">Use the seeded admin@campus.edu / Admin@123 for a full demo</p>
        </div>

        <Card className="p-6">
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@campus.edu" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
            </div>
            <Button type="submit" className="w-full" disabled={login.isPending}>
              {login.isPending ? "Signing in..." : "Sign in"} <ArrowRight className="h-4 w-4" />
            </Button>
          </form>
        </Card>

        <p className="mt-4 text-center text-xs text-ink-muted">
          Don't have an account?{" "}
          <Link to="/register" className="text-brand-400 hover:underline">Create one</Link>
        </p>
      </motion.div>
    </div>
  )
}
