import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/common/EmptyState"
import { LabUtilizationChart } from "@/components/charts/LabUtilizationChart"
import { DepartmentChart } from "@/components/charts/DepartmentChart"
import { AlgorithmPerformanceChart } from "@/components/charts/AlgorithmPerformanceChart"
import { useAnalyticsOverview } from "@/hooks/useAnalytics"
import { formatMs } from "@/lib/utils"
import { BarChart3 } from "lucide-react"

export default function AnalyticsPage() {
  const { data, isLoading } = useAnalyticsOverview()

  if (isLoading) return <Skeleton className="h-96 w-full" />
  if (!data?.historical_runs.length) {
    return <EmptyState icon={BarChart3} title="No analytics yet" description="Run at least one allocation to populate analytics." />
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Laboratory Utilization</CardTitle>
            <CardDescription>Allocated seats vs remaining capacity for the latest run</CardDescription>
          </CardHeader>
          <CardContent><LabUtilizationChart data={data.lab_utilization} /></CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Department Allocation</CardTitle>
            <CardDescription>Matched vs unmatched students by department</CardDescription>
          </CardHeader>
          <CardContent><DepartmentChart data={data.department_allocation} /></CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Algorithm Performance</CardTitle>
          <CardDescription>Measured execution time per run, colored by algorithm</CardDescription>
        </CardHeader>
        <CardContent><AlgorithmPerformanceChart data={data.algorithm_performance} /></CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Historical Allocation Runs</CardTitle></CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Run</TableHead>
                <TableHead>Algorithm</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Matched</TableHead>
                <TableHead>Unmatched</TableHead>
                <TableHead>Execution Time</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.historical_runs.map((r) => (
                <TableRow key={r.run_id}>
                  <TableCell className="text-ink">#{r.run_id}</TableCell>
                  <TableCell><Badge variant="secondary">{r.algorithm}</Badge></TableCell>
                  <TableCell>{r.status}</TableCell>
                  <TableCell className="tabular text-good">{r.matched_count}</TableCell>
                  <TableCell className="tabular text-critical">{r.unmatched_count}</TableCell>
                  <TableCell className="tabular">{formatMs(r.execution_time_ms)}</TableCell>
                  <TableCell className="text-ink-muted">{new Date(r.created_at).toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
