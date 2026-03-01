import { useState } from 'react'
import { Activity, AlertTriangle, Bug, Package, RefreshCw, Clock, ChevronRight } from 'lucide-react'
import { useOpsHealth, useChangeLog } from './useOps'
import type { ServiceHealthSummary, ChangeEvent } from './api'
import { cn } from '@/lib/utils/cn'

const HEALTH_COLOR: Record<string, string> = {
  Healthy: 'text-green-500',
  Degraded: 'text-yellow-500',
  Unavailable: 'text-red-500',
  Unknown: 'text-muted-foreground',
}

const HEALTH_BG: Record<string, string> = {
  Healthy: 'bg-green-500/10',
  Degraded: 'bg-yellow-500/10',
  Unavailable: 'bg-red-500/10',
  Unknown: 'bg-muted',
}

function HealthDot({ status }: { status: string }) {
  const color = {
    Healthy: 'bg-green-500',
    Degraded: 'bg-yellow-500',
    Unavailable: 'bg-red-500',
    Unknown: 'bg-muted-foreground',
  }[status] ?? 'bg-muted-foreground'
  return <span className={cn('inline-block w-2 h-2 rounded-full', color)} />
}

function ServiceHealthRow({ s }: { s: ServiceHealthSummary }) {
  return (
    <div className="flex items-center gap-3 py-2 border-b border-border last:border-0">
      <HealthDot status={s.health_status} />
      <span className="flex-1 text-sm font-medium truncate">{s.service_name}</span>
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        {s.critical_incidents > 0 && (
          <span className="flex items-center gap-1 text-red-500">
            <AlertTriangle className="w-3 h-3" />
            {s.critical_incidents}
          </span>
        )}
        {s.open_incidents > 0 && (
          <span className="flex items-center gap-1">
            <Activity className="w-3 h-3" />
            {s.open_incidents}
          </span>
        )}
        {s.open_bugs > 0 && (
          <span className="flex items-center gap-1">
            <Bug className="w-3 h-3" />
            {s.open_bugs}
          </span>
        )}
        {s.vulnerable_packages > 0 && (
          <span className="flex items-center gap-1 text-orange-500">
            <Package className="w-3 h-3" />
            {s.vulnerable_packages}
          </span>
        )}
      </div>
      <span className={cn('text-xs font-medium px-1.5 py-0.5 rounded', HEALTH_COLOR[s.health_status], HEALTH_BG[s.health_status])}>
        {s.health_status}
      </span>
    </div>
  )
}

const EVENT_ICON: Record<string, string> = {
  'incident.opened': '🔴',
  'incident.updated': '🟡',
  'workitem.updated': '🔵',
  'catalog.updated': '🟢',
}

function ChangeRow({ event }: { event: ChangeEvent }) {
  const ago = (() => {
    const ms = Date.now() - new Date(event.occurred_at).getTime()
    const m = Math.floor(ms / 60_000)
    if (m < 60) return `${m}m ago`
    const h = Math.floor(m / 60)
    if (h < 24) return `${h}h ago`
    return `${Math.floor(h / 24)}d ago`
  })()

  return (
    <div className="flex items-start gap-3 py-2.5 border-b border-border last:border-0">
      <span className="text-sm mt-0.5">{EVENT_ICON[event.event_type] ?? '⚪'}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm truncate">{event.summary}</p>
        <p className="text-xs text-muted-foreground mt-0.5">
          {event.entity_kind} · {event.actor || 'system'}
        </p>
      </div>
      <span className="text-xs text-muted-foreground whitespace-nowrap flex items-center gap-1">
        <Clock className="w-3 h-3" />
        {ago}
      </span>
    </div>
  )
}

export function OpsHub() {
  const { data: health, isLoading: healthLoading, refetch } = useOpsHealth()
  const { data: changelog, isLoading: logLoading } = useChangeLog(30)
  const [tab, setTab] = useState<'health' | 'changelog'>('health')

  const degradedCount = health?.services.filter(s => s.health_status === 'Degraded').length ?? 0
  const unavailableCount = health?.services.filter(s => s.health_status === 'Unavailable').length ?? 0

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Operations Hub</h1>
          <p className="text-muted-foreground text-sm mt-1">Live health, change history, and blast-radius analysis</p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-3 py-2 text-sm border border-border rounded-lg hover:bg-muted"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Aggregate stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Total Services', value: health?.services.length ?? '—', color: 'text-foreground' },
          { label: 'Open Incidents', value: health?.total_open_incidents ?? '—', color: 'text-yellow-500' },
          { label: 'Critical', value: health?.total_critical_incidents ?? '—', color: 'text-red-500' },
          { label: 'Degraded / Down', value: `${degradedCount} / ${unavailableCount}`, color: 'text-orange-500' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-card border border-border rounded-xl p-4">
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className={cn('text-2xl font-bold mt-1', color)}>{value}</p>
          </div>
        ))}
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-border">
        {(['health', 'changelog'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              'px-4 py-2 text-sm font-medium capitalize border-b-2 -mb-px transition-colors',
              tab === t
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground',
            )}
          >
            {t === 'health' ? 'Service Health' : 'Change Log'}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'health' && (
        <div className="bg-card border border-border rounded-xl divide-y divide-border">
          {healthLoading ? (
            <p className="p-6 text-sm text-muted-foreground">Loading health data…</p>
          ) : !health?.services.length ? (
            <p className="p-6 text-sm text-muted-foreground">No services found.</p>
          ) : (
            <div className="p-4">
              {health.services.map(s => (
                <ServiceHealthRow key={s.service_id} s={s} />
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'changelog' && (
        <div className="bg-card border border-border rounded-xl">
          {logLoading ? (
            <p className="p-6 text-sm text-muted-foreground">Loading change log…</p>
          ) : !changelog?.events.length ? (
            <p className="p-6 text-sm text-muted-foreground">No recent changes.</p>
          ) : (
            <div className="p-4">
              {changelog.events.map(e => (
                <ChangeRow key={e.id} event={e} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
