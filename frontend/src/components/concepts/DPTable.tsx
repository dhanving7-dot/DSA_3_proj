import { cn } from "@/lib/utils"

interface DPTableProps {
  table: (number | null)[][]
  rowLabels: string[]
  colLabels: string[]
  path?: [number, number][]
  corner?: string
  highlight?: [number, number] | null
  format?: (v: number) => string
}

/** Renders a DP table with the optimal traceback path highlighted - the table *is* the algorithm. */
export function DPTable({ table, rowLabels, colLabels, path = [], corner = "", highlight = null, format }: DPTableProps) {
  const onPath = new Set(path.map(([i, j]) => `${i},${j}`))
  const fmt = format ?? ((v: number) => (Number.isInteger(v) ? String(v) : v.toFixed(1)))
  return (
    <div className="max-w-full overflow-auto rounded-lg border border-border-subtle">
      <table className="border-collapse text-[11px] tabular">
        <thead>
          <tr>
            <th className="sticky left-0 top-0 z-20 bg-canvas-raised px-2 py-1 text-ink-muted">{corner}</th>
            {colLabels.map((c, j) => (
              <th key={j} className="sticky top-0 z-10 min-w-7 bg-canvas-raised px-1.5 py-1 font-mono font-medium text-ink-secondary">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.map((row, i) => (
            <tr key={i}>
              <th className="sticky left-0 z-10 bg-canvas-raised px-2 py-1 text-right font-mono font-medium text-ink-secondary">{rowLabels[i]}</th>
              {row.map((v, j) => {
                const isPath = onPath.has(`${i},${j}`)
                const isHit = highlight && highlight[0] === i && highlight[1] === j
                return (
                  <td
                    key={j}
                    className={cn(
                      "border border-border-subtle/60 px-1.5 py-1 text-center",
                      v == null ? "text-ink-muted/40" : "text-ink-secondary",
                      isPath && "bg-brand-500/25 font-semibold text-ink",
                      isHit && "ring-1 ring-inset ring-good"
                    )}
                  >
                    {v == null ? "·" : fmt(v)}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
