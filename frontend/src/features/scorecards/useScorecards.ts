import { useQuery } from '@tanstack/react-query'
import { listTemplates, scoreService, scoreAllServices } from './api'

export function useScorecardTemplates() {
  return useQuery({
    queryKey: ['scorecards', 'templates'],
    queryFn: listTemplates,
    staleTime: 5 * 60_000,
  })
}

export function useServiceScorecard(serviceId: string) {
  return useQuery({
    queryKey: ['scorecards', 'service', serviceId],
    queryFn: () => scoreService(serviceId),
    enabled: Boolean(serviceId),
    staleTime: 2 * 60_000,
  })
}

export function useAllScorecards() {
  return useQuery({
    queryKey: ['scorecards', 'all'],
    queryFn: scoreAllServices,
    staleTime: 2 * 60_000,
  })
}
