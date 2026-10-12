import type { ReactNode } from "react"
import { Play, Lightbulb } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

interface DemoCardProps {
  id: string
  title: string
  complexity: string
  concept: ReactNode
  controls?: ReactNode
  onRun?: () => void
  running?: boolean
  runLabel?: string
  children?: ReactNode
  className?: string
}

/** One Concept Lab demo: the idea in words, the inputs, and the real backend result. */
export function DemoCard({ id, title, complexity, concept, controls, onRun, running, runLabel = "Run", children, className }: DemoCardProps) {
  return (
    <Card id={id} className={cn("scroll-mt-24", className)}>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <CardTitle className="text-base text-ink">{title}</CardTitle>
          <Badge variant="secondary" className="font-mono text-[11px]">{complexity}</Badge>
        </div>
        <div className="mt-1 flex gap-2 rounded-lg border border-brand-500/20 bg-brand-500/[0.05] p-3 text-xs leading-relaxed text-ink-secondary">
          <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand-400" />
          <div>{concept}</div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {(controls || onRun) && (
          <div className="flex flex-wrap items-end gap-3">
            {controls}
            {onRun && (
              <Button onClick={onRun} disabled={running} size="sm">
                <Play className="h-3.5 w-3.5" /> {running ? "Running..." : runLabel}
              </Button>
            )}
          </div>
        )}
        {running ? <Skeleton className="h-32 w-full" /> : children}
      </CardContent>
    </Card>
  )
}

export function Field({ label, children, className }: { label: string; children: ReactNode; className?: string }) {
  return (
    <label className={cn("flex flex-col gap-1 text-xs text-ink-muted", className)}>
      {label}
      {children}
    </label>
  )
}

export function MetricTile({ label, value, hint, tone }: { label: string; value: ReactNode; hint?: string; tone?: "good" | "critical" | "brand" }) {
  return (
    <div className="rounded-lg border border-border-subtle bg-white/[0.02] px-3 py-2">
      <p className="text-[10px] uppercase tracking-wide text-ink-muted">{label}</p>
      <p
        className={cn(
          "mt-0.5 text-sm font-medium tabular",
          tone === "good" ? "text-good" : tone === "critical" ? "text-critical" : tone === "brand" ? "text-brand-400" : "text-ink"
        )}
      >
        {value}
      </p>
      {hint && <p className="mt-0.5 text-[10px] text-ink-muted">{hint}</p>}
    </div>
  )
}

/** A pass/fail line for results the backend verified against an independent oracle. */
export function Verified({ ok, children }: { ok: boolean; children: ReactNode }) {
  return (
    <p className={cn("flex items-center gap-1.5 text-xs", ok ? "text-good" : "text-critical")}>
      <span aria-hidden>{ok ? "✓" : "✗"}</span>
      <span className="text-ink-secondary">{children}</span>
    </p>
  )
}
