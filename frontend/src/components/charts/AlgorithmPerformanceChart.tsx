import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, Cell } from "recharts"
import { ALGORITHM_COLORS, CHART_CHROME } from "@/lib/chartTheme"
import { ALGORITHM_LABELS } from "@/lib/algorithms"
import type { AlgorithmPerformance } from "@/types"

function ChartTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null
  const p = payload[0].payload
  return (
    <div className="rounded-lg glass-panel-strong px-3 py-2 text-xs">
      <p className="mb-1 font-medium text-ink">{p.algorithm}</p>
      <p className="text-ink-secondary">
        Run #{p.run_id} - <span className="tabular text-ink">{p.execution_time_ms.toFixed(4)}ms</span>
      </p>
    </div>
  )
}

export function AlgorithmPerformanceChart({ data }: { data: AlgorithmPerformance[] }) {
  const chartData = [...data].reverse().slice(-12)
  const present = Object.keys(ALGORITHM_COLORS).filter((a) => chartData.some((d) => d.algorithm === a))

  return (
    <div>
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={chartData} margin={{ top: 8, right: 8, left: -16, bottom: 8 }}>
        <CartesianGrid stroke={CHART_CHROME.gridline} vertical={false} />
        <XAxis dataKey="run_id" tickFormatter={(v) => `#${v}`} tick={{ fill: CHART_CHROME.textMuted, fontSize: 11 }} axisLine={{ stroke: CHART_CHROME.baseline }} tickLine={false} />
        <YAxis tick={{ fill: CHART_CHROME.textMuted, fontSize: 11 }} axisLine={false} tickLine={false} unit="ms" />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
        <Bar dataKey="execution_time_ms" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={ALGORITHM_COLORS[entry.algorithm] ?? CHART_CHROME.textMuted} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-ink-secondary">
        {present.map((a) => (
          <span key={a} className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-sm" style={{ background: ALGORITHM_COLORS[a] }} />
            {ALGORITHM_LABELS[a] ?? a}
          </span>
        ))}
      </div>
    </div>
  )
}
