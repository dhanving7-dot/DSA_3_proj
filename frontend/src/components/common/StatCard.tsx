import { useEffect, useRef, useState } from "react"
import { motion, useInView } from "framer-motion"
import type { LucideIcon } from "lucide-react"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface StatCardProps {
  label: string
  value: number
  suffix?: string
  decimals?: number
  icon?: LucideIcon
  accent?: "brand" | "good" | "warning" | "critical" | "violet"
  hint?: string
  delay?: number
}

const accentClasses: Record<string, string> = {
  brand: "text-brand-400 bg-brand-500/15",
  good: "text-good bg-good/15",
  warning: "text-warning bg-warning/15",
  critical: "text-critical bg-critical/15",
  violet: "text-violet-400 bg-violet-500/15",
}

function useCountUp(target: number, active: boolean, duration = 1000) {
  const [value, setValue] = useState(0)
  useEffect(() => {
    if (!active) return
    let start: number | null = null
    let raf: number
    const step = (timestamp: number) => {
      if (start === null) start = timestamp
      const progress = Math.min((timestamp - start) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(target * eased)
      if (progress < 1) raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [target, active, duration])
  return value
}

export function StatCard({ label, value, suffix = "", decimals = 0, icon: Icon, accent = "brand", hint, delay = 0 }: StatCardProps) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: "-40px" })
  const animated = useCountUp(value, inView)

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 16 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, delay }}
    >
      <Card className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">{label}</p>
            <p className="mt-2 text-3xl font-semibold tabular text-ink">
              {animated.toFixed(decimals)}
              <span className="text-lg text-ink-secondary">{suffix}</span>
            </p>
            {hint && <p className="mt-1 text-xs text-ink-muted">{hint}</p>}
          </div>
          {Icon && (
            <div className={cn("rounded-lg p-2", accentClasses[accent])}>
              <Icon className="h-4 w-4" />
            </div>
          )}
        </div>
      </Card>
    </motion.div>
  )
}
