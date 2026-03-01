import { useQuery } from '@tanstack/react-query'
import { getOpsHealth, getChangeLog, getImpactAnalysis } from './api'

export function useOpsHealth() {
  return useQuery({
    queryKey: ['ops', 'health'],
    queryFn: getOpsHealth,
    staleTime: 30_000,
    refetchInterval: 60_000,
  })
}

export function useChangeLog(limit = 50, entityId = '') {
  return useQuery({
    queryKey: ['ops', 'changelog', limit, entityId],
    queryFn: () => getChangeLog(limit, entityId),
    staleTime: 30_000,
  })
}

export function useImpactAnalysis(entityId: string, depth = 3) {
  return useQuery({
    queryKey: ['ops', 'impact', entityId, depth],
    queryFn: () => getImpactAnalysis(entityId, depth),
    enabled: Boolean(entityId),
    staleTime: 60_000,
  })
}
