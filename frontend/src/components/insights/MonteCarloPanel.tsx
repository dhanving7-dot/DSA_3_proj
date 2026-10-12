import { useState } from "react"
import { toast } from "sonner"
import { Dices } from "lucide-react"
import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { MetricTile } from "@/components/concepts/DemoCard"
import { useMonteCarlo } from "@/hooks/useInsights"
import { ALLOCATION_ALGORITHMS } from "@/lib/algorithms"
import { apiErrorMessage } from "@/lib/api"
import { CHART_CHROME, SERIES } from "@/lib/chartTheme"
import { formatMs, formatPercent } from "@/lib/utils"

/** Monte Carlo risk estimate: random lab outages, re-run the real engine, report a confidence interval. */
export function MonteCarloPanel() {
  const [trials, setTrials] = useState(100)
  const [p, setP] = useState(0.1)
  const [algorithm, setAlgorithm] = useState("HOPCROFT_KARP")
  const [seed, setSeed] = useState(2024)
  const mc = useMonteCarlo()
  const data = mc.data
  // every integer from the lowest outcome up to the no-outage baseline, so gaps and the baseline marker are always visible
  const histogram = data
    ? Array.from({ length: data.baseline_matched - Math.min(data.min_matched, data.baseline_matched) + 1 }, (_, i) => {
        const matched = Math.min(data.min_matched, data.baseline_matched) + i
        return { matched, trials: data.histogram.find((h) => h.matched === matched)?.trials ?? 0 }
      })
    : []

  async function onRun() {
    try {
      await mc.mutateAsync({ trials, outage_probability: p, seed, algorithm })
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2"><Dices className="h-4 w-4" /> Outage risk - Monte Carlo simulation</CardTitle>
        <CardDescription className="max-w-4xl leading-relaxed">
          Each trial takes every active lab offline independently with probability p and re-runs the real allocation engine. This is a
          <strong className="text-ink-secondary"> Monte Carlo</strong> method: the running time is fixed (trials × one allocation) and the
          answer is an estimate whose error shrinks like 1/√trials - unlike the Las Vegas algorithms elsewhere, which are always exact and
          only random in how long they take. The same seed always reproduces the same trials.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-xs text-ink-muted">
            Trials (2-300)
            <Input type="number" min={2} max={300} value={trials} onChange={(e) => setTrials(Number(e.target.value))} className="w-24" />
          </label>
          <label className="flex flex-col gap-1 text-xs text-ink-muted">
            Outage probability p
            <Input type="number" min={0} max={1} step={0.05} value={p} onChange={(e) => setP(Number(e.target.value))} className="w-28" />
          </label>
          <label className="flex flex-col gap-1 text-xs text-ink-muted">
            Algorithm
            <Select value={algorithm} onValueChange={setAlgorithm}>
              <SelectTrigger className="w-48"><SelectValue /></SelectTrigger>
              <SelectContent>{ALLOCATION_ALGORITHMS.map((a) => <SelectItem key={a.value} value={a.value}>{a.label}</SelectItem>)}</SelectContent>
            </Select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-ink-muted">
            Seed
            <Input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} className="w-24" />
          </label>
          <Button onClick={onRun} disabled={mc.isPending}>
            <Dices className="h-4 w-4" /> {mc.isPending ? "Simulating..." : "Run trials"}
          </Button>
        </div>

        {mc.isPending ? (
          <Skeleton className="h-64 w-full" />
        ) : data ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
              <MetricTile label="No outages" value={data.baseline_matched} hint="placements today" />
              <MetricTile label="Expected placements" value={data.mean_matched} tone="brand" />
              <MetricTile label="95% confidence interval" value={`${data.ci95[0]} – ${data.ci95[1]}`} hint="mean ± 1.96·s/√trials" />
              <MetricTile label="Std. deviation" value={data.std_matched} hint={`range ${data.min_matched}–${data.max_matched}`} />
              <MetricTile label="Simulation time" value={formatMs(data.execution_time_ms)} hint={`${data.trials} allocations`} />
            </div>
            <div>
              <p className="mb-1 text-xs font-medium text-ink-secondary">Placements per trial</p>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={histogram} margin={{ top: 12, right: 8, left: -12, bottom: 0 }}>
                  <CartesianGrid stroke={CHART_CHROME.gridline} vertical={false} />
                  <XAxis dataKey="matched" tick={{ fill: CHART_CHROME.textMuted, fontSize: 10 }} axisLine={{ stroke: CHART_CHROME.baseline }} tickLine={false} />
                  <YAxis allowDecimals={false} tick={{ fill: CHART_CHROME.textMuted, fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip
                    cursor={{ fill: "rgba(255,255,255,0.04)" }}
                    content={({ active, payload }) =>
                      active && payload?.length ? (
                        <div className="rounded-lg glass-panel-strong px-3 py-2 text-xs text-ink-secondary">
                          <span className="tabular text-ink">{payload[0].payload.trials}</span> trial(s) placed{" "}
                          <span className="tabular text-ink">{payload[0].payload.matched}</span> students
                        </div>
                      ) : null
                    }
                  />
                  <ReferenceLine
                    x={data.baseline_matched}
                    stroke={CHART_CHROME.textSecondary}
                    strokeDasharray="4 4"
                    label={{ value: "no outages", fill: CHART_CHROME.textSecondary, fontSize: 10, position: "insideTopRight" }}
                  />
                  <Bar dataKey="trials" fill={SERIES.blue} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <div>
                <p className="mb-2 text-xs font-medium text-ink-secondary">Most critical labs (expected loss when that lab is down)</p>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Lab</TableHead>
                      <TableHead>Trials down</TableHead>
                      <TableHead>Placements lost</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.lab_criticality.slice(0, 8).map((l) => (
                      <TableRow key={l.lab_id}>
                        <TableCell className="text-ink">{l.lab_name}</TableCell>
                        <TableCell className="tabular">{l.trials_down}</TableCell>
                        <TableCell className="tabular text-critical">{l.loss_vs_baseline}</TableCell>
                      </TableRow>
                    ))}
                    {data.lab_criticality.length === 0 && (
                      <TableRow><TableCell colSpan={3} className="text-xs text-ink-muted">No lab went down in any trial - raise p.</TableCell></TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
              <div>
                <p className="mb-2 text-xs font-medium text-ink-secondary">
                  Placed today, displaced by outages ({data.students_ever_displaced} student{data.students_ever_displaced === 1 ? "" : "s"} affected in at least one trial)
                </p>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Student</TableHead>
                      <TableHead>P(unplaced)</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.at_risk_students.slice(0, 8).map((s) => (
                      <TableRow key={s.student_id}>
                        <TableCell className="text-ink">{s.student}</TableCell>
                        <TableCell className="tabular">{formatPercent(s.p_unmatched)}</TableCell>
                      </TableRow>
                    ))}
                    {data.at_risk_students.length === 0 && (
                      <TableRow><TableCell colSpan={2} className="text-xs text-ink-muted">No placed student lost their seat in any trial.</TableCell></TableRow>
                    )}
                  </TableBody>
                </Table>
                <p className="mt-1 text-[11px] text-ink-muted">
                  Not listed: {data.never_placeable} student(s) who are unplaced even with every lab open - outages cannot change their outcome.
                </p>
              </div>
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
