import { useState } from "react"
import { toast } from "sonner"
import { ClipboardList, GitCompare, Sparkles, Shuffle } from "lucide-react"
import { Input } from "@/components/ui/input"
import { useAuditSample } from "@/hooks/useInsights"
import { ALGORITHM_LABELS } from "@/lib/algorithms"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/common/EmptyState"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { useAllocationRun, useAllocationRuns, useCompareAlgorithms } from "@/hooks/useAllocation"
import { useAIExplain } from "@/hooks/useAI"
import { useStudents } from "@/hooks/useStudents"
import { useLabs } from "@/hooks/useLabs"
import { apiErrorMessage } from "@/lib/api"
import { formatMs, formatPercent } from "@/lib/utils"
import { DEFAULT_ALLOCATION_CONFIG, type Allocation } from "@/types"

export default function AllocationResultsPage() {
  const { data: runs, isLoading: runsLoading } = useAllocationRuns()
  const [runId, setRunId] = useState<number | null>(null)
  const [explainTarget, setExplainTarget] = useState<Allocation | null>(null)
  const [compareOpen, setCompareOpen] = useState(false)

  const activeRunId = runId ?? runs?.[0]?.id ?? null
  const { data: run, isLoading: runLoading } = useAllocationRun(activeRunId)
  const { data: students } = useStudents()
  const { data: labs } = useLabs()
  const explain = useAIExplain()
  const compare = useCompareAlgorithms()
  const audit = useAuditSample()
  const [auditK, setAuditK] = useState(8)

  async function onAudit() {
    try {
      // a fresh seed each click: every draw is an independent uniform sample
      await audit.mutateAsync({ run_id: activeRunId, k: auditK, seed: Math.floor(Math.random() * 1_000_000) })
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  function studentLabel(id: number) {
    const s = students?.find((s) => s.id === id)
    return s ? `${s.full_name} (${s.roll_number})` : `Student #${id}`
  }
  function labLabel(id: number | null) {
    if (id == null) return "—"
    return labs?.find((l) => l.id === id)?.name ?? `Lab #${id}`
  }

  async function onExplain(allocation: Allocation) {
    setExplainTarget(allocation)
    try {
      await explain.mutateAsync({ allocation_id: allocation.id })
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  async function onCompare() {
    setCompareOpen(true)
    try {
      await compare.mutateAsync({ config: DEFAULT_ALLOCATION_CONFIG })
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  if (runsLoading) return <Skeleton className="h-96 w-full" />
  if (!runs?.length) {
    return <EmptyState icon={ClipboardList} title="No allocation results yet" description="Generate an allocation from Allocation Config to see results here." />
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Select value={String(activeRunId)} onValueChange={(v) => setRunId(Number(v))}>
          <SelectTrigger className="w-64"><SelectValue /></SelectTrigger>
          <SelectContent>
            {runs.map((r) => (
              <SelectItem key={r.id} value={String(r.id)}>
                Run #{r.id} · {r.algorithm} · {new Date(r.created_at).toLocaleString()}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button variant="secondary" size="sm" onClick={onCompare}>
          <GitCompare className="h-3.5 w-3.5" /> Compare All Algorithms
        </Button>
      </div>

      {runLoading || !run ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Card className="p-4"><p className="text-xs text-ink-muted">Algorithm</p><p className="mt-1 font-medium text-ink">{run.algorithm}</p></Card>
            <Card className="p-4"><p className="text-xs text-ink-muted">Matched / Total</p><p className="mt-1 tabular font-medium text-ink">{run.matched_count} / {run.total_students}</p></Card>
            <Card className="p-4"><p className="text-xs text-ink-muted">Preference Satisfaction</p><p className="mt-1 tabular font-medium text-ink">{formatPercent(run.preference_satisfaction)}</p></Card>
            <Card className="p-4"><p className="text-xs text-ink-muted">Execution Time</p><p className="mt-1 tabular font-medium text-ink">{formatMs(run.execution_time_ms)}</p></Card>
          </div>

          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <CardTitle className="flex items-center gap-2"><Shuffle className="h-4 w-4" /> Audit sample (reservoir sampling)</CardTitle>
                  <CardDescription className="mt-1 max-w-2xl">
                    Streams this run&apos;s allocations from the database once and keeps a uniform random sample of k rows in O(k) memory
                    (Algorithm R): every allocation has exactly the same k/n chance of being audited, without loading the run into memory.
                  </CardDescription>
                </div>
                <div className="flex items-end gap-2">
                  <label className="flex flex-col gap-1 text-xs text-ink-muted">
                    k
                    <Input type="number" min={1} max={100} value={auditK} onChange={(e) => setAuditK(Number(e.target.value))} className="w-20" />
                  </label>
                  <Button size="sm" variant="secondary" onClick={onAudit} disabled={audit.isPending}>
                    <Shuffle className="h-3.5 w-3.5" /> {audit.isPending ? "Sampling..." : "Draw sample"}
                  </Button>
                </div>
              </div>
            </CardHeader>
            {audit.data && (
              <CardContent className="space-y-2">
                <p className="text-xs text-ink-muted">
                  Run #{audit.data.run_id}: streamed {audit.data.items_seen} rows, kept {audit.data.sample.length}; each row&apos;s inclusion probability = {formatPercent(audit.data.inclusion_probability)}.
                </p>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Student</TableHead>
                      <TableHead>Laboratory</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Recorded reason</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {audit.data.sample.map((row) => (
                      <TableRow key={row.allocation_id}>
                        <TableCell className="text-ink">{row.student}</TableCell>
                        <TableCell>{row.lab ?? "—"}</TableCell>
                        <TableCell><Badge variant={row.status === "MATCHED" ? "success" : "critical"}>{row.status}</Badge></TableCell>
                        <TableCell className="max-w-md text-xs text-ink-muted">{row.reason}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            )}
          </Card>

          <Card>
            <CardHeader><CardTitle>Assignments</CardTitle></CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Student</TableHead>
                    <TableHead>Assigned Laboratory</TableHead>
                    <TableHead>Preference Rank</TableHead>
                    <TableHead>Match Score</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Explain</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {run.allocations.map((a) => (
                    <TableRow key={a.id}>
                      <TableCell className="text-ink">{studentLabel(a.student_id)}</TableCell>
                      <TableCell>{labLabel(a.lab_id)}</TableCell>
                      <TableCell>{a.preference_rank ? `#${a.preference_rank}` : "—"}</TableCell>
                      <TableCell className="tabular">{a.match_score.toFixed(3)}</TableCell>
                      <TableCell>
                        <Badge variant={a.status === "MATCHED" ? "success" : "critical"}>{a.status}</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button size="sm" variant="ghost" onClick={() => onExplain(a)}>
                          <Sparkles className="h-3.5 w-3.5" /> Why?
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}

      <Dialog open={!!explainTarget} onOpenChange={(open) => !open && setExplainTarget(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>Allocation Explanation</DialogTitle></DialogHeader>
          {explain.isPending ? (
            <Skeleton className="h-24 w-full" />
          ) : explain.data ? (
            <div className="space-y-3">
              <p className="text-sm text-ink-secondary">{explain.data.explanation}</p>
              <div className="rounded-lg border border-border-subtle bg-white/[0.02] p-3 text-xs">
                <pre className="whitespace-pre-wrap text-ink-muted">{JSON.stringify(explain.data.facts, null, 2)}</pre>
              </div>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      <Dialog open={compareOpen} onOpenChange={setCompareOpen}>
        <DialogContent className="max-w-4xl">
          <DialogHeader><DialogTitle>Algorithm Comparison (same input graph)</DialogTitle></DialogHeader>
          <p className="text-xs text-ink-muted">
            All algorithms solve the same maximum-flow problem, so the matched count is identical; total score shows which maximum matching
            each one happened to return. Only min-cost flow guarantees the highest.
          </p>
          {compare.isPending ? (
            <Skeleton className="h-48 w-full" />
          ) : compare.data ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Algorithm</TableHead>
                  <TableHead>Matched</TableHead>
                  <TableHead>Total score</TableHead>
                  <TableHead>Vertices/Edges</TableHead>
                  <TableHead>Iterations</TableHead>
                  <TableHead>Time</TableHead>
                  <TableHead>Complexity</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {compare.data.map((row) =>
                  row.skipped_reason ? (
                    <TableRow key={row.algorithm}>
                      <TableCell className="text-ink">{ALGORITHM_LABELS[row.algorithm] ?? row.algorithm}</TableCell>
                      <TableCell colSpan={6} className="text-xs text-ink-muted">skipped - {row.skipped_reason}</TableCell>
                    </TableRow>
                  ) : (
                    <TableRow key={row.algorithm}>
                      <TableCell className="text-ink">{ALGORITHM_LABELS[row.algorithm] ?? row.algorithm}</TableCell>
                      <TableCell className="tabular">{row.matched_count}</TableCell>
                      <TableCell className="tabular">{row.total_score?.toFixed(2) ?? "—"}</TableCell>
                      <TableCell className="tabular">{row.vertices}/{row.edges}</TableCell>
                      <TableCell className="tabular">{row.iterations}</TableCell>
                      <TableCell className="tabular">{formatMs(row.execution_time_ms ?? 0)}</TableCell>
                      <TableCell className="font-mono text-[11px] text-brand-400">{row.time_complexity}</TableCell>
                    </TableRow>
                  )
                )}
              </TableBody>
            </Table>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  )
}
