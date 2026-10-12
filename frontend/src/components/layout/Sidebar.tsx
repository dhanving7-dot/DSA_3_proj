import { NavLink } from "react-router-dom"
import {
  LayoutDashboard,
  Users,
  FlaskConical,
  Settings2,
  Share2,
  PlayCircle,
  ClipboardList,
  BarChart3,
  Sparkles,
  GitCompare,
  Network,
  Lightbulb,
  BookOpen,
  FlaskRound,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/store/authStore"

const NAV: { icon: typeof Users; label: string; path: string; roles: string[]; section?: string }[] = [
  { icon: LayoutDashboard, label: "Dashboard", path: "/app/dashboard", roles: ["ADMIN", "FACULTY", "STUDENT"] },
  { icon: Users, label: "Students", path: "/app/students", roles: ["ADMIN", "FACULTY"] },
  { icon: FlaskConical, label: "Laboratories", path: "/app/labs", roles: ["ADMIN", "FACULTY"] },
  { icon: Settings2, label: "Allocation Config", path: "/app/config", roles: ["ADMIN", "FACULTY"] },
  { icon: Share2, label: "Graph Visualization", path: "/app/graph", roles: ["ADMIN", "FACULTY", "STUDENT"] },
  { icon: PlayCircle, label: "Algorithm Playground", path: "/app/playground", roles: ["ADMIN", "FACULTY", "STUDENT"] },
  { icon: ClipboardList, label: "Allocation Results", path: "/app/results", roles: ["ADMIN", "FACULTY", "STUDENT"] },
  { icon: BarChart3, label: "Analytics", path: "/app/analytics", roles: ["ADMIN", "FACULTY", "STUDENT"] },
  { icon: Lightbulb, label: "Allocation Insights", path: "/app/insights", roles: ["ADMIN", "FACULTY", "STUDENT"] },
  { icon: Sparkles, label: "AI Command Center", path: "/app/ai", roles: ["ADMIN", "FACULTY"] },
  { icon: GitCompare, label: "What-If Simulator", path: "/app/simulator", roles: ["ADMIN", "FACULTY"] },
  { icon: BookOpen, label: "Algorithm Atlas", path: "/app/atlas", roles: ["ADMIN", "FACULTY", "STUDENT"], section: "Learn" },
  { icon: FlaskRound, label: "Concept Lab", path: "/app/concepts", roles: ["ADMIN", "FACULTY", "STUDENT"] },
]

export function Sidebar() {
  const role = useAuthStore((s) => s.user?.role)

  return (
    <aside className="hidden w-64 flex-col border-r border-border-subtle bg-canvas-raised/60 lg:flex">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500 to-violet-500">
          <Network className="h-4 w-4 text-white" />
        </div>
        <div>
          <p className="text-sm font-semibold text-ink">AllocateX</p>
          <p className="text-[10px] text-ink-muted">Lab Allocation Engine</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-2">
        {NAV.filter((item) => !role || item.roles.includes(role)).map((item) => (
          <div key={item.path}>
            {item.section && (
              <p className="px-3 pb-1 pt-4 text-[10px] font-medium uppercase tracking-wider text-ink-muted">{item.section}</p>
            )}
            <NavLink
              to={item.path}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive ? "bg-white/[0.08] text-ink" : "text-ink-muted hover:bg-white/[0.04] hover:text-ink-secondary"
                )
              }
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          </div>
        ))}
      </nav>

      <div className="border-t border-border-subtle p-4">
        <div className="rounded-xl border border-border-subtle bg-white/[0.03] p-3 text-xs text-ink-muted">
          <p className="font-medium text-ink-secondary">Press ⌘K</p>
          <p>to open the command palette</p>
        </div>
      </div>
    </aside>
  )
}
