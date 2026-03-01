import { Component, type ReactNode, type ErrorInfo } from 'react'
import { AlertTriangle } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  correlationId: string
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null, correlationId: '' }

  static getDerivedStateFromError(error: Error): State {
    const correlationId =
      (error as any).correlationId || crypto.randomUUID().slice(0, 8)
    return { hasError: true, error, correlationId }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary]', error, info)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback
      return (
        <div className="flex flex-col items-center justify-center min-h-48 p-8 text-center">
          <AlertTriangle className="w-10 h-10 text-destructive mb-3" />
          <h3 className="font-semibold text-foreground mb-1">Something went wrong</h3>
          <p className="text-muted-foreground text-sm mb-3">{this.state.error?.message}</p>
          <p className="text-xs text-muted-foreground/60 font-mono">
            Correlation ID: {this.state.correlationId}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null, correlationId: '' })}
            className="mt-4 text-sm text-primary hover:underline"
          >
            Try again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
