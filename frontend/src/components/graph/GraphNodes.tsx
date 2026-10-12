import { memo } from "react"
import { Handle, Position, type NodeProps } from "reactflow"
import { GraduationCap, FlaskConical } from "lucide-react"
import { cn } from "@/lib/utils"

export interface BipartiteNodeData {
  label: string
  sublabel?: string
  kind: "student" | "lab"
  status?: "matched" | "unmatched" | "neutral" | "active"
  dimmed?: boolean
}

function BipartiteNodeImpl({ data }: NodeProps<BipartiteNodeData>) {
  const isStudent = data.kind === "student"
  const statusRing =
    data.status === "matched"
      ? "border-good/50 shadow-[0_0_16px_-2px_rgba(12,163,12,0.5)]"
      : data.status === "active"
      ? "border-brand-400/60 shadow-[0_0_16px_-2px_rgba(99,102,241,0.6)]"
      : data.status === "unmatched"
      ? "border-critical/40"
      : "border-border-strong"

  return (
    <div
      className={cn(
        "flex min-w-[150px] items-center gap-2 rounded-xl glass-panel px-3 py-2 transition-opacity",
        statusRing,
        data.dimmed && "opacity-25"
      )}
    >
      {isStudent ? (
        <Handle type="source" position={Position.Right} className="!h-2 !w-2 !border-none !bg-brand-400" />
      ) : (
        <Handle type="target" position={Position.Left} className="!h-2 !w-2 !border-none !bg-violet-400" />
      )}
      <div className={cn("flex h-7 w-7 shrink-0 items-center justify-center rounded-lg", isStudent ? "bg-brand-500/20 text-brand-400" : "bg-violet-500/20 text-violet-400")}>
        {isStudent ? <GraduationCap className="h-3.5 w-3.5" /> : <FlaskConical className="h-3.5 w-3.5" />}
      </div>
      <div className="overflow-hidden">
        <p className="truncate text-xs font-medium text-ink">{data.label}</p>
        {data.sublabel && <p className="truncate text-[10px] text-ink-muted">{data.sublabel}</p>}
      </div>
    </div>
  )
}

export const BipartiteNode = memo(BipartiteNodeImpl)

export const nodeTypes = { bipartite: BipartiteNode }
