import { useRef, useCallback, useState } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { Search } from 'lucide-react'
import { useEntities } from './useEntities'
import { EntityCard } from './EntityCard'
import { EntityCardSkeleton } from './EntityCardSkeleton'
import { EmptyState } from '@/components/shared/EmptyState'
import { cn } from '@/lib/utils/cn'
import type { EntityKind } from '@/types/entities'

const ENTITY_KINDS: { kind: EntityKind; label: string }[] = [
  { kind: 'Service', label: 'Services' },
  { kind: 'AzureResource', label: 'Azure Resources' },
  { kind: 'Environment', label: 'Environments' },
  { kind: 'Team', label: 'Teams' },
  { kind: 'ApiEndpoint', label: 'APIs' },
  { kind: 'Package', label: 'Packages' },
  { kind: 'Incident', label: 'Incidents' },
  { kind: 'ADOWorkItem', label: 'Work Items' },
]

export function CatalogBrowser() {
  const [search, setSearch] = useState('')
  const [kind, setKind] = useState<EntityKind>('Service')

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading, isError, error } =
    useEntities(search, kind)

  const allEntities = (data?.pages.flatMap((p) => p.data) ?? []) as Parameters<typeof EntityCard>[0]['entity'][]

  const parentRef = useRef<HTMLDivElement>(null)
  const rowVirtualizer = useVirtualizer({
    count: hasNextPage ? allEntities.length + 1 : allEntities.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 140,
    overscan: 5,
  })
  void rowVirtualizer // used for scroll estimation

  const fetchMoreOnScroll = useCallback(
    (e: React.UIEvent<HTMLDivElement>) => {
      const { scrollHeight, scrollTop, clientHeight } = e.currentTarget
      if (scrollHeight - scrollTop - clientHeight < 300 && hasNextPage && !isFetchingNextPage) {
        fetchNextPage()
      }
    },
    [fetchNextPage, hasNextPage, isFetchingNextPage],
  )

  const selectedLabel = ENTITY_KINDS.find((k) => k.kind === kind)?.label ?? kind

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border">
        <h1 className="text-2xl font-bold mb-4">Catalog</h1>
        <div className="relative max-w-lg mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder={`Search ${selectedLabel.toLowerCase()}...`}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-muted border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>

        {/* Entity type tabs */}
        <div className="flex gap-1 overflow-x-auto pb-1 scrollbar-none">
          {ENTITY_KINDS.map(({ kind: k, label }) => (
            <button
              key={k}
              onClick={() => setKind(k)}
              className={cn(
                'px-3 py-1.5 text-xs font-medium rounded-full whitespace-nowrap transition-colors',
                kind === k
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80',
              )}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Body */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <EntityCardSkeleton key={i} />
          ))}
        </div>
      ) : isError ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-destructive font-medium">Failed to load {selectedLabel}</p>
            <p className="text-muted-foreground text-sm mt-1">{(error as Error).message}</p>
          </div>
        </div>
      ) : allEntities.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <EmptyState
            title={`No ${selectedLabel} found`}
            description={search ? `No ${selectedLabel.toLowerCase()} match "${search}"` : `No ${selectedLabel.toLowerCase()} have been registered yet.`}
            action={{ label: 'Register one', href: '#' }}
          />
        </div>
      ) : (
        <div ref={parentRef} className="flex-1 overflow-auto p-6" onScroll={fetchMoreOnScroll}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {allEntities.map((entity) => (
              <EntityCard key={entity.id} entity={entity} />
            ))}
            {isFetchingNextPage && (
              <>
                <EntityCardSkeleton />
                <EntityCardSkeleton />
                <EntityCardSkeleton />
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
