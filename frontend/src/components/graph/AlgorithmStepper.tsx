import { useEffect, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { GitBranch, Search, CheckCircle2, XCircle, Flag, Layers } from "lucide-react"
import type { AlgorithmStep } from "@/types"
import { cn } from "@/lib/utils"

const EVENT_META: Record<string, { icon: typeof Search; color: string }> = {
  GRAPH_CREATED: { icon: GitBranch, color: "text-brand-400" },
  PHASE_START: { icon: Layers, color: "text-violet-400" },
  SEARCHING_AUGMENTING_PATH: { icon: Search, color: "text-ink-muted" },
  AUGMENTING_PATH_FOUND: { icon: CheckCircle2, color: "text-good" },
  MATCH_FOUND: { icon: CheckCircle2, color: "text-good" },
  MATCH_UPDATED: { icon: CheckCircle2, color: "text-good" },
  NO_PATH_FOUND: { icon: XCircle, color: "text-ink-muted" },
  ALGORITHM_COMPLETE: { icon: Flag, color: "text-brand-400" },
}

export function AlgorithmStepper({ steps, maxVisible = 200 }: { steps: AlgorithmStep[]; maxVisible?: number }) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    containerRef.current?.scrollTo({ top: containerRef.current.scrollHeight, behavior: "smooth" })
  }, [steps.length])

  const visible = steps.slice(-maxVisible)

  return (
    <div ref={containerRef} className="max-h-[420px] space-y-1.5 overflow-y-auto pr-2">
      <AnimatePresence initial={false}>
        {visible.map((step) => {
          const meta = EVENT_META[step.event] ?? { icon: Search, color: "text-ink-muted" }
          const Icon = meta.icon
          return (
            <motion.div
              key={step.step_number}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              className={cn(
                "flex items-start gap-2 rounded-lg border border-border-subtle bg-white/[0.02] px-3 py-2 text-xs",
                step.event === "ALGORITHM_COMPLETE" && "border-brand-500/40 bg-brand-500/[0.06]"
              )}
            >
              <Icon className={cn("mt-0.5 h-3.5 w-3.5 shrink-0", meta.color)} />
              <div>
                <span className="tabular text-ink-muted">#{step.step_number}</span>{" "}
                <span className="text-ink-secondary">{step.description}</span>
              </div>
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}
