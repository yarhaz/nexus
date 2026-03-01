// ─── Base ─────────────────────────────────────────────────────────────────────

export type EntityKind =
  | 'Service'
  | 'AzureResource'
  | 'Environment'
  | 'Team'
  | 'ApiEndpoint'
  | 'Package'
  | 'Incident'
  | 'ADOWorkItem'

// ─── Service (Phase 0) ────────────────────────────────────────────────────────

export type ServiceStatus = 'active' | 'deprecated' | 'experimental'
export type ServiceLifecycle = 'production' | 'staging' | 'development' | 'end-of-life'

export interface ServiceEntity {
  id: string
  entity_type: 'Service'
  name: string
  description: string
  team: string
  status: ServiceStatus
  lifecycle: ServiceLifecycle
  repository_url: string
  runbook_url: string
  tags: string[]
  created_at: string
  updated_at: string
}

// ─── AzureResource ────────────────────────────────────────────────────────────

export type HealthStatus = 'Healthy' | 'Degraded' | 'Unavailable' | 'Unknown'

export interface AzureResourceEntity {
  id: string
  entity_type: 'AzureResource'
  name: string
  resource_type: string
  sku: string
  region: string
  subscription_id: string
  resource_group: string
  azure_resource_id: string
  health_status: HealthStatus
  cost_stub: number
  tags: string[]
  created_at: string
  updated_at: string
}

// ─── Environment ──────────────────────────────────────────────────────────────

export type EnvironmentStage = 'dev' | 'staging' | 'prod' | 'dr'

export interface EnvironmentEntity {
  id: string
  entity_type: 'Environment'
  name: string
  stage: EnvironmentStage
  region: string
  subscription_id: string
  linked_services: string[]
  tags: string[]
  created_at: string
  updated_at: string
}

// ─── Team ─────────────────────────────────────────────────────────────────────

export interface TeamEntity {
  id: string
  entity_type: 'Team'
  name: string
  description: string
  entra_group_id: string
  members: string[]
  owned_services: string[]
  on_call_schedule: string
  tags: string[]
  created_at: string
  updated_at: string
}

// ─── ApiEndpoint ──────────────────────────────────────────────────────────────

export type AuthScheme = 'none' | 'api-key' | 'oauth2' | 'jwt'

export interface ApiEndpointEntity {
  id: string
  entity_type: 'ApiEndpoint'
  name: string
  description: string
  version: string
  base_url: string
  spec_url: string
  auth_scheme: AuthScheme
  sla: string
  consumers: string[]
  owner_service_id: string
  tags: string[]
  created_at: string
  updated_at: string
}

// ─── Package ──────────────────────────────────────────────────────────────────

export interface PackageEntity {
  id: string
  entity_type: 'Package'
  name: string
  description: string
  version: string
  license: string
  registry_url: string
  consumers: string[]
  cve_count: number
  cve_ids: string[]
  tags: string[]
  created_at: string
  updated_at: string
}

// ─── Incident ─────────────────────────────────────────────────────────────────

export type IncidentSeverity = 'critical' | 'high' | 'medium' | 'low'
export type IncidentStatus = 'open' | 'investigating' | 'resolved'

export interface IncidentEntity {
  id: string
  entity_type: 'Incident'
  title: string
  description: string
  severity: IncidentSeverity
  status: IncidentStatus
  affected_service_id: string
  started_at: string
  resolved_at: string | null
  mttr_minutes: number | null
  source: string
  source_id: string
  tags: string[]
  created_at: string
  updated_at: string
}

// ─── ADOWorkItem ──────────────────────────────────────────────────────────────

export type WorkItemType = 'Bug' | 'UserStory' | 'Task' | 'Feature' | 'Epic'

export interface ADOWorkItemEntity {
  id: string
  entity_type: 'ADOWorkItem'
  ado_id: number
  work_item_type: WorkItemType
  title: string
  description: string
  status: string
  sprint: string
  assignee: string
  linked_service_id: string
  iteration_path: string
  area_path: string
  tags: string[]
  created_at: string
  updated_at: string
}

// ─── Graph ────────────────────────────────────────────────────────────────────

export interface GraphNode {
  id: string
  label: string
  name: string
  entity_type: string
}

export interface GraphEdge {
  id: string
  source_id: string
  target_id: string
  relationship_type: string
}

export interface EntityGraph {
  root_id: string
  nodes: GraphNode[]
  edges: GraphEdge[]
}

// ─── User State ───────────────────────────────────────────────────────────────

export interface UserState {
  user_id: string
  name: string
  email: string
  role: string
  my_services: ServiceEntity[]
  my_team: TeamEntity | null
  active_incidents: IncidentEntity[]
  my_work_items: ADOWorkItemEntity[]
  my_prs: unknown[]
  my_deployments: unknown[]
  computed_at: string
}

// ─── Current user ─────────────────────────────────────────────────────────────

export interface CurrentUser {
  oid: string
  name: string
  email: string
  groups: string[]
  role: string
}

// ─── Shared pagination ────────────────────────────────────────────────────────

export interface CursorPage<T> {
  data: T[]
  meta: { next_cursor: string | null }
}
