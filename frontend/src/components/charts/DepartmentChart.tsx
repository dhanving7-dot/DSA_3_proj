import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { CHART_CHROME, STATUS } from "@/lib/chartTheme"
import type { DepartmentAllocation } from "@/types"

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg glass-panel-strong px-3 py-2 text-xs">
      <p className="mb-1 font-medium text-ink">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: <span className="tabular text-ink">{p.value}</span>
        </p>
      ))}
    </div>
  )
}

export function DepartmentChart({ data }: { data: DepartmentAllocation[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 8 }} barCategoryGap={20}>
        <CartesianGrid stroke={CHART_CHROME.gridline} vertical={false} />
        <XAxis dataKey="department" tick={{ fill: CHART_CHROME.textMuted, fontSize: 11 }} axisLine={{ stroke: CHART_CHROME.baseline }} tickLine={false} />
        <YAxis tick={{ fill: CHART_CHROME.textMuted, fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
        <Legend wrapperStyle={{ fontSize: 12, color: CHART_CHROME.textSecondary }} />
        <Bar dataKey="matched" name="Matched" fill={STATUS.good} radius={[4, 4, 0, 0]} />
        <Bar dataKey="unmatched" name="Unmatched" fill={STATUS.critical} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
