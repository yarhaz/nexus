import { formatDistanceToNow } from 'date-fns'
import { CheckCircle, XCircle, Clock, Loader2, AlertCircle, Ban } from 'lucide-react'
import { useMyExecutions, useApproveExecution, useCancelExecution } from './useActions'
import { cn } from '@/lib/utils/cn'
import type { ActionExecution, ExecutionStatus } from './types'

// ─── Status badge ─────────────────────────────────────────────────────────────

const statusConfig: Record<ExecutionStatus, { label: string; icon: React.ElementType; color: string }> = {
  pending_approval: { label: 'Pending Approval', icon: Clock, color: 'text-yellow-600 bg-yellow-500/10' },
  approved: { label: 'Approved', icon: CheckCircle, color: 'text-blue-600 bg-blue-500/10' },
  running: { label: 'Running', icon: Loader2, color: 'text-blue-600 bg-blue-500/10' },
  succeeded: { label: 'Succeeded', icon: CheckCircle, color: 'text-green-600 bg-green-500/10' },
  failed: { label: 'Failed', icon: XCircle, color: 'text-red-600 bg-red-500/10' },
  rejected: { label: 'Rejected', icon: XCircle, color: 'text-red-600 bg-red-500/10' },
  expired: { label: 'Expired', icon: Clock, color: 'text-gray-600 bg-gray-500/10' },
  cancelled: { label: 'Cancelled', icon: Ban, color: 'text-gray-600 bg-gray-500/10' },
}

function StatusBadge({ status }: { status: ExecutionStatus }) {
  const cfg = statusConfig[status] ?? statusConfig.cancelled
  const Icon = cfg.icon
  return (
    <span className={cn('flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium', cfg.color)}>
      <Icon className={cn('w-3 h-3', status === 'running' && 'animate-spin')} />
      {cfg.label}
    </span>
  )
}

// ─── Execution row ────────────────────────────────────────────────────────────

function ExecutionRow({ execution }: { execution: ActionExecution }) {
  const { mutate: approve, isPending: approving } = useApproveExecution(execution.id)
  const { mutate: cancel, isPending: cancelling } = useCancelExecution(execution.id)

  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="min-w-0">
          <p className="font-medium truncate">{execution.action_name}</p>
          <p className="text-xs text-muted-foreground font-mono mt-0.5">{execution.id}</p>
        </div>
        <StatusBadge status={execution.status} />
      </div>

      <div className="text-xs text-muted-foreground flex flex-wrap gap-x-4 gap-y-1 mb-3">
        <span>Triggered {formatDistanceToNow(new Date(execution.created_at))} ago</span>
        {execution.triggered_by_name && <span>by {execution.triggered_by_name}</span>}
        {execution.target_entity_id && <span>target: {execution.target_entity_id}</span>}
        {execution.comment && <span>"{execution.comment}"</span>}
      </div>

      {execution.error_message && (
        <div className="flex items-center gap-2 text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2 mb-3">
          <AlertCircle className="w-3 h-3 flex-shrink-0" />
          {execution.error_message}
        </div>
      )}

      {execution.rejection_reason && (
        <div className="text-xs text-muted-foreground bg-muted rounded-lg px-3 py-2 mb-3">
          Rejected: {execution.rejection_reason}
        </div>
      )}

      {/* Actions for pending executions */}
      {execution.status === 'pending_approval' && (
        <div className="flex gap-2">
          <button
            onClick={() => approve({ approved: true })}
            disabled={approving}
            className="flex-1 flex items-center justify-center gap-1 py-1.5 text-xs bg-green-500/10 hover:bg-green-500/20 text-green-700 dark:text-green-400 rounded-lg font-medium transition-colors disabled:opacity-50"
          >
            <CheckCircle className="w-3 h-3" /> Approve
          </button>
          <button
            onClick={() => approve({ approved: false, reason: 'Rejected by approver' })}
            disabled={approving}
            className="flex-1 flex items-center justify-center gap-1 py-1.5 text-xs bg-red-500/10 hover:bg-red-500/20 text-red-700 dark:text-red-400 rounded-lg font-medium transition-colors disabled:opacity-50"
          >
            <XCircle className="w-3 h-3" /> Reject
          </button>
          <button
            onClick={() => cancel()}
            disabled={cancelling}
            className="py-1.5 px-3 text-xs bg-muted hover:bg-muted/80 text-muted-foreground rounded-lg transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
        </div>
      )}

      {execution.status === 'running' && (
        <button
          onClick={() => cancel()}
          disabled={cancelling}
          className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
        >
          <Ban className="w-3 h-3" /> Cancel
        </button>
      )}
    </div>
  )
}

// ─── History list ─────────────────────────────────────────────────────────────

export function ExecutionHistory() {
  const { data: executions, isLoading } = useMyExecutions()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!executions?.length) {
    return (
      <div className="text-center py-12 text-muted-foreground text-sm">
        No executions yet. Run an action to see history here.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {executions.map((ex) => (
        <ExecutionRow key={ex.id} execution={ex} />
      ))}
    </div>
  )
}
