import { createFileRoute, Link } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { ErrorBoundary } from '@/components/shared/ErrorBoundary'
import { EntityCardSkeleton } from '@/features/catalog/EntityCardSkeleton'
import {
  ArrowLeft,
  GitBranch,
  BookOpen,
  Tag,
  Users,
  Clock,
  Cloud,
  Globe,
  AlertTriangle,
  Package,
  ClipboardList,
  Layers,
  ExternalLink,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { RelationshipGraph } from '@/features/catalog/RelationshipGraph'
import { ScorecardPanel } from '@/features/scorecards/ScorecardPanel'
import { useImpactAnalysis } from '@/features/ops/useOps'
import {
  getService,
  azureResources,
  environments,
  teams,
  apiEndpoints,
  packages,
  incidents,
  adoWorkItems,
  getEntityGraph,
} from '@/features/catalog/api'
import type {
  ServiceEntity,
  AzureResourceEntity,
  EnvironmentEntity,
  TeamEntity,
  ApiEndpointEntity,
  PackageEntity,
  IncidentEntity,
  ADOWorkItemEntity,
  EntityGraph,
} from '@/types/entities'

export const Route = createFileRoute('/catalog/$entityId')({
  component: EntityDetailPage,
})

// ─── Entity fetch (try all entity types) ─────────────────────────────────────

type AnyEntity =
  | ServiceEntity
  | AzureResourceEntity
  | EnvironmentEntity
  | TeamEntity
  | ApiEndpointEntity
  | PackageEntity
  | IncidentEntity
  | ADOWorkItemEntity

async function fetchAnyEntity(id: string): Promise<AnyEntity> {
  const fetchers = [
    () => getService(id).then((e) => ({ ...e, entity_type: 'Service' as const })),
    () => azureResources.get(id),
    () => environments.get(id),
    () => teams.get(id),
    () => apiEndpoints.get(id),
    () => packages.get(id),
    () => incidents.get(id),
    () => adoWorkItems.get(id),
  ]

  for (const fetch of fetchers) {
    try {
      return await fetch()
    } catch {
      // Try next type
    }
  }
  throw new Error(`Entity '${id}' not found in any catalog`)
}

// ─── Section helpers ─────────────────────────────────────────────────────────

function Row({ label, value, href }: { label: string; value?: string | number | null; href?: string }) {
  if (!value && value !== 0) return null
  return (
    <div className="flex items-center justify-between py-2 border-b border-border last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      {href ? (
        <a href={href} target="_blank" rel="noopener noreferrer"
          className="flex items-center gap-1 text-sm text-primary hover:underline">
          {String(value)} <ExternalLink className="w-3 h-3" />
        </a>
      ) : (
        <span className="text-sm font-medium">{String(value)}</span>
      )}
    </div>
  )
}

function Tags({ tags }: { tags?: string[] }) {
  if (!tags?.length) return null
  return (
    <div className="flex items-center gap-2 flex-wrap mt-4">
      <Tag className="w-4 h-4 text-muted-foreground" />
      {tags.map((tag) => (
        <span key={tag} className="bg-muted text-muted-foreground text-xs px-2 py-1 rounded-full">{tag}</span>
      ))}
    </div>
  )
}

// ─── Per-type detail panels ───────────────────────────────────────────────────

function ServiceDetail({ e }: { e: ServiceEntity }) {
  return (
    <div className="space-y-1">
      <Row label="Team" value={e.team} />
      <Row label="Status" value={e.status} />
      <Row label="Lifecycle" value={e.lifecycle} />
      <Row label="Repository" value={e.repository_url ? 'View' : undefined} href={e.repository_url || undefined} />
      <Row label="Runbook" value={e.runbook_url ? 'View' : undefined} href={e.runbook_url || undefined} />
    </div>
  )
}

function AzureResourceDetail({ e }: { e: AzureResourceEntity }) {
  return (
    <div className="space-y-1">
      <Row label="Type" value={e.resource_type} />
      <Row label="SKU" value={e.sku} />
      <Row label="Region" value={e.region} />
      <Row label="Resource Group" value={e.resource_group} />
      <Row label="Subscription" value={e.subscription_id} />
      <Row label="Health" value={e.health_status} />
      <Row label="Cost (stub)" value={e.cost_stub ? `$${e.cost_stub.toFixed(2)}` : undefined} />
    </div>
  )
}

function EnvironmentDetail({ e }: { e: EnvironmentEntity }) {
  return (
    <div className="space-y-1">
      <Row label="Stage" value={e.stage} />
      <Row label="Region" value={e.region} />
      <Row label="Subscription" value={e.subscription_id} />
      <Row label="Linked Services" value={e.linked_services.length || undefined} />
    </div>
  )
}

function TeamDetail({ e }: { e: TeamEntity }) {
  return (
    <div className="space-y-1">
      <Row label="Members" value={e.members.length} />
      <Row label="Owned Services" value={e.owned_services.length} />
      <Row label="On-Call" value={e.on_call_schedule ? 'Configured' : undefined} href={e.on_call_schedule || undefined} />
      <Row label="Entra Group" value={e.entra_group_id} />
    </div>
  )
}

function ApiEndpointDetail({ e }: { e: ApiEndpointEntity }) {
  return (
    <div className="space-y-1">
      <Row label="Version" value={e.version} />
      <Row label="Base URL" value={e.base_url} href={e.base_url || undefined} />
      <Row label="Spec" value={e.spec_url ? 'OpenAPI' : undefined} href={e.spec_url || undefined} />
      <Row label="Auth" value={e.auth_scheme} />
      <Row label="SLA" value={e.sla} />
      <Row label="Consumers" value={e.consumers.length || undefined} />
    </div>
  )
}

function PackageDetail({ e }: { e: PackageEntity }) {
  return (
    <div className="space-y-1">
      <Row label="Version" value={e.version} />
      <Row label="License" value={e.license} />
      <Row label="Registry" value={e.registry_url ? 'View' : undefined} href={e.registry_url || undefined} />
      <Row label="Consumers" value={e.consumers.length || undefined} />
      <Row label="CVEs" value={e.cve_count || undefined} />
    </div>
  )
}

function IncidentDetail({ e }: { e: IncidentEntity }) {
  return (
    <div className="space-y-1">
      <Row label="Severity" value={e.severity} />
      <Row label="Status" value={e.status} />
      <Row label="Affected Service" value={e.affected_service_id} />
      <Row label="Source" value={e.source} />
      <Row label="MTTR" value={e.mttr_minutes != null ? `${e.mttr_minutes} min` : undefined} />
      <Row label="Started" value={formatDistanceToNow(new Date(e.started_at)) + ' ago'} />
      {e.resolved_at && <Row label="Resolved" value={formatDistanceToNow(new Date(e.resolved_at)) + ' ago'} />}
    </div>
  )
}

function ADOWorkItemDetail({ e }: { e: ADOWorkItemEntity }) {
  return (
    <div className="space-y-1">
      <Row label="Type" value={e.work_item_type} />
      <Row label="Status" value={e.status} />
      <Row label="Assignee" value={e.assignee} />
      <Row label="Sprint" value={e.sprint} />
      <Row label="ADO ID" value={e.ado_id || undefined} />
      <Row label="Area" value={e.area_path} />
    </div>
  )
}

function EntityDetails({ entity }: { entity: AnyEntity }) {
  switch (entity.entity_type) {
    case 'Service': return <ServiceDetail e={entity as ServiceEntity} />
    case 'AzureResource': return <AzureResourceDetail e={entity as AzureResourceEntity} />
    case 'Environment': return <EnvironmentDetail e={entity as EnvironmentEntity} />
    case 'Team': return <TeamDetail e={entity as TeamEntity} />
    case 'ApiEndpoint': return <ApiEndpointDetail e={entity as ApiEndpointEntity} />
    case 'Package': return <PackageDetail e={entity as PackageEntity} />
    case 'Incident': return <IncidentDetail e={entity as IncidentEntity} />
    case 'ADOWorkItem': return <ADOWorkItemDetail e={entity as ADOWorkItemEntity} />
    default: return null
  }
}

const entityTypeIcon: Record<string, React.ElementType> = {
  Service: GitBranch,
  AzureResource: Cloud,
  Environment: Layers,
  Team: Users,
  ApiEndpoint: Globe,
  Package: Package,
  Incident: AlertTriangle,
  ADOWorkItem: ClipboardList,
}

function getEntityName(entity: AnyEntity): string {
  if ('name' in entity) return (entity as { name: string }).name
  if ('title' in entity) return (entity as { title: string }).title
  return entity.id
}

function getEntityDescription(entity: AnyEntity): string {
  if ('description' in entity) return (entity as { description: string }).description
  return ''
}

// ─── Graph view ───────────────────────────────────────────────────────────────

function GraphSection({ graph }: { graph: EntityGraph }) {
  if (graph.nodes.length <= 1) return null
  return (
    <div className="bg-card border border-border rounded-xl p-5 mt-6">
      <h2 className="font-semibold mb-4">
        Relationship Graph
        <span className="ml-2 text-xs text-muted-foreground font-normal">
          {graph.nodes.length} nodes · {graph.edges.length} edges · click to navigate
        </span>
      </h2>
      <RelationshipGraph graph={graph} />
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

function EntityDetailPage() {
  const { entityId } = Route.useParams()

  const { data: entity, isLoading, isError, error } = useQuery({
    queryKey: ['catalog', 'entity', entityId],
    queryFn: () => fetchAnyEntity(entityId),
    enabled: !!entityId,
  })

  const { data: graph } = useQuery({
    queryKey: ['catalog', 'graph', entityId],
    queryFn: () => getEntityGraph(entityId),
    enabled: !!entity,
  })

  if (isLoading) {
    return (
      <div className="p-6 max-w-4xl">
        <div className="h-6 w-24 bg-muted rounded mb-6 animate-pulse" />
        <EntityCardSkeleton />
      </div>
    )
  }

  if (isError || !entity) {
    return (
      <div className="p-6">
        <p className="text-destructive">{(error as Error)?.message || 'Entity not found'}</p>
      </div>
    )
  }

  const name = getEntityName(entity)
  const description = getEntityDescription(entity)
  const tags = 'tags' in entity ? (entity as { tags: string[] }).tags : []
  const updatedAt = 'updated_at' in entity ? entity.updated_at : null
  const TypeIcon = entityTypeIcon[entity.entity_type] ?? BookOpen

  return (
    <ErrorBoundary>
      <div className="p-6 max-w-4xl">
        <Link to="/catalog" className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-6">
          <ArrowLeft className="w-4 h-4" /> Back to catalog
        </Link>

        <div className="bg-card border border-border rounded-xl p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-primary/10 rounded-lg mt-0.5">
                <TypeIcon className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">{name}</h1>
                <span className="text-sm text-muted-foreground font-medium">{entity.entity_type}</span>
                {description && <p className="text-muted-foreground mt-1">{description}</p>}
              </div>
            </div>
            {updatedAt && (
              <span className="text-xs text-muted-foreground flex items-center gap-1 flex-shrink-0">
                <Clock className="w-3 h-3" />
                {formatDistanceToNow(new Date(updatedAt))} ago
              </span>
            )}
          </div>

          <EntityDetails entity={entity} />
          <Tags tags={tags} />
        </div>

        {graph && <GraphSection graph={graph} />}

        {entity.entity_type === 'Service' && (
          <>
            <ImpactSection entityId={entity.id} />
            <div className="bg-card border border-border rounded-xl p-5 mt-6">
              <h2 className="font-semibold mb-4">Scorecards</h2>
              <ScorecardPanel serviceId={entity.id} />
            </div>
          </>
        )}
      </div>
    </ErrorBoundary>
  )
}

function ImpactSection({ entityId }: { entityId: string }) {
  const { data: impact } = useImpactAnalysis(entityId)
  if (!impact || impact.total_affected === 0) return null
  return (
    <div className="bg-card border border-border rounded-xl p-5 mt-6">
      <h2 className="font-semibold mb-1">Blast Radius</h2>
      <p className="text-sm text-muted-foreground mb-4">
        {impact.total_affected} entit{impact.total_affected === 1 ? 'y' : 'ies'} potentially affected by an incident on this service.
      </p>
      <div className="space-y-2">
        {impact.affected.map(node => (
          <div key={node.entity_id} className="flex items-center gap-3 text-sm">
            <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${node.impact_level === 'direct' ? 'bg-red-500' : 'bg-yellow-500'}`} />
            <span className="font-medium">{node.entity_name}</span>
            <span className="text-muted-foreground">{node.entity_kind}</span>
            {node.relationship && (
              <span className="text-xs bg-muted px-1.5 py-0.5 rounded">{node.relationship}</span>
            )}
            <span className="ml-auto text-xs text-muted-foreground capitalize">{node.impact_level}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
