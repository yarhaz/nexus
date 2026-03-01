import { motion } from 'framer-motion'
import { Link } from '@tanstack/react-router'
import {
  GitBranch,
  Users,
  Tag,
  Cloud,
  Layers,
  Globe,
  Package,
  AlertTriangle,
  ClipboardList,
  Server,
} from 'lucide-react'
import { cn } from '@/lib/utils/cn'
import type {
  ServiceEntity,
  AzureResourceEntity,
  EnvironmentEntity,
  TeamEntity,
  ApiEndpointEntity,
  PackageEntity,
  IncidentEntity,
  ADOWorkItemEntity,
  EntityKind,
} from '@/types/entities'

type AnyEntity =
  | ServiceEntity
  | AzureResourceEntity
  | EnvironmentEntity
  | TeamEntity
  | ApiEndpointEntity
  | PackageEntity
  | IncidentEntity
  | ADOWorkItemEntity

interface Props {
  entity: AnyEntity
  // legacy prop kept for backward compat
  service?: ServiceEntity
}

// ─── Per-type metadata ───────────────────────────────────────────────────────

const kindIcon: Record<EntityKind, React.ElementType> = {
  Service: Server,
  AzureResource: Cloud,
  Environment: Layers,
  Team: Users,
  ApiEndpoint: Globe,
  Package: Package,
  Incident: AlertTriangle,
  ADOWorkItem: ClipboardList,
}

const kindColor: Record<EntityKind, string> = {
  Service: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
  AzureResource: 'bg-sky-500/10 text-sky-600 dark:text-sky-400',
  Environment: 'bg-violet-500/10 text-violet-600 dark:text-violet-400',
  Team: 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400',
  ApiEndpoint: 'bg-teal-500/10 text-teal-600 dark:text-teal-400',
  Package: 'bg-orange-500/10 text-orange-600 dark:text-orange-400',
  Incident: 'bg-red-500/10 text-red-600 dark:text-red-400',
  ADOWorkItem: 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400',
}

// ─── Status dot ──────────────────────────────────────────────────────────────

function getStatusDot(entity: AnyEntity): string {
  if (entity.entity_type === 'Service') {
    const s = entity as ServiceEntity
    return s.status === 'active' ? 'bg-green-500' : s.status === 'deprecated' ? 'bg-orange-500' : 'bg-purple-500'
  }
  if (entity.entity_type === 'Incident') {
    const i = entity as IncidentEntity
    return i.status === 'resolved' ? 'bg-green-500' : i.severity === 'critical' ? 'bg-red-500' : 'bg-orange-500'
  }
  if (entity.entity_type === 'AzureResource') {
    const r = entity as AzureResourceEntity
    return r.health_status === 'Healthy' ? 'bg-green-500' : r.health_status === 'Degraded' ? 'bg-orange-500' : 'bg-gray-400'
  }
  return 'bg-green-500'
}

// ─── Subtitle ────────────────────────────────────────────────────────────────

function getSubtitle(entity: AnyEntity): string {
  switch (entity.entity_type) {
    case 'Service': return (entity as ServiceEntity).lifecycle
    case 'AzureResource': return (entity as AzureResourceEntity).resource_type || (entity as AzureResourceEntity).region
    case 'Environment': return (entity as EnvironmentEntity).stage
    case 'Team': return `${(entity as TeamEntity).members.length} members`
    case 'ApiEndpoint': return `v${(entity as ApiEndpointEntity).version}`
    case 'Package': return (entity as PackageEntity).version || (entity as PackageEntity).license
    case 'Incident': return (entity as IncidentEntity).severity
    case 'ADOWorkItem': return (entity as ADOWorkItemEntity).work_item_type
    default: return ''
  }
}

// ─── Entity name ─────────────────────────────────────────────────────────────

function getEntityName(entity: AnyEntity): string {
  if ('name' in entity) return (entity as { name: string }).name
  if ('title' in entity) return (entity as IncidentEntity | ADOWorkItemEntity).title
  return entity.id
}

// ─── Description ─────────────────────────────────────────────────────────────

function getDescription(entity: AnyEntity): string {
  if ('description' in entity) return (entity as { description: string }).description
  return ''
}

// ─── Tags ────────────────────────────────────────────────────────────────────

function getTags(entity: AnyEntity): string[] {
  return 'tags' in entity ? (entity as { tags: string[] }).tags : []
}

// ─── Component ───────────────────────────────────────────────────────────────

export function EntityCard({ entity: entityProp, service }: Props) {
  // Support legacy `service` prop
  const entity: AnyEntity = entityProp ?? (service ? { ...service, entity_type: 'Service' as const } : ({} as AnyEntity))

  const kind = entity.entity_type as EntityKind
  const Icon = kindIcon[kind] ?? Server
  const colorClass = kindColor[kind] ?? 'bg-muted text-muted-foreground'
  const subtitle = getSubtitle(entity)
  const name = getEntityName(entity)
  const description = getDescription(entity)
  const tags = getTags(entity)

  return (
    <motion.div whileHover={{ y: -2 }} transition={{ type: 'spring', stiffness: 400, damping: 30 }}>
      <Link
        to="/catalog/$entityId"
        params={{ entityId: entity.id }}
        className="block bg-card border border-border rounded-xl p-5 hover:border-primary/50 hover:shadow-md transition-all duration-200"
      >
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2 min-w-0">
            <div className={cn('w-2 h-2 rounded-full flex-shrink-0', getStatusDot(entity))} />
            <h3 className="font-semibold text-foreground truncate">{name}</h3>
          </div>
          <span className={cn('flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0', colorClass)}>
            <Icon className="w-3 h-3" />
            {subtitle}
          </span>
        </div>

        {description && (
          <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{description}</p>
        )}

        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className={cn('flex items-center gap-1 font-medium', colorClass)}>
            <Icon className="w-3 h-3" />
            {kind}
          </span>
          {entity.entity_type === 'Service' && (entity as ServiceEntity).repository_url && (
            <span className="flex items-center gap-1">
              <GitBranch className="w-3 h-3" /> Repo
            </span>
          )}
          {tags.length > 0 && (
            <span className="flex items-center gap-1">
              <Tag className="w-3 h-3" />
              {tags.slice(0, 2).join(', ')}
              {tags.length > 2 && ` +${tags.length - 2}`}
            </span>
          )}
        </div>
      </Link>
    </motion.div>
  )
}
