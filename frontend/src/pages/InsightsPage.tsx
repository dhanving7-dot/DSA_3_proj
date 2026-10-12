import { useEffect } from "react"
import { Link, useLocation } from "react-router-dom"
import { AlertTriangle, CheckCircle2, FlaskConical } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { MetricTile, Verified } from "@/components/concepts/DemoCard"
import { useBottleneck, useOptimalityGap, useSetCover, useSkillSupply } from "@/hooks/useInsights"
import { ALGORITHM_LABELS } from "@/lib/algorithms"
import { ALGORITHM_COLORS } from "@/lib/chartTheme"
import { formatMs, formatPercent } from "@/lib/utils"

export default function InsightsPage() {
  const location = useLocation()
  useEffect(() => {
    if (!location.hash) return
    const id = location.hash.slice(1)
    const timer = window.setTimeout(() => document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" }), 250)
    return () => window.clearTimeout(timer)
  }, [location.hash])

  return (
    <div className="space-y-4">
      <p className="max-w-3xl text-sm text-ink-secondary">
        Advanced algorithms answering questions about <em>your</em> data. Every figure is recomputed from the current students and labs,
        using the configuration of the latest allocation run (or the defaults if none exists).
      </p>
      <BottleneckSection />
      <OptimalitySection />
      <SetCoverSection />
      <SkillSupplySection />
    </div>
  )
}

function SectionHeader({ title, description, demo }: { title: string; description: string; demo?: string }) {
  return (
    <CardHeader>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <CardTitle className="text-base text-ink">{title}</CardTitle>
        {demo && (
          <Link to={demo} className="flex items-center gap-1 text-xs text-brand-400 hover:underline">
            <FlaskConical className="h-3.5 w-3.5" /> concept demo
          </Link>
        )}
      </div>
      <CardDescription className="max-w-4xl leading-relaxed">{description}</CardDescription>
    </CardHeader>
  )
}

// --------------------------------------------------------------------------- bottleneck

function BottleneckSection() {
  const { data, isLoading } = useBottleneck()
  return (
    <Card id="bottleneck" className="scroll-mt-24">
      <SectionHeader
        title="Why can't everyone be placed? Min cut · Hall · König"
        description="Dinic computes the maximum flow, then the students and labs still reachable from the source in the residual graph form a minimum cut. Those students are a Hall violator: together they need more seats than all of their eligible labs offer. That set is the proof that no algorithm, however clever, could place more students."
        demo="/app/concepts?tab=flow#mincut"
      />
      <CardContent>
        {isLoading || !data ? (
          <Skeleton className="h-40 w-full" />
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              <MetricTile label="Maximum placements" value={`${data.max_flow} / ${data.total_students}`} tone="brand" />
              <MetricTile label="Minimum cut capacity" value={data.min_cut_capacity} hint="equals the max flow" />
              <MetricTile label="Hall violator set" value={`${data.hall.violator_size} students`} hint={`share only ${data.hall.reachable_capacity} reachable seats`} />
              <MetricTile label="Deficiency" value={data.hall.deficiency} hint="= students that cannot be placed" tone={data.hall.deficiency ? "critical" : "good"} />
            </div>
            <Verified ok={data.max_flow_equals_min_cut}>
              Max-flow min-cut theorem holds on your data: {data.max_flow} = {data.min_cut_capacity}. König: minimum vertex cover = {data.konig.students_in_cover} students + {data.konig.lab_seats_in_cover} lab seats = {data.konig.min_vertex_cover} = maximum matching.
            </Verified>
            {data.unmatched === 0 ? (
              <p className="flex items-center gap-2 text-sm text-good"><CheckCircle2 className="h-4 w-4" /> Every student can be placed - Hall's condition holds for every subset.</p>
            ) : data.bottleneck_labs.length === 0 && data.binding_quotas.length === 0 ? (
              <div className="flex gap-2 rounded-lg border border-warning/30 bg-warning/[0.06] p-3 text-xs text-ink-secondary">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
                <div>
                  <p className="font-medium text-ink">The binding constraint is eligibility, not capacity.</p>
                  <p className="mt-1">
                    No lab is saturated in the cut: all {data.hall.deficiency} unplaced students have no eligible lab at all
                    ({data.hall.students_with_no_eligible_lab} have zero eligible edges). Adding seats would not help - relaxing skill
                    requirements or department rules would. Try it in the What-If Simulator.
                  </p>
                </div>
              </div>
            ) : (
              <div className="grid gap-4 lg:grid-cols-2">
                <div>
                  <p className="mb-2 text-xs font-medium text-ink-secondary">Saturated labs in the cut (the real bottleneck)</p>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Lab</TableHead>
                        <TableHead>Capacity</TableHead>
                        <TableHead>Students competing</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {data.bottleneck_labs.map((b) => (
                        <TableRow key={b.lab_id}>
                          <TableCell className="text-ink">{b.lab_name}</TableCell>
                          <TableCell className="tabular">{b.capacity}</TableCell>
                          <TableCell className="tabular">{b.students_competing}</TableCell>
                        </TableRow>
                      ))}
                      {data.binding_quotas.map((q, i) => (
                        <TableRow key={`q${i}`}>
                          <TableCell className="text-ink">{q.lab_name} <Badge variant="warning" className="ml-1 text-[10px]">{q.department} quota</Badge></TableCell>
                          <TableCell className="tabular">{q.quota}</TableCell>
                          <TableCell className="tabular">—</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
                <div>
                  <p className="mb-2 text-xs font-medium text-ink-secondary">Hall violator set by department</p>
                  <DepartmentBars counts={data.hall.by_department} />
                </div>
              </div>
            )}
            {data.bottleneck_labs.length === 0 && data.binding_quotas.length === 0 && data.unmatched > 0 && (
              <div>
                <p className="mb-2 text-xs font-medium text-ink-secondary">Unplaceable students by department</p>
                <DepartmentBars counts={data.hall.by_department} />
              </div>
            )}
            <p className="text-[11px] text-ink-muted">Computed in {formatMs(data.execution_time_ms)}{data.config_from_run ? ` using the configuration of run #${data.config_from_run}` : " using the default configuration"}.</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function DepartmentBars({ counts }: { counts: Record<string, number> }) {
  const entries = Object.entries(counts)
  const max = Math.max(1, ...entries.map(([, v]) => v))
  return (
    <div className="space-y-1.5">
      {entries.map(([dept, v]) => (
        <div key={dept} className="flex items-center gap-2 text-xs">
          <span className="w-12 text-ink-secondary">{dept}</span>
          <span className="h-3 flex-1 rounded-sm bg-white/[0.04]">
            <span className="block h-3 rounded-sm bg-series-blue" style={{ width: `${(v / max) * 100}%` }} />
          </span>
          <span className="w-8 text-right tabular text-ink">{v}</span>
        </div>
      ))}
    </div>
  )
}

// --------------------------------------------------------------------------- optimality

function OptimalitySection() {
  const { data, isLoading } = useOptimalityGap()
  const max = data ? Math.max(...data.algorithms.map((a) => a.total_score), 1) : 1
  return (
    <Card id="optimality" className="scroll-mt-24">
      <SectionHeader
        title="Same size, different quality: the optimality gap"
        description="Every max-flow and matching algorithm reaches the same maximum number of placements - they solve the same problem. But a maximum matching is rarely unique, and which one you get depends on search order. Only min-cost max-flow is guaranteed to return the maximum matching with the highest total preference/skill/priority score."
        demo="/app/concepts?tab=flow#mincost"
      />
      <CardContent>
        {isLoading || !data ? (
          <Skeleton className="h-40 w-full" />
        ) : (
          <div className="space-y-3">
            <Verified ok={data.same_cardinality}>All algorithms place the same number of students.</Verified>
            {data.skipped.length > 0 && <p className="text-xs text-ink-muted">Skipped (cannot express the active fairness cap): {data.skipped.join(", ")}</p>}
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Algorithm</TableHead>
                  <TableHead>Placed</TableHead>
                  <TableHead>Total score</TableHead>
                  <TableHead>Gap to optimal</TableHead>
                  <TableHead>#1 choices</TableHead>
                  <TableHead>Placed differently</TableHead>
                  <TableHead>Time</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.algorithms.map((a) => (
                  <TableRow key={a.algorithm}>
                    <TableCell className="text-ink">
                      <span className="mr-2 inline-block h-2.5 w-2.5 rounded-sm" style={{ background: ALGORITHM_COLORS[a.algorithm] }} />
                      {ALGORITHM_LABELS[a.algorithm] ?? a.algorithm}
                    </TableCell>
                    <TableCell className="tabular">{a.matched}</TableCell>
                    <TableCell className="tabular">
                      {a.total_score.toFixed(2)}
                      <span className="mt-1 block h-1.5 w-28 rounded-full bg-white/[0.06]">
                        <span className="block h-1.5 rounded-full bg-series-blue" style={{ width: `${(a.total_score / max) * 100}%` }} />
                      </span>
                    </TableCell>
                    <TableCell className={`tabular ${a.gap_to_optimal > 1e-6 ? "text-critical" : "text-good"}`}>{a.gap_to_optimal > 1e-6 ? `−${a.gap_to_optimal.toFixed(2)}` : "optimal"}</TableCell>
                    <TableCell className="tabular">{a.rank_distribution["#1"] ?? 0}</TableCell>
                    <TableCell className="tabular">{a.students_placed_differently}</TableCell>
                    <TableCell className="tabular">{formatMs(a.execution_time_ms)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <p className="text-[11px] text-ink-muted">
              "Placed differently" counts students whose lab differs from the min-cost solution. A difference with zero score gap means the two
              matchings tie - both are optimal.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// --------------------------------------------------------------------------- set cover

function SetCoverSection() {
  const { data, isLoading } = useSetCover()
  return (
    <Card id="setcover" className="scroll-mt-24">
      <SectionHeader
        title="Which labs must stay open? Set cover"
        description="Each lab covers the students eligible for it. Keeping every placeable student placeable with as few labs as possible is set cover - NP-hard. Greedy (most uncovered students first) is within H(n) of optimal; with a handful of labs the exact answer is still affordable by a subset DP over all 2ᵏ lab combinations, so we can measure the real ratio."
        demo="/app/concepts?tab=np#setcover"
      />
      <CardContent>
        {isLoading || !data ? (
          <Skeleton className="h-40 w-full" />
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              <MetricTile label="Placeable students" value={data.placeable_students} hint={`${data.students_with_no_eligible_lab} have no eligible lab`} />
              <MetricTile label="Greedy cover" value={`${data.greedy.size} labs`} hint={formatMs(data.greedy.time_ms)} />
              <MetricTile label="Exact cover" value={data.exact ? `${data.exact.size} labs` : "—"} hint={data.exact ? `${data.exact.subsets_evaluated.toLocaleString()} subsets · ${formatMs(data.exact.time_ms)}` : "too many labs"} tone="brand" />
              <MetricTile label="Ratio vs H(n)" value={data.approximation_ratio != null ? `${data.approximation_ratio}× vs ${data.harmonic_bound}×` : "—"} />
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <div>
                <p className="mb-2 text-xs font-medium text-ink-secondary">Greedy pick order</p>
                <ol className="space-y-1 text-xs">
                  {data.greedy.labs.map((l, i) => (
                    <li key={l.lab_id} className="flex justify-between rounded-md border border-border-subtle px-3 py-1.5">
                      <span className="text-ink">{i + 1}. {l.lab_name}</span>
                      <span className="tabular text-ink-muted">+{data.greedy.new_students_per_pick[i]} new students</span>
                    </li>
                  ))}
                </ol>
              </div>
              <div>
                <p className="mb-2 text-xs font-medium text-ink-secondary">Essential labs (some student is eligible nowhere else)</p>
                {data.essential_labs.length === 0 ? (
                  <p className="text-xs text-ink-muted">None - every student has an alternative lab.</p>
                ) : (
                  <ul className="space-y-1 text-xs">
                    {data.essential_labs.map((l) => (
                      <li key={l.lab_id} className="flex justify-between rounded-md border border-border-subtle px-3 py-1.5">
                        <span className="text-ink">{l.lab_name}</span>
                        <span className="tabular text-warning">{l.students_only_eligible_here} only here</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// --------------------------------------------------------------------------- skill supply (SOS DP)

function SkillSupplySection() {
  const { data, isLoading } = useSkillSupply()
  const maxPair = data ? Math.max(1, ...data.pair_matrix.flat()) : 1
  return (
    <Card id="skills" className="scroll-mt-24">
      <SectionHeader
        title="Skill supply: sum over subsets (SOS) DP"
        description="Each lab requirement (skill ≥ level) is one bit. A student is a bitmask of the requirements they meet. SOS DP turns the 'how many students have exactly this mask' table into 'how many students meet at least these requirements' for all 2ᵏ combinations at once in O(k·2ᵏ), instead of re-scanning every student per lab. Each lab's count is checked against a brute-force scan."
      />
      <CardContent>
        {isLoading || !data ? (
          <Skeleton className="h-40 w-full" />
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              <MetricTile label="Requirement bits k" value={data.k} hint={`${data.masks.toLocaleString()} combinations`} />
              <MetricTile label="SOS operations" value={data.sos_operations.toLocaleString()} hint={formatMs(data.sos_time_ms)} />
              <MetricTile label="Brute-force checks" value={data.bruteforce_operations.toLocaleString()} hint="for the per-lab answers only" />
              <MetricTile label="Meet no requirement" value={`${data.qualified_for_none} / ${data.students}`} hint={formatPercent(data.qualified_for_none / Math.max(data.students, 1))} />
            </div>
            <Verified ok={data.per_lab.every((l) => l.qualified_sos == null || l.qualified_sos === l.qualified_bruteforce)}>
              SOS answer equals the brute-force count for every lab.
            </Verified>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Lab</TableHead>
                  <TableHead>Requirements</TableHead>
                  <TableHead>Qualified (SOS)</TableHead>
                  <TableHead>Capacity</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.per_lab.map((l) => (
                  <TableRow key={l.lab_id}>
                    <TableCell className="text-ink">{l.lab_name}</TableCell>
                    <TableCell className="text-xs">{l.requirements.join(" ∧ ") || "none"}</TableCell>
                    <TableCell className={`tabular ${l.qualified_bruteforce < l.capacity ? "text-warning" : ""}`}>
                      {l.qualified_sos ?? l.qualified_bruteforce}
                      {l.qualified_bruteforce < l.capacity && <span className="ml-1 text-[10px] text-ink-muted">(fewer than seats)</span>}
                    </TableCell>
                    <TableCell className="tabular">{l.capacity}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <div>
              <p className="mb-2 text-xs font-medium text-ink-secondary">Students meeting both requirements (one SOS lookup per cell; diagonal = single requirement)</p>
              <div className="overflow-auto">
                <table className="text-[10px] tabular">
                  <thead>
                    <tr>
                      <th />
                      {data.items.map((_, j) => <th key={j} className="px-1 py-1 font-normal text-ink-muted">{j + 1}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {data.pair_matrix.map((row, i) => (
                      <tr key={i}>
                        <th className="whitespace-nowrap pr-2 text-right font-normal text-ink-secondary">{i + 1}. {data.items[i]}</th>
                        {row.map((v, j) => (
                          <td
                            key={j}
                            title={`${data.items[i]} ∧ ${data.items[j]}: ${v} students`}
                            className="h-7 w-8 border border-canvas text-center text-ink"
                            style={{ background: `rgba(57, 135, 229, ${0.06 + 0.8 * (v / maxPair)})` }}
                          >
                            {v}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
