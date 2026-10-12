import { useState } from "react"
import { toast } from "sonner"
import { GitCompare, Play, TrendingUp, TrendingDown, Minus } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { useLabs } from "@/hooks/useLabs"
import { useSimulateAllocation } from "@/hooks/useAllocation"
import { apiErrorMessage } from "@/lib/api"
import { formatMs, formatPercent } from "@/lib/utils"
import { DEFAULT_ALLOCATION_CONFIG, type AlgorithmName } from "@/types"
import { ALLOCATION_ALGORITHMS } from "@/lib/algorithms"
import { MonteCarloPanel } from "@/components/insights/MonteCarloPanel"

export default function WhatIfSimulatorPage() {
  const { data: labs } = useLabs()
  const [algorithm, setAlgorithm] = useState<AlgorithmName>("HOPCROFT_KARP")
  const [labId, setLabId] = useState<string>("")
  const [newCapacity, setNewCapacity] = useState(30)
  const [extraStudents, setExtraStudents] = useState(0)
  const [requirePreference, setRequirePreference] = useState(false)

  const simulate = useSimulateAllocation()

  async function onRun() {
    try {
      await simulate.mutateAsync({
        algorithm,
        baseline_config: DEFAULT_ALLOCATION_CONFIG,
        modified_config: { ...DEFAULT_ALLOCATION_CONFIG, require_preference: requirePreference },
        lab_capacity_overrides: labId ? { [Number(labId)]: newCapacity } : {},
        extra_student_count: extraStudents,
      })
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  const result = simulate.data

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>What-If Configuration</CardTitle>
          <CardDescription>Runs the real matching engine twice — once with today's data, once with your hypothetical change — nothing here is persisted as an official run.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-1">
            <Label>Algorithm</Label>
            <Select value={algorithm} onValueChange={(v) => setAlgorithm(v as AlgorithmName)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>{ALLOCATION_ALGORITHMS.map((a) => <SelectItem key={a.value} value={a.value}>{a.label}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label>Bump capacity for lab</Label>
            <Select value={labId} onValueChange={setLabId}>
              <SelectTrigger><SelectValue placeholder="Choose lab" /></SelectTrigger>
              <SelectContent>
                {labs?.map((l) => <SelectItem key={l.id} value={String(l.id)}>{l.name} (cap {l.capacity})</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label>New capacity</Label>
            <Input type="number" min={0} value={newCapacity} onChange={(e) => setNewCapacity(Number(e.target.value))} disabled={!labId} />
          </div>
          <div className="space-y-1">
            <Label>Extra incoming students</Label>
            <Input type="number" min={0} value={extraStudents} onChange={(e) => setExtraStudents(Number(e.target.value))} />
          </div>
        </CardContent>
        <CardContent className="flex items-center justify-between pt-0">
          <label className="flex items-center gap-2 text-xs text-ink-secondary">
            <input type="checkbox" checked={requirePreference} onChange={(e) => setRequirePreference(e.target.checked)} className="accent-brand-500" />
            "After" scenario requires a stated preference for eligibility
          </label>
          <Button onClick={onRun} disabled={simulate.isPending}>
            <Play className="h-4 w-4" /> {simulate.isPending ? "Simulating..." : "Run Simulation"}
          </Button>
        </CardContent>
      </Card>

      {simulate.isPending ? (
        <Skeleton className="h-64 w-full" />
      ) : result ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><GitCompare className="h-4 w-4" /> Before vs After</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <ScenarioColumn title="Before" metrics={result.before} />
              <ScenarioColumn title="After" metrics={result.after} />
            </div>
            <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-5">
              <DeltaTile label="Matched" value={result.delta.matched_count} />
              <DeltaTile label="Unmatched" value={result.delta.unmatched_count} invert />
              <DeltaTile label="Pref. Satisfaction" value={result.delta.preference_satisfaction} percent />
              <DeltaTile label="Capacity Util." value={result.delta.capacity_utilization} percent />
              <DeltaTile label="Exec. Time (ms)" value={result.delta.execution_time_ms} raw invert />
            </div>
          </CardContent>
        </Card>
      ) : null}

      <MonteCarloPanel />
    </div>
  )
}

function ScenarioColumn({ title, metrics }: { title: string; metrics: { matched_count: number; unmatched_count: number; preference_satisfaction: number; capacity_utilization: number; execution_time_ms: number } }) {
  return (
    <div className="rounded-xl border border-border-subtle bg-white/[0.02] p-4">
      <p className="mb-3 text-sm font-medium text-ink">{title}</p>
      <dl className="space-y-2 text-xs">
        <Row label="Matched" value={String(metrics.matched_count)} />
        <Row label="Unmatched" value={String(metrics.unmatched_count)} />
        <Row label="Preference Satisfaction" value={formatPercent(metrics.preference_satisfaction)} />
        <Row label="Capacity Utilization" value={formatPercent(metrics.capacity_utilization)} />
        <Row label="Execution Time" value={formatMs(metrics.execution_time_ms)} />
      </dl>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <dt className="text-ink-muted">{label}</dt>
      <dd className="tabular text-ink">{value}</dd>
    </div>
  )
}

function DeltaTile({ label, value, percent, invert, raw }: { label: string; value: number; percent?: boolean; invert?: boolean; raw?: boolean }) {
  const positive = invert ? value < 0 : value > 0
  const neutral = value === 0
  const Icon = neutral ? Minus : positive ? TrendingUp : TrendingDown
  const color = neutral ? "text-ink-muted" : positive ? "text-good" : "text-critical"
  const display = percent ? formatPercent(Math.abs(value)) : raw ? `${Math.abs(value).toFixed(3)}ms` : Math.abs(value)
  return (
    <div className="rounded-lg border border-border-subtle bg-white/[0.02] p-3 text-center">
      <p className="text-[10px] uppercase tracking-wide text-ink-muted">{label}</p>
      <p className={`mt-1 flex items-center justify-center gap-1 text-sm font-medium tabular ${color}`}>
        <Icon className="h-3.5 w-3.5" /> {value >= 0 && !neutral ? "+" : neutral ? "" : "-"}{display}
      </p>
    </div>
  )
}
