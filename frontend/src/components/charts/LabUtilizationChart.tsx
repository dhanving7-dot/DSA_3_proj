import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { CHART_CHROME, SERIES } from "@/lib/chartTheme"
import type { LabUtilization } from "@/types"

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

function shortLabName(name: string) {
  return name
    .replace(" Laboratory", "")
    .replace(" (Under Maintenance)", "")
    .replace("Artificial Intelligence", "AI")
    .replace("Database Management Systems", "DBMS")
    .replace("Computer Aided Design", "CAD")
    .replace("Computer Networks", "Networks")
}

export function LabUtilizationChart({ data }: { data: LabUtilization[] }) {
  const chartData = data.map((d) => ({
    name: shortLabName(d.lab_name),
    Allocated: d.allocated,
    Remaining: Math.max(d.capacity - d.allocated, 0),
  }))

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 8 }} barCategoryGap={18}>
        <CartesianGrid stroke={CHART_CHROME.gridline} vertical={false} />
        <XAxis
          dataKey="name"
          tick={{ fill: CHART_CHROME.textMuted, fontSize: 11 }}
          axisLine={{ stroke: CHART_CHROME.baseline }}
          tickLine={false}
          interval={0}
          angle={-30}
          textAnchor="end"
          height={64}
        />
        <YAxis tick={{ fill: CHART_CHROME.textMuted, fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
        <Legend wrapperStyle={{ fontSize: 12, color: CHART_CHROME.textSecondary }} />
        <Bar dataKey="Allocated" stackId="a" fill={SERIES.blue} radius={[0, 0, 4, 4]} />
        <Bar dataKey="Remaining" stackId="a" fill="rgba(255,255,255,0.08)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
