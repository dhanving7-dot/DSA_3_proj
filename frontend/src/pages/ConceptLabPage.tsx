import { useEffect } from "react"
import { useLocation, useSearchParams, Link } from "react-router-dom"
import { BookOpen } from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { StringsLab } from "@/components/concepts/StringsLab"
import { DPLab } from "@/components/concepts/DPLab"
import { FlowLab } from "@/components/concepts/FlowLab"
import { NPLab } from "@/components/concepts/NPLab"
import { RandomLab } from "@/components/concepts/RandomLab"
import { useAtlas } from "@/hooks/useInsights"

const TABS = [
  { id: "strings", label: "Strings", module: 2 },
  { id: "dp", label: "Dynamic Programming", module: 3 },
  { id: "flow", label: "Flow & Cuts", module: 4 },
  { id: "np", label: "NP & Approximation", module: 5 },
  { id: "random", label: "Randomised & Parallel", module: 6 },
]

export default function ConceptLabPage() {
  const [params, setParams] = useSearchParams()
  const location = useLocation()
  const tab = TABS.some((t) => t.id === params.get("tab")) ? (params.get("tab") as string) : "strings"
  const { data: atlas } = useAtlas()

  // deep links from the Atlas: /app/concepts?tab=dp#obst scrolls to that demo once the tab has rendered
  useEffect(() => {
    if (!location.hash) return
    const id = location.hash.slice(1)
    const timer = window.setTimeout(() => document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" }), 150)
    return () => window.clearTimeout(timer)
  }, [location.hash, tab])

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-3xl text-sm text-ink-secondary">
          Every demo runs the hand-built implementation from <code className="text-ink">backend/app/algorithms</code> on input you choose -
          tables, traces and comparisons come straight from the server, and most results are checked against an independent brute-force
          oracle before they are shown.
        </p>
        <Link to="/app/atlas" className="flex items-center gap-1.5 text-xs text-brand-400 hover:underline">
          <BookOpen className="h-3.5 w-3.5" /> Algorithm Atlas
        </Link>
      </div>
      <Tabs value={tab} onValueChange={(v) => setParams({ tab: v }, { replace: true })}>
        <TabsList className="h-auto flex-wrap">
          {TABS.map((t) => (
            <TabsTrigger key={t.id} value={t.id}>
              <span className="mr-1.5 text-[10px] text-ink-muted">M{t.module}</span>
              {t.label}
            </TabsTrigger>
          ))}
        </TabsList>
        <TabsContent value="strings"><StringsLab /></TabsContent>
        <TabsContent value="dp"><DPLab /></TabsContent>
        <TabsContent value="flow"><FlowLab /></TabsContent>
        <TabsContent value="np"><NPLab reductions={atlas?.reductions ?? []} /></TabsContent>
        <TabsContent value="random"><RandomLab /></TabsContent>
      </Tabs>
    </div>
  )
}
