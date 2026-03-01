import { createFileRoute } from '@tanstack/react-router'
import { CatalogBrowser } from '@/features/catalog/CatalogBrowser'
import { ErrorBoundary } from '@/components/shared/ErrorBoundary'

export const Route = createFileRoute('/catalog/')({
  component: CatalogPage,
})

function CatalogPage() {
  return (
    <ErrorBoundary>
      <CatalogBrowser />
    </ErrorBoundary>
  )
}
