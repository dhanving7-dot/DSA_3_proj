import { useMemo, useState } from "react"
import { Search, Share2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/common/EmptyState"
import { BipartiteFlowGraph } from "@/components/graph/BipartiteFlowGraph"
import { useAllocationRuns, useAllocationRun } from "@/hooks/useAllocation"
import { useStudents } from "@/hooks/useStudents"
import { useLabs } from "@/hooks/useLabs"

export default function GraphVisualizationPage() {
  const [search, setSearch] = useState("")
  const [highlightId, setHighlightId] = useState<string | null>(null)
  const { data: runs } = useAllocationRuns()
  const latestRunId = runs?.[0]?.id ?? null
  const { data: run, isLoading: runLoading } = useAllocationRun(latestRunId)
  const { data: students, isLoading: studentsLoading } = useStudents()
  const { data: labs, isLoading: labsLoading } = useLabs()

  const isLoading = runLoading || studentsLoading || labsLoading

  const MAX_VISIBLE_STUDENTS = 40

  const { leftItems, rightItems, edges, truncated } = useMemo(() => {
    const matchedIds = (run?.allocations ?? []).filter((a) => a.status === "MATCHED").map((a) => a.student_id)
    const matchedStudents = (students ?? []).filter((s) => matchedIds.includes(s.id))
    const pool = search.trim() ? (students ?? []) : matchedStudents
    const relevantStudents = pool.slice(0, MAX_VISIBLE_STUDENTS)
    const left = relevantStudents.map((s) => ({ id: s.id, label: s.full_name, sublabel: `${s.department} · Y${s.year}` }))
    const right = (labs ?? []).map((l) => ({ id: l.id, label: l.name, sublabel: `${l.department} · cap ${l.capacity}` }))
    const graphEdges = (run?.allocations ?? [])
      .filter((a) => a.lab_id != null && relevantStudents.some((s) => s.id === a.student_id))
      .map((a) => ({ source: a.student_id, target: a.lab_id as number, matched: true }))
    return { leftItems: left, rightItems: right, edges: graphEdges, truncated: pool.length > MAX_VISIBLE_STUDENTS }
  }, [run, students, labs, search])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div className="relative w-72">
          <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-muted" />
          <Input placeholder="Search student or lab..." className="pl-8" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        {run && <Badge variant="secondary">Run #{run.id} · {run.algorithm}</Badge>}
      </div>

      {isLoading ? (
        <Skeleton className="h-[560px] w-full" />
      ) : !run ? (
        <EmptyState icon={Share2} title="No allocation run yet" description="Run an allocation from Allocation Config to visualize the resulting bipartite graph here." />
      ) : (
        <Card className="p-2">
          <CardHeader>
            <CardTitle>Final Matching Graph</CardTitle>
            <CardDescription>
              Green edges are matched student→lab pairs from run #{run.id}. Drag to pan, scroll to zoom, click a node to highlight its edges.
              {truncated && " Showing a subset — use search to bring a specific student or lab into view."}
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <BipartiteFlowGraph
              leftItems={leftItems}
              rightItems={rightItems}
              edges={edges}
              searchTerm={search}
              height={680}
              showMiniMap
              highlightId={highlightId}
              onNodeClick={(id) => setHighlightId((prev) => (prev === id ? null : id))}
            />
          </CardContent>
        </Card>
      )}
    </div>
  )
}
