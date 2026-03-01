import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost, apiDelete } from '@/lib/api/client'
import type { ActionManifest, ActionExecution, ExecutionRequest } from './types'

const ACTIONS_KEY = ['actions'] as const
const EXECUTIONS_KEY = ['executions'] as const

// ─── Actions ─────────────────────────────────────────────────────────────────

export function useActions() {
  return useQuery({
    queryKey: ACTIONS_KEY,
    queryFn: () => apiGet<ActionManifest[]>('api/v1/actions'),
    staleTime: 60_000,
  })
}

export function useAction(actionId: string) {
  return useQuery({
    queryKey: [...ACTIONS_KEY, actionId],
    queryFn: () => apiGet<ActionManifest>(`api/v1/actions/${actionId}`),
    enabled: !!actionId,
  })
}

// ─── Execute ─────────────────────────────────────────────────────────────────

export function useExecuteAction(actionId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (req: ExecutionRequest) =>
      apiPost<ActionExecution>(`api/v1/actions/${actionId}/execute`, req),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: EXECUTIONS_KEY })
    },
  })
}

// ─── My executions ────────────────────────────────────────────────────────────

export function useMyExecutions() {
  return useQuery({
    queryKey: [...EXECUTIONS_KEY, 'me'],
    queryFn: () => apiGet<ActionExecution[]>('api/v1/actions/executions/me'),
    refetchInterval: 10_000,  // poll every 10s for status updates
  })
}

export function useExecution(execId: string) {
  return useQuery({
    queryKey: [...EXECUTIONS_KEY, execId],
    queryFn: () => apiGet<ActionExecution>(`api/v1/actions/executions/${execId}`),
    enabled: !!execId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'running' || status === 'pending_approval' ? 5_000 : false
    },
  })
}

// ─── Approval ────────────────────────────────────────────────────────────────

export function useApproveExecution(execId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { approved: boolean; reason?: string }) =>
      apiPost<ActionExecution>(`api/v1/actions/executions/${execId}/approve`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: EXECUTIONS_KEY })
    },
  })
}

export function useCancelExecution(execId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => apiPost<ActionExecution>(`api/v1/actions/executions/${execId}/cancel`, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: EXECUTIONS_KEY })
    },
  })
}

// ─── Delete action ────────────────────────────────────────────────────────────

export function useDeleteAction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (actionId: string) => apiDelete(`api/v1/actions/${actionId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ACTIONS_KEY })
    },
  })
}
