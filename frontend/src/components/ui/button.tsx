import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/50",
  {
    variants: {
      variant: {
        default: "bg-gradient-to-b from-brand-500 to-brand-600 text-white shadow-[0_1px_0_0_rgba(255,255,255,0.15)_inset,0_4px_16px_-4px_rgba(99,102,241,0.5)] hover:brightness-110",
        secondary: "bg-white/[0.06] text-ink border border-border-strong hover:bg-white/[0.1]",
        outline: "border border-border-strong bg-transparent text-ink hover:bg-white/[0.05]",
        ghost: "text-ink-secondary hover:bg-white/[0.06] hover:text-ink",
        destructive: "bg-critical/90 text-white hover:bg-critical",
        link: "text-brand-400 underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-11 rounded-lg px-6 text-base",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
