import { Component, type ErrorInfo, type ReactNode } from "react"
import { AlertTriangle } from "lucide-react"
import { Button } from "@/components/ui/button"

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error) {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Unhandled UI error:", error, info)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-[300px] flex-col items-center justify-center gap-3 rounded-2xl border border-critical/30 bg-critical/[0.04] p-10 text-center">
          <AlertTriangle className="h-8 w-8 text-critical" />
          <p className="text-sm font-medium text-ink">Something went wrong rendering this section.</p>
          <p className="max-w-md text-xs text-ink-muted">{this.state.error.message}</p>
          <Button size="sm" variant="secondary" onClick={() => this.setState({ error: null })}>
            Try again
          </Button>
        </div>
      )
    }
    return this.props.children
  }
}
