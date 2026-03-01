import { createFileRoute } from '@tanstack/react-router'
import { Dashboard } from '@/features/dashboard/Dashboard'
import { ErrorBoundary } from '@/components/shared/ErrorBoundary'

export const Route = createFileRoute('/dashboard')({
  component: DashboardPage,
})

function DashboardPage() {
  return (
    <ErrorBoundary>
      <Dashboard />
    </ErrorBoundary>
  )
}
