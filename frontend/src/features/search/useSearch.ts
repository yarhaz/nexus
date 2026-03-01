import { useQuery } from '@tanstack/react-query'
import { useDebounce } from 'use-debounce'
import { apiGet } from '@/lib/api/client'
import type { SearchResponse } from './types'

export function useSearch(query: string) {
  const [debouncedQuery] = useDebounce(query.trim(), 250)

  return useQuery({
    queryKey: ['search', debouncedQuery],
    queryFn: () =>
      apiGet<SearchResponse>(`api/v1/search?q=${encodeURIComponent(debouncedQuery)}&limit=15`),
    enabled: debouncedQuery.length >= 2,
    staleTime: 10_000,
    placeholderData: (prev) => prev,
  })
}
