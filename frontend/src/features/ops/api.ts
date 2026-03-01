import { apiGet } from '@/lib/api/client'

// ─── Health ───────────────────────────────────────────────────────────────────

export interface ServiceHealthSummary {
  service_id: string
  service_name: string
  health_status: 'Healthy' | 'Degraded' | 'Unavailable' | 'Unknown'
  open_incidents: number
  critical_incidents: number
  open_bugs: number
  open_work_items: number
  vulnerable_packages: number
  computed_at: string
}

export interface OpsHealthResponse {
  services: ServiceHealthSummary[]
  total_open_incidents: number
  total_critical_incidents: number
}

// ─── Change log ───────────────────────────────────────────────────────────────

export interface ChangeEvent {
  id: string
  event_type: string
  entity_id: string
  entity_name: string
  entity_kind: string
  summary: string
  actor: string
  occurred_at: string
  metadata: Record<string, unknown>
}

export interface ChangeLogResponse {
  events: ChangeEvent[]
  total: number
}

// ─── Impact analysis ──────────────────────────────────────────────────────────

export interface ImpactNode {
  entity_id: string
  entity_name: string
  entity_kind: string
  impact_level: 'direct' | 'transitive'
  relationship: string
}

export interface ImpactAnalysisResponse {
  root_entity_id: string
  root_entity_name: string
  affected: ImpactNode[]
  total_affected: number
}

// ─── API calls ────────────────────────────────────────────────────────────────

export function getOpsHealth(): Promise<OpsHealthResponse> {
  return apiGet<OpsHealthResponse>('api/v1/ops/health')
}

export function getChangeLog(limit = 50, entityId = ''): Promise<ChangeLogResponse> {
  const q = new URLSearchParams({ limit: String(limit) })
  if (entityId) q.set('entity_id', entityId)
  return apiGet<ChangeLogResponse>(`api/v1/ops/changelog?${q}`)
}

export function getImpactAnalysis(entityId: string, depth = 3): Promise<ImpactAnalysisResponse> {
  return apiGet<ImpactAnalysisResponse>(`api/v1/ops/impact/${entityId}?depth=${depth}`)
}
