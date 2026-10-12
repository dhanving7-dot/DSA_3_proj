import { Link } from "react-router-dom"
import { Users, FlaskConical, CheckCircle2, XCircle, ArrowRight, Scale, BookOpen, FlaskRound } from "lucide-react"
import { StatCard } from "@/components/common/StatCard"
import { ProgressRing } from "@/components/common/ProgressRing"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/common/EmptyState"
import { Button } from "@/components/ui/button"
import { LabUtilizationChart } from "@/components/charts/LabUtilizationChart"
import { DepartmentChart } from "@/components/charts/DepartmentChart"
import { useAnalyticsOverview } from "@/hooks/useAnalytics"
import { useBottleneck } from "@/hooks/useInsights"

export default function DashboardPage() {
  const { data, isLoading } = useAnalyticsOverview()
  const { data: theory } = useBottleneck()

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-28" />
        ))}
      </div>
    )
  }

  const overview = data?.overview
  const hasRun = !!overview?.latest_run_id

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total Students" value={overview?.total_students ?? 0} icon={Users} accent="brand" delay={0} />
        <StatCard label="Total Laboratories" value={overview?.total_labs ?? 0} icon={FlaskConical} accent="violet" delay={0.05} />
        <StatCard label="Matched Students" value={overview?.matched_students ?? 0} icon={CheckCircle2} accent="good" delay={0.1} />
        <StatCard label="Unmatched Students" value={overview?.unmatched_students ?? 0} icon={XCircle} accent="critical" delay={0.15} />
      </div>

      {!hasRun ? (
        <EmptyState
          icon={FlaskConical}
          title="No allocation has been run yet"
          description="Generate an allocation to see live matching, capacity and preference metrics here."
          actionLabel="Go to Allocation Config"
        />
      ) : (
        <>
          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <div>
                <CardTitle>Latest Run Summary</CardTitle>
                <p className="mt-1 text-xs text-ink-muted">
                  Run #{overview?.latest_run_id} · {overview?.latest_algorithm}
                </p>
              </div>
              <Link to="/app/results">
                <Button size="sm" variant="secondary">
                  View Results <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="flex flex-wrap justify-around gap-6">
              <ProgressRing value={overview?.matching_percentage ?? 0} label="Students Matched" color="#3987e5" />
              <ProgressRing value={overview?.capacity_utilization ?? 0} label="Capacity Utilization" color="#9085e9" />
              <ProgressRing value={overview?.preference_satisfaction ?? 0} label="Preference Satisfaction" color="#0ca30c" />
            </CardContent>
          </Card>

          {theory && (
            <Card>
              <CardHeader className="flex-row items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2"><Scale className="h-4 w-4" /> What the theory guarantees about this data</CardTitle>
                  <p className="mt-1 text-xs text-ink-muted">Recomputed from the current students and labs with a max flow and its minimum cut.</p>
                </div>
                <Link to="/app/insights#bottleneck">
                  <Button size="sm" variant="secondary">Full analysis <ArrowRight className="h-3.5 w-3.5" /></Button>
                </Link>
              </CardHeader>
              <CardContent className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-3">
                <div className="rounded-xl border border-border-subtle bg-white/[0.02] p-4">
                  <p className="text-xs text-ink-muted">Upper bound on placements</p>
                  <p className="mt-1 text-2xl font-semibold tabular text-ink">{theory.max_flow}</p>
                  <p className="mt-1 text-xs text-ink-secondary">No algorithm can place more: a cut of capacity {theory.min_cut_capacity} proves it (max-flow = min-cut).</p>
                </div>
                <div className="rounded-xl border border-border-subtle bg-white/[0.02] p-4">
                  <p className="text-xs text-ink-muted">Hall deficiency</p>
                  <p className="mt-1 text-2xl font-semibold tabular text-ink">{theory.hall.deficiency}</p>
                  <p className="mt-1 text-xs text-ink-secondary">
                    {theory.hall.deficiency === 0
                      ? "Every student can be placed."
                      : theory.bottleneck_labs.length === 0 && theory.binding_quotas.length === 0
                        ? `Limited by eligibility, not seats: ${theory.hall.students_with_no_eligible_lab} students have no eligible lab.`
                        : `${theory.hall.violator_size} students compete for ${theory.hall.reachable_capacity} reachable seats.`}
                  </p>
                </div>
                <div className="rounded-xl border border-border-subtle bg-white/[0.02] p-4">
                  <p className="text-xs text-ink-muted">König vertex cover</p>
                  <p className="mt-1 text-2xl font-semibold tabular text-ink">{theory.konig.min_vertex_cover}</p>
                  <p className="mt-1 text-xs text-ink-secondary">Equals the maximum matching, as König&apos;s theorem says it must on a bipartite graph.</p>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Laboratory Utilization</CardTitle>
              </CardHeader>
              <CardContent>
                <LabUtilizationChart data={data?.lab_utilization ?? []} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Department Allocation</CardTitle>
              </CardHeader>
              <CardContent>
                <DepartmentChart data={data?.department_allocation ?? []} />
              </CardContent>
            </Card>
          </div>
        </>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Link to="/app/atlas">
          <Card className="flex items-center gap-3 p-4 transition-colors hover:bg-white/[0.04]">
            <BookOpen className="h-5 w-5 text-brand-400" />
            <div>
              <p className="text-sm font-medium text-ink">Algorithm Atlas</p>
              <p className="text-xs text-ink-muted">Every algorithm in the system, its complexity, and where the product uses it.</p>
            </div>
          </Card>
        </Link>
        <Link to="/app/concepts">
          <Card className="flex items-center gap-3 p-4 transition-colors hover:bg-white/[0.04]">
            <FlaskRound className="h-5 w-5 text-brand-400" />
            <div>
              <p className="text-sm font-medium text-ink">Concept Lab</p>
              <p className="text-xs text-ink-muted">Run strings, DP, flow, NP and randomised algorithms on your own input.</p>
            </div>
          </Card>
        </Link>
      </div>
    </div>
  )
}
