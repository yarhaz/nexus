import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { useDebounce } from 'use-debounce'
import {
  listServices,
  getService,
  azureResources,
  environments,
  teams,
  apiEndpoints,
  packages,
  incidents,
  adoWorkItems,
} from './api'
import type { EntityKind } from '@/types/entities'

const entityListFns: Record<EntityKind, (params: { cursor?: string; limit?: number }) => Promise<{ data: unknown[]; next_cursor: string | null }>> = {
  Service: (p) => listServices(p) as Promise<{ data: unknown[]; next_cursor: string | null }>,
  AzureResource: (p) => azureResources.list(p) as Promise<{ data: unknown[]; next_cursor: string | null }>,
  Environment: (p) => environments.list(p) as Promise<{ data: unknown[]; next_cursor: string | null }>,
  Team: (p) => teams.list(p) as Promise<{ data: unknown[]; next_cursor: string | null }>,
  ApiEndpoint: (p) => apiEndpoints.list(p) as Promise<{ data: unknown[]; next_cursor: string | null }>,
  Package: (p) => packages.list(p) as Promise<{ data: unknown[]; next_cursor: string | null }>,
  Incident: (p) => incidents.list(p) as Promise<{ data: unknown[]; next_cursor: string | null }>,
  ADOWorkItem: (p) => adoWorkItems.list(p) as Promise<{ data: unknown[]; next_cursor: string | null }>,
}

export function useEntities(search?: string, kind: EntityKind = 'Service') {
  const [debouncedSearch] = useDebounce(search, 300)
  void debouncedSearch // search is used client-side for now; future: pass to server

  return useInfiniteQuery({
    queryKey: ['catalog', kind, debouncedSearch],
    queryFn: async ({ pageParam }) => {
      const fn = entityListFns[kind]
      return fn({ cursor: pageParam as string | undefined, limit: 25 })
    },
    initialPageParam: undefined,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
  })
}

export function useEntity(id: string) {
  return useQuery({
    queryKey: ['catalog', 'service', id],
    queryFn: () => getService(id),
    enabled: !!id,
  })
}
