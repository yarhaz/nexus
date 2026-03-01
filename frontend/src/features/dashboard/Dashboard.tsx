import { AlertTriangle, ClipboardList, Users, RefreshCw } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { useUserState, useInvalidateUserState } from '@/features/userstate/useUserState'
import { EntityCard } from '@/features/catalog/EntityCard'
import { EntityCardSkeleton } from '@/features/catalog/EntityCardSkeleton'
import { EmptyState } from '@/components/shared/EmptyState'
import type { IncidentEntity, ADOWorkItemEntity } from '@/types/entities'

// ─── Incident row ─────────────────────────────────────────────────────────────

const severityColor: Record<string, string> = {
  critical: 'text-red-600 bg-red-500/10',
  high: 'text-orange-600 bg-orange-500/10',
  medium: 'text-yellow-600 bg-yellow-500/10',
  low: 'text-green-600 bg-green-500/10',
}

function IncidentRow({ incident }: { incident: IncidentEntity }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border last:border-0">
      <div className="flex items-center gap-3 min-w-0">
        <AlertTriangle className="w-4 h-4 text-destructive flex-shrink-0" />
        <span className="text-sm font-medium truncate">{incident.title}</span>
      </div>
      <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0 ml-3 ${severityColor[incident.severity] ?? 'text-muted-foreground'}`}>
        {incident.severity}
      </span>
    </div>
  )
}

// ─── Work item row ────────────────────────────────────────────────────────────

const wiTypeColor: Record<string, string> = {
  Bug: 'text-red-500',
  UserStory: 'text-blue-500',
  Task: 'text-gray-500',
  Feature: 'text-green-500',
  Epic: 'text-purple-500',
}

function WorkItemRow({ item }: { item: ADOWorkItemEntity }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border last:border-0">
      <div className="flex items-center gap-3 min-w-0">
        <ClipboardList className={`w-4 h-4 flex-shrink-0 ${wiTypeColor[item.work_item_type] ?? 'text-muted-foreground'}`} />
        <span className="text-sm truncate">{item.title}</span>
      </div>
      <span className="text-xs text-muted-foreground flex-shrink-0 ml-3">{item.status}</span>
    </div>
  )
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

export function Dashboard() {
  const { data: state, isLoading, isError } = useUserState()
  const { mutate: invalidate, isPending: isRefreshing } = useInvalidateUserState()

  if (isLoading) {
    return (
      <div className="p-6 max-w-7xl space-y-8">
        <div className="h-8 w-48 bg-muted animate-pulse rounded" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => <EntityCardSkeleton key={i} />)}
        </div>
      </div>
    )
  }

  if (isError || !state) {
    return (
      <div className="p-6">
        <EmptyState
          title="Could not load your dashboard"
          description="We couldn't fetch your personalised state. Try refreshing."
          action={{ label: 'Retry', href: '#' }}
        />
      </div>
    )
  }

  const firstName = state.name.split(' ')[0]
  const computedAgo = formatDistanceToNow(new Date(state.computed_at))

  return (
    <div className="p-6 space-y-8 max-w-7xl">
      {/* Title row */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Welcome back{firstName ? `, ${firstName}` : ''}</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            {state.role} · updated {computedAgo} ago
          </p>
        </div>
        <button
          onClick={() => invalidate()}
          disabled={isRefreshing}
          className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* My Team */}
      {state.my_team && (
        <section>
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <Users className="w-5 h-5" /> My Team
          </h2>
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="font-medium">{state.my_team.name}</p>
            {state.my_team.description && (
              <p className="text-sm text-muted-foreground mt-1">{state.my_team.description}</p>
            )}
            <p className="text-xs text-muted-foreground mt-2">{state.my_team.members.length} members</p>
          </div>
        </section>
      )}

      {/* My Services */}
      <section>
        <h2 className="text-lg font-semibold mb-4">My Services</h2>
        {state.my_services.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {state.my_services.map((s) => (
              <EntityCard key={s.id} entity={{ ...s, entity_type: 'Service' as const }} />
            ))}
          </div>
        ) : (
          <EmptyState
            title="No services yet"
            description="Services owned by your team will appear here."
            action={{ label: 'Browse catalog', href: '/catalog' }}
          />
        )}
      </section>

      {/* Active Incidents + Work Items */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Active Incidents */}
        <div className="bg-card border border-border rounded-xl p-5">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-destructive" />
            Active Incidents
            {state.active_incidents.length > 0 && (
              <span className="ml-auto bg-destructive/10 text-destructive text-xs px-2 py-0.5 rounded-full">
                {state.active_incidents.length}
              </span>
            )}
          </h3>
          {state.active_incidents.length > 0 ? (
            state.active_incidents.map((i) => <IncidentRow key={i.id} incident={i} />)
          ) : (
            <p className="text-sm text-muted-foreground text-center py-4">No active incidents</p>
          )}
        </div>

        {/* Work Items */}
        <div className="bg-card border border-border rounded-xl p-5">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <ClipboardList className="w-4 h-4" />
            My Work Items
            {state.my_work_items.length > 0 && (
              <span className="ml-auto bg-muted text-muted-foreground text-xs px-2 py-0.5 rounded-full">
                {state.my_work_items.length}
              </span>
            )}
          </h3>
          {state.my_work_items.length > 0 ? (
            state.my_work_items.map((item) => <WorkItemRow key={item.id} item={item} />)
          ) : (
            <p className="text-sm text-muted-foreground text-center py-4">No open work items</p>
          )}
        </div>
      </div>
    </div>
  )
}
