import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMyState } from '@/features/catalog/api'
import { apiPost } from '@/lib/api/client'

export const USER_STATE_KEY = ['userstate', 'me'] as const

export function useUserState() {
  return useQuery({
    queryKey: USER_STATE_KEY,
    queryFn: getMyState,
    staleTime: 30_000,   // 30s — recomputed server-side every 60s
    retry: 1,
  })
}

export function useInvalidateUserState() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => apiPost('api/v1/userstate/me/invalidate', {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: USER_STATE_KEY }),
  })
}
