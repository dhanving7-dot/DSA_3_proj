import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Command } from "cmdk"
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
  LogOut,
  Lightbulb,
  BookOpen,
  FlaskRound,
  GraduationCap,
} from "lucide-react"
import { useUIStore } from "@/store/uiStore"
import { useAuthStore } from "@/store/authStore"
import { useEntitySearch } from "@/hooks/useInsights"
import { HighlightSpans } from "@/components/concepts/HighlightText"
import { formatMs } from "@/lib/utils"

const ITEMS = [
  { icon: LayoutDashboard, label: "Dashboard", path: "/app/dashboard" },
  { icon: Users, label: "Student Management", path: "/app/students" },
  { icon: FlaskConical, label: "Laboratory Management", path: "/app/labs" },
  { icon: Settings2, label: "Allocation Configuration", path: "/app/config" },
  { icon: Share2, label: "Graph Visualization", path: "/app/graph" },
  { icon: PlayCircle, label: "Algorithm Playground", path: "/app/playground" },
  { icon: ClipboardList, label: "Allocation Results", path: "/app/results" },
  { icon: BarChart3, label: "Analytics", path: "/app/analytics" },
  { icon: Sparkles, label: "AI Command Center", path: "/app/ai" },
  { icon: GitCompare, label: "What-If Simulator", path: "/app/simulator" },
  { icon: Lightbulb, label: "Allocation Insights", path: "/app/insights" },
  { icon: BookOpen, label: "Algorithm Atlas", path: "/app/atlas" },
  { icon: FlaskRound, label: "Concept Lab", path: "/app/concepts" },
]

function useDebounced<T>(value: T, delay = 200): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = window.setTimeout(() => setDebounced(value), delay)
    return () => window.clearTimeout(t)
  }, [value, delay])
  return debounced
}

export function CommandPalette() {
  const open = useUIStore((s) => s.commandPaletteOpen)
  const setOpen = useUIStore((s) => s.setCommandPaletteOpen)

  useEffect(() => {
    function handler(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault()
        setOpen(!open)
      }
      if (e.key === "Escape") setOpen(false)
    }
    document.addEventListener("keydown", handler)
    return () => document.removeEventListener("keydown", handler)
  }, [open, setOpen])

  // mounted only while open, so the search box starts empty every time
  return open ? <PaletteDialog /> : null
}

function PaletteDialog() {
  const setOpen = useUIStore((s) => s.setCommandPaletteOpen)
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()
  const [query, setQuery] = useState("")
  const debounced = useDebounced(query)
  const search = useEntitySearch(debounced)

  function openEntity(type: "student" | "lab", id: number, title: string) {
    navigate(type === "student" ? `/app/students?search=${encodeURIComponent(title)}` : `/app/labs?focus=${id}`)
    setOpen(false)
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center bg-black/70 pt-[15vh] backdrop-blur-sm" onClick={() => setOpen(false)}>
      <div onClick={(e) => e.stopPropagation()} className="w-full max-w-lg overflow-hidden rounded-2xl glass-panel-strong shadow-2xl">
        <Command className="w-full">
          <div className="flex items-center border-b border-border-subtle px-4">
            <Command.Input
              autoFocus
              value={query}
              onValueChange={setQuery}
              placeholder="Search pages, students and labs..."
              className="h-12 w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted"
            />
            <kbd className="rounded border border-border-subtle px-1.5 py-0.5 text-[10px] text-ink-muted">ESC</kbd>
          </div>
          <Command.List className="max-h-80 overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-sm text-ink-muted">No results found.</Command.Empty>
            <Command.Group heading="Navigate" className="px-2 py-1 text-xs text-ink-muted [&_[cmdk-group-heading]]:px-1 [&_[cmdk-group-heading]]:py-1">
              {ITEMS.map((item) => (
                <Command.Item
                  key={item.path}
                  onSelect={() => {
                    navigate(item.path)
                    setOpen(false)
                  }}
                  className="flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-sm text-ink-secondary data-[selected=true]:bg-white/[0.08] data-[selected=true]:text-ink"
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </Command.Item>
              ))}
            </Command.Group>
            {search.data && search.data.results.length > 0 && (
              <Command.Group
                heading={`Students & labs · ${search.data.algorithm} · ${search.data.comparisons.toLocaleString()} comparisons · ${formatMs(search.data.search_time_ms)}`}
                className="px-2 py-1 text-xs text-ink-muted [&_[cmdk-group-heading]]:px-1 [&_[cmdk-group-heading]]:py-1"
              >
                {search.data.results.map((hit) => {
                  const field = hit.fields.name ?? Object.values(hit.fields)[0]
                  const Icon = hit.type === "student" ? GraduationCap : FlaskConical
                  return (
                    <Command.Item
                      key={`${hit.type}-${hit.id}`}
                      value={`entity ${hit.type} ${hit.id} ${hit.title}`}
                      keywords={[query]}
                      onSelect={() => openEntity(hit.type, hit.id, hit.title)}
                      className="flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-sm text-ink-secondary data-[selected=true]:bg-white/[0.08] data-[selected=true]:text-ink"
                    >
                      <Icon className="h-4 w-4 shrink-0" />
                      <span className="min-w-0 flex-1 truncate">
                        {hit.fields.name ? <HighlightSpans value={field.value} spans={field.spans} /> : hit.title}
                        <span className="ml-2 text-[11px] text-ink-muted">{hit.subtitle}</span>
                      </span>
                      {hit.match === "fuzzy" && <span className="rounded border border-warning/30 px-1 text-[10px] text-warning">≈ {hit.distance}</span>}
                    </Command.Item>
                  )
                })}
              </Command.Group>
            )}
            <Command.Group heading="Session" className="px-2 py-1 text-xs text-ink-muted">
              <Command.Item
                onSelect={() => {
                  logout()
                  navigate("/login")
                  setOpen(false)
                }}
                className="flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-sm text-critical data-[selected=true]:bg-critical/10"
              >
                <LogOut className="h-4 w-4" />
                Sign out
              </Command.Item>
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  )
}
