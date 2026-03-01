import { useState } from 'react'
import { Zap, ChevronRight, Tag, Users, CheckCircle, Loader2, AlertCircle } from 'lucide-react'
import { useActions } from './useActions'
import { ActionExecuteModal } from './ActionExecuteModal'
import { ExecutionHistory } from './ExecutionHistory'
import { EmptyState } from '@/components/shared/EmptyState'
import { cn } from '@/lib/utils/cn'
import type { ActionManifest } from './types'

const executorLabel: Record<string, string> = {
  ado_pipeline: 'ADO Pipeline',
  github_actions: 'GitHub Actions',
  http_webhook: 'Webhook',
  azure_function: 'Azure Function',
  manual: 'Manual',
}

const executorColor: Record<string, string> = {
  ado_pipeline: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
  github_actions: 'bg-gray-500/10 text-gray-600 dark:text-gray-300',
  http_webhook: 'bg-orange-500/10 text-orange-600',
  azure_function: 'bg-purple-500/10 text-purple-600',
  manual: 'bg-muted text-muted-foreground',
}

function ActionCard({ action, onExecute }: { action: ActionManifest; onExecute: (a: ActionManifest) => void }) {
  return (
    <div className="bg-card border border-border rounded-xl p-5 hover:border-primary/40 transition-colors">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className="p-1.5 bg-primary/10 rounded-lg flex-shrink-0">
            <Zap className="w-4 h-4 text-primary" />
          </div>
          <h3 className="font-semibold truncate">{action.name}</h3>
        </div>
        <span className={cn('text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0', executorColor[action.executor_type])}>
          {executorLabel[action.executor_type]}
        </span>
      </div>

      {action.description && (
        <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{action.description}</p>
      )}

      <div className="flex items-center gap-3 text-xs text-muted-foreground mb-4">
        {action.category && (
          <span className="flex items-center gap-1">
            <Tag className="w-3 h-3" /> {action.category}
          </span>
        )}
        {action.approval.required && (
          <span className="flex items-center gap-1 text-yellow-600">
            <Users className="w-3 h-3" /> Approval required
          </span>
        )}
        {action.parameters.length > 0 && (
          <span>{action.parameters.length} param{action.parameters.length !== 1 ? 's' : ''}</span>
        )}
      </div>

      <button
        onClick={() => onExecute(action)}
        className="w-full flex items-center justify-center gap-2 py-2 bg-primary/10 hover:bg-primary/20 text-primary text-sm font-medium rounded-lg transition-colors"
      >
        <Zap className="w-4 h-4" />
        {action.approval.required ? 'Request Execution' : 'Execute'}
        <ChevronRight className="w-4 h-4 ml-auto" />
      </button>
    </div>
  )
}

// ─── Groups by category ───────────────────────────────────────────────────────

export function ActionsList() {
  const { data: actions, isLoading, isError, error } = useActions()
  const [selectedAction, setSelectedAction] = useState<ActionManifest | null>(null)
  const [tab, setTab] = useState<'actions' | 'history'>('actions')

  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="p-6 flex items-center gap-2 text-destructive">
        <AlertCircle className="w-5 h-5" />
        {(error as Error).message}
      </div>
    )
  }

  const grouped = (actions ?? []).reduce<Record<string, ActionManifest[]>>((acc, a) => {
    const cat = a.category || 'General'
    ;(acc[cat] ??= []).push(a)
    return acc
  }, {})

  return (
    <div className="p-6 max-w-6xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Actions</h1>
          <p className="text-muted-foreground mt-1 text-sm">Self-service operations for your services</p>
        </div>
        <div className="flex gap-1 bg-muted rounded-lg p-1">
          {(['actions', 'history'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={cn(
                'px-4 py-1.5 text-sm rounded-md font-medium transition-colors capitalize',
                tab === t ? 'bg-card shadow-sm text-foreground' : 'text-muted-foreground',
              )}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {tab === 'history' ? (
        <ExecutionHistory />
      ) : actions?.length === 0 ? (
        <EmptyState
          title="No actions registered"
          description="Actions allow engineers to self-serve Day-2 operations without filing tickets."
        />
      ) : (
        <div className="space-y-8">
          {Object.entries(grouped).map(([category, items]) => (
            <section key={category}>
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                {category}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {items.map((action) => (
                  <ActionCard key={action.id} action={action} onExecute={setSelectedAction} />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      {selectedAction && (
        <ActionExecuteModal
          action={selectedAction}
          onClose={() => setSelectedAction(null)}
        />
      )}
    </div>
  )
}
