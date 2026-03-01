import { useState, useRef } from 'react'
import { X, Zap, Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import { useExecuteAction } from './useActions'
import type { ActionManifest } from './types'

interface Props {
  action: ActionManifest
  targetEntityId?: string
  onClose: () => void
}

export function ActionExecuteModal({ action, targetEntityId, onClose }: Props) {
  const formRef = useRef<HTMLFormElement>(null)
  const { mutate: execute, isPending, data: execution, error } = useExecuteAction(action.id)
  const [done, setDone] = useState(false)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formRef.current) return
    const fd = new FormData(formRef.current)
    const errs: Record<string, string> = {}
    const params: Record<string, unknown> = {}

    for (const param of action.parameters) {
      const raw = fd.get(param.name)
      if (param.required && (raw === null || raw === '')) {
        errs[param.name] = `${param.label} is required`
        continue
      }
      if (param.type === 'integer') {
        params[param.name] = raw ? parseInt(String(raw), 10) : param.default
      } else if (param.type === 'boolean') {
        params[param.name] = raw === 'on'
      } else {
        params[param.name] = raw ?? param.default
      }
    }

    if (Object.keys(errs).length > 0) {
      setValidationErrors(errs)
      return
    }
    setValidationErrors({})

    const comment = String(fd.get('_comment') ?? '')
    execute(
      { action_id: action.id, target_entity_id: targetEntityId ?? '', parameters: params, comment },
      { onSuccess: () => setDone(true) },
    )
  }

  if (done && execution) {
    const isPendingApproval = execution.status === 'pending_approval'
    return (
      <ModalShell onClose={onClose}>
        <div className="text-center py-6 px-4">
          {isPendingApproval ? (
            <>
              <div className="w-12 h-12 bg-yellow-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
                <Zap className="w-6 h-6 text-yellow-500" />
              </div>
              <h3 className="font-semibold text-lg">Awaiting Approval</h3>
              <p className="text-muted-foreground text-sm mt-1">
                Your request has been submitted and is waiting for approval.
              </p>
              <p className="text-xs text-muted-foreground mt-2 font-mono">{execution.id}</p>
            </>
          ) : (
            <>
              <div className="w-12 h-12 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
                <CheckCircle className="w-6 h-6 text-green-500" />
              </div>
              <h3 className="font-semibold text-lg">Action Triggered</h3>
              <p className="text-muted-foreground text-sm mt-1">
                <strong>{action.name}</strong> is running.
              </p>
              <p className="text-xs text-muted-foreground mt-2 font-mono">{execution.id}</p>
            </>
          )}
          <button
            onClick={onClose}
            className="mt-5 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium"
          >
            Close
          </button>
        </div>
      </ModalShell>
    )
  }

  return (
    <ModalShell onClose={onClose}>
      <div className="p-6">
        <div className="flex items-start gap-3 mb-5">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Zap className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-bold">{action.name}</h2>
            {action.description && (
              <p className="text-sm text-muted-foreground mt-0.5">{action.description}</p>
            )}
          </div>
        </div>

        {action.approval.required && (
          <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg px-4 py-2 mb-4 text-sm text-yellow-700 dark:text-yellow-400">
            This action requires approval before running.
          </div>
        )}

        <form ref={formRef} onSubmit={onSubmit} className="space-y-4">
          {action.parameters.map((param) => (
            <div key={param.name}>
              <label className="block text-sm font-medium mb-1">
                {param.label}
                {param.required && <span className="text-destructive ml-1">*</span>}
              </label>
              {param.description && (
                <p className="text-xs text-muted-foreground mb-1">{param.description}</p>
              )}
              {param.type === 'select' ? (
                <select
                  name={param.name}
                  className="w-full bg-muted border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  <option value="">Select…</option>
                  {param.options.map((o) => (
                    <option key={o} value={o}>{o}</option>
                  ))}
                </select>
              ) : param.type === 'boolean' ? (
                <input type="checkbox" name={param.name} className="w-4 h-4" />
              ) : (
                <input
                  type={param.secret ? 'password' : param.type === 'integer' ? 'number' : 'text'}
                  name={param.name}
                  defaultValue={param.default !== null ? String(param.default) : ''}
                  placeholder={param.label}
                  className="w-full bg-muted border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              )}
              {validationErrors[param.name] && (
                <p className="text-xs text-destructive mt-1">{validationErrors[param.name]}</p>
              )}
            </div>
          ))}

          <div>
            <label className="block text-sm font-medium mb-1">Comment <span className="text-muted-foreground font-normal">(optional)</span></label>
            <textarea
              name="_comment"
              rows={2}
              placeholder="Reason for this action…"
              className="w-full bg-muted border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 text-destructive text-sm">
              <AlertCircle className="w-4 h-4" />
              {(error as Error).message}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm rounded-lg border border-border hover:bg-muted">
              Cancel
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-sm rounded-lg font-medium disabled:opacity-50"
            >
              {isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              {action.approval.required ? 'Submit for Approval' : 'Execute'}
            </button>
          </div>
        </form>
      </div>
    </ModalShell>
  )
}

function ModalShell({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-card border border-border rounded-2xl shadow-2xl w-full max-w-md overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-end px-4 pt-4">
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}
