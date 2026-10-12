import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "border-brand-500/30 bg-brand-500/15 text-brand-400",
        secondary: "border-border-strong bg-white/[0.05] text-ink-secondary",
        success: "border-good/30 bg-good/15 text-good",
        warning: "border-warning/30 bg-warning/15 text-warning",
        critical: "border-critical/30 bg-critical/15 text-critical",
        outline: "border-border-strong text-ink-secondary",
      },
    },
    defaultVariants: { variant: "default" },
  }
)

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
