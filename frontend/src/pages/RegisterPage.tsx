import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { Network, ArrowRight } from "lucide-react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useRegister } from "@/hooks/useAuth"
import { apiErrorMessage } from "@/lib/api"
import type { UserRole } from "@/types"

export default function RegisterPage() {
  const [fullName, setFullName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [role, setRole] = useState<UserRole>("STUDENT")
  const navigate = useNavigate()
  const register = useRegister()

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    try {
      await register.mutateAsync({ email, password, full_name: fullName, role })
      toast.success("Account created")
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
          <h1 className="text-xl font-semibold text-ink">Create your account</h1>
        </div>

        <Card className="p-6">
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="name">Full name</Label>
              <Input id="name" required value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Jane Doe" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@campus.edu" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" minLength={8} required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="min 8 characters" />
            </div>
            <div className="space-y-1.5">
              <Label>Role</Label>
              <Select value={role} onValueChange={(v) => setRole(v as UserRole)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="STUDENT">Student</SelectItem>
                  <SelectItem value="FACULTY">Faculty</SelectItem>
                  <SelectItem value="ADMIN">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button type="submit" className="w-full" disabled={register.isPending}>
              {register.isPending ? "Creating..." : "Create account"} <ArrowRight className="h-4 w-4" />
            </Button>
          </form>
        </Card>

        <p className="mt-4 text-center text-xs text-ink-muted">
          Already have an account?{" "}
          <Link to="/login" className="text-brand-400 hover:underline">Sign in</Link>
        </p>
      </motion.div>
    </div>
  )
}
