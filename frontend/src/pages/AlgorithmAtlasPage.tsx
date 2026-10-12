import { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { ArrowUpRight, FlaskConical, Search } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useAtlas } from "@/hooks/useInsights"
import { cn } from "@/lib/utils"
import type { AtlasAlgorithm } from "@/types/insights"

/** Module 1: which question the system answers, and which algorithm family answers it. */
const QUERY_MAP = [
  { query: "Who goes to which lab?", family: "Maximum bipartite matching / max-flow", cost: "O(E√V) (Hopcroft-Karp, Dinic)", where: "/app/config" },
  { query: "Which maximum allocation is best for students?", family: "Min-cost max-flow (assignment problem)", cost: "O(F·E log V)", where: "/app/config" },
  { query: "Why can't everyone be placed?", family: "Min cut · Hall's theorem · König", cost: "O(V + E) after max flow", where: "/app/insights#bottleneck" },
  { query: "Which labs must stay open?", family: "Set cover (NP-hard) - greedy H(n) vs exact", cost: "O(k·n) / O(2ᵏ)", where: "/app/insights#setcover" },
  { query: "How many students qualify for each skill combination?", family: "SOS dynamic programming", cost: "O(k·2ᵏ)", where: "/app/insights#skills" },
  { query: "How robust is the allocation to lab outages?", family: "Monte Carlo simulation", cost: "O(trials × allocation)", where: "/app/simulator" },
  { query: "Find a student or lab by (mistyped) name", family: "KMP / Z / Rabin-Karp / suffix array + edit distance", cost: "O(n + m) + O(n·m) fuzzy", where: "/app/concepts?tab=strings#search-race" },
  { query: "Understand a free-text command", family: "Aho-Corasick + Damerau-Levenshtein", cost: "O(n + Σ|P|)", where: "/app/ai" },
  { query: "Audit a run without bias", family: "Reservoir sampling", cost: "O(n) time, O(k) memory", where: "/app/results" },
]

function demoLink(demo: string) {
  const [tab, anchor] = demo.split(":")
  return `/app/concepts?tab=${tab}#${anchor}`
}

export default function AlgorithmAtlasPage() {
  const { data, isLoading } = useAtlas()
  const [filter, setFilter] = useState("")
  const [module, setModule] = useState<number | null>(null)

  const visible = useMemo(() => {
    const q = filter.trim().toLowerCase()
    return (data?.algorithms ?? []).filter(
      (a) =>
        (module == null || a.module === module) &&
        (!q || [a.name, a.category, a.summary, a.time_complexity].some((s) => s.toLowerCase().includes(q)))
    )
  }, [data, filter, module])

  if (isLoading || !data) return <Skeleton className="h-96 w-full" />

  const usedCount = data.algorithms.filter((a) => a.used_in.length).length

  return (
    <div className="space-y-6">
      <Card className="p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-2xl">
            <p className="text-base font-medium text-ink">AllocateX as a system of algorithms</p>
            <p className="mt-1 text-sm text-ink-secondary">
              {data.algorithms.length} algorithms, every one hand-built with no graph or string libraries. {usedCount} of them run inside
              the product itself; the rest can be explored on your own input in the Concept Lab. The first design question for any query is
              always the same: which algorithm answers it, and what does it cost?
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3 text-center">
            {[
              [data.algorithms.length, "algorithms"],
              [usedCount, "used in product"],
              [data.algorithms.filter((a) => a.demo).length, "interactive demos"],
            ].map(([v, l]) => (
              <div key={l as string}>
                <p className="text-2xl font-semibold tabular text-ink">{v}</p>
                <p className="text-[11px] text-ink-muted">{l}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="mt-5 overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>The system is asked…</TableHead>
                <TableHead>Algorithm family</TableHead>
                <TableHead>Cost</TableHead>
                <TableHead className="text-right">See it</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {QUERY_MAP.map((row) => (
                <TableRow key={row.query}>
                  <TableCell className="text-ink">{row.query}</TableCell>
                  <TableCell>{row.family}</TableCell>
                  <TableCell className="font-mono text-[11px] text-brand-400">{row.cost}</TableCell>
                  <TableCell className="text-right">
                    <Link to={row.where} className="inline-flex items-center gap-1 text-xs text-brand-400 hover:underline">
                      open <ArrowUpRight className="h-3 w-3" />
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </Card>

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-ink-muted" />
          <Input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Filter by name, category, complexity…" className="w-72 pl-8" />
        </div>
        <button
          onClick={() => setModule(null)}
          className={cn("rounded-full border px-3 py-1 text-xs", module == null ? "border-brand-500/50 bg-brand-500/10 text-ink" : "border-border-subtle text-ink-muted hover:text-ink")}
        >
          All modules
        </button>
        {data.modules
          .filter((m) => m.id > 1)
          .map((m) => (
            <button
              key={m.id}
              onClick={() => setModule(m.id)}
              className={cn("rounded-full border px-3 py-1 text-xs", module === m.id ? "border-brand-500/50 bg-brand-500/10 text-ink" : "border-border-subtle text-ink-muted hover:text-ink")}
            >
              M{m.id} · {m.title}
            </button>
          ))}
      </div>

      {data.modules
        .filter((m) => m.id > 1 && (module == null || module === m.id))
        .map((m) => {
          const algos = visible.filter((a) => a.module === m.id)
          if (!algos.length) return null
          return (
            <section key={m.id} className="space-y-3">
              <div>
                <p className="text-sm font-medium text-ink">Module {m.id} · {m.title}</p>
                <p className="text-xs text-ink-muted">{m.summary}</p>
              </div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
                {algos.map((a) => <AlgorithmCard key={a.id} algo={a} />)}
              </div>
            </section>
          )
        })}
      {!visible.length && <p className="py-10 text-center text-sm text-ink-muted">No algorithm matches that filter.</p>}
    </div>
  )
}

function AlgorithmCard({ algo }: { algo: AtlasAlgorithm }) {
  return (
    <Card className="flex h-full flex-col p-4">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium text-ink">{algo.name}</p>
        <Badge variant="secondary" className="shrink-0 text-[10px]">{algo.category}</Badge>
      </div>
      <p className="mt-1 font-mono text-[11px] text-brand-400">{algo.time_complexity}</p>
      <p className="font-mono text-[10px] text-ink-muted">space {algo.space_complexity}</p>
      <p className="mt-2 flex-1 text-xs text-ink-secondary">{algo.summary}</p>
      <div className="mt-3 space-y-1.5">
        {algo.used_in.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {algo.used_in.map((u) => (
              <Link key={u.label} to={u.path}>
                <Badge variant="success" className="text-[10px] hover:brightness-125">
                  used in · {u.label}
                </Badge>
              </Link>
            ))}
          </div>
        ) : (
          <p className="text-[10px] text-ink-muted">Concept demo only</p>
        )}
        <div className="flex items-center justify-between">
          <code className="truncate text-[10px] text-ink-muted" title={algo.source}>{algo.source.replace("backend/app/", "")}</code>
          {algo.demo && (
            <Link to={demoLink(algo.demo)} className="flex shrink-0 items-center gap-1 text-[11px] text-brand-400 hover:underline">
              <FlaskConical className="h-3 w-3" /> Try it
            </Link>
          )}
        </div>
      </div>
    </Card>
  )
}
