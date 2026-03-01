import { apiGet, apiPost, apiPut, apiDelete } from '@/lib/api/client'
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
  UserState,
} from '@/types/entities'

// ─── Services ─────────────────────────────────────────────────────────────────

export interface ListParams {
  cursor?: string
  limit?: number
  search?: string
}

export async function listServices(params: ListParams = {}): Promise<{
  data: ServiceEntity[]
  next_cursor: string | null
  has_more: boolean
}> {
  const q = new URLSearchParams()
  if (params.cursor) q.set('cursor', params.cursor)
  if (params.limit) q.set('limit', String(params.limit))
  const url = `api/v1/catalog/services${q.toString() ? `?${q}` : ''}`
  return apiGet<{ data: ServiceEntity[]; next_cursor: string | null; has_more: boolean }>(url)
}

export async function getService(id: string): Promise<ServiceEntity> {
  return apiGet<ServiceEntity>(`api/v1/catalog/services/${id}`)
}

export async function createService(data: Omit<ServiceEntity, 'id' | 'entity_type' | 'created_at' | 'updated_at'>): Promise<ServiceEntity> {
  return apiPost<ServiceEntity>('api/v1/catalog/services', data)
}

// ─── Generic entity list helper ───────────────────────────────────────────────

async function listEntities<T>(path: string, params: ListParams = {}): Promise<{
  data: T[]
  next_cursor: string | null
}> {
  const q = new URLSearchParams()
  if (params.cursor) q.set('cursor', params.cursor)
  if (params.limit) q.set('limit', String(params.limit))
  const url = `${path}${q.toString() ? `?${q}` : ''}`
  return apiGet<{ data: T[]; next_cursor: string | null }>(url)
}

async function getEntity<T>(path: string, id: string): Promise<T> {
  return apiGet<T>(`${path}/${id}`)
}

// ─── AzureResource ────────────────────────────────────────────────────────────

export const azureResources = {
  list: (p?: ListParams) => listEntities<AzureResourceEntity>('api/v1/entities/azure-resources', p),
  get: (id: string) => getEntity<AzureResourceEntity>('api/v1/entities/azure-resources', id),
  create: (data: Omit<AzureResourceEntity, 'id' | 'entity_type' | 'created_at' | 'updated_at'>) =>
    apiPost<AzureResourceEntity>('api/v1/entities/azure-resources', data),
  update: (id: string, data: Partial<AzureResourceEntity>) =>
    apiPut<AzureResourceEntity>(`api/v1/entities/azure-resources/${id}`, data),
  delete: (id: string) => apiDelete(`api/v1/entities/azure-resources/${id}`),
}

// ─── Environment ──────────────────────────────────────────────────────────────

export const environments = {
  list: (p?: ListParams) => listEntities<EnvironmentEntity>('api/v1/entities/environments', p),
  get: (id: string) => getEntity<EnvironmentEntity>('api/v1/entities/environments', id),
  create: (data: Omit<EnvironmentEntity, 'id' | 'entity_type' | 'created_at' | 'updated_at'>) =>
    apiPost<EnvironmentEntity>('api/v1/entities/environments', data),
  update: (id: string, data: Partial<EnvironmentEntity>) =>
    apiPut<EnvironmentEntity>(`api/v1/entities/environments/${id}`, data),
  delete: (id: string) => apiDelete(`api/v1/entities/environments/${id}`),
}

// ─── Team ─────────────────────────────────────────────────────────────────────

export const teams = {
  list: (p?: ListParams) => listEntities<TeamEntity>('api/v1/entities/teams', p),
  get: (id: string) => getEntity<TeamEntity>('api/v1/entities/teams', id),
  create: (data: Omit<TeamEntity, 'id' | 'entity_type' | 'created_at' | 'updated_at'>) =>
    apiPost<TeamEntity>('api/v1/entities/teams', data),
  update: (id: string, data: Partial<TeamEntity>) =>
    apiPut<TeamEntity>(`api/v1/entities/teams/${id}`, data),
  delete: (id: string) => apiDelete(`api/v1/entities/teams/${id}`),
}

// ─── ApiEndpoint ──────────────────────────────────────────────────────────────

export const apiEndpoints = {
  list: (p?: ListParams) => listEntities<ApiEndpointEntity>('api/v1/entities/api-endpoints', p),
  get: (id: string) => getEntity<ApiEndpointEntity>('api/v1/entities/api-endpoints', id),
  create: (data: Omit<ApiEndpointEntity, 'id' | 'entity_type' | 'created_at' | 'updated_at'>) =>
    apiPost<ApiEndpointEntity>('api/v1/entities/api-endpoints', data),
  update: (id: string, data: Partial<ApiEndpointEntity>) =>
    apiPut<ApiEndpointEntity>(`api/v1/entities/api-endpoints/${id}`, data),
  delete: (id: string) => apiDelete(`api/v1/entities/api-endpoints/${id}`),
}

// ─── Package ──────────────────────────────────────────────────────────────────

export const packages = {
  list: (p?: ListParams) => listEntities<PackageEntity>('api/v1/entities/packages', p),
  get: (id: string) => getEntity<PackageEntity>('api/v1/entities/packages', id),
  create: (data: Omit<PackageEntity, 'id' | 'entity_type' | 'created_at' | 'updated_at'>) =>
    apiPost<PackageEntity>('api/v1/entities/packages', data),
  update: (id: string, data: Partial<PackageEntity>) =>
    apiPut<PackageEntity>(`api/v1/entities/packages/${id}`, data),
  delete: (id: string) => apiDelete(`api/v1/entities/packages/${id}`),
}

// ─── Incident ─────────────────────────────────────────────────────────────────

export const incidents = {
  list: (p?: ListParams) => listEntities<IncidentEntity>('api/v1/entities/incidents', p),
  get: (id: string) => getEntity<IncidentEntity>('api/v1/entities/incidents', id),
  create: (data: Omit<IncidentEntity, 'id' | 'entity_type' | 'created_at' | 'updated_at'>) =>
    apiPost<IncidentEntity>('api/v1/entities/incidents', data),
  update: (id: string, data: Partial<IncidentEntity>) =>
    apiPut<IncidentEntity>(`api/v1/entities/incidents/${id}`, data),
  delete: (id: string) => apiDelete(`api/v1/entities/incidents/${id}`),
}

// ─── ADOWorkItem ──────────────────────────────────────────────────────────────

export const adoWorkItems = {
  list: (p?: ListParams) => listEntities<ADOWorkItemEntity>('api/v1/entities/ado-work-items', p),
  get: (id: string) => getEntity<ADOWorkItemEntity>('api/v1/entities/ado-work-items', id),
  create: (data: Omit<ADOWorkItemEntity, 'id' | 'entity_type' | 'created_at' | 'updated_at'>) =>
    apiPost<ADOWorkItemEntity>('api/v1/entities/ado-work-items', data),
  update: (id: string, data: Partial<ADOWorkItemEntity>) =>
    apiPut<ADOWorkItemEntity>(`api/v1/entities/ado-work-items/${id}`, data),
  delete: (id: string) => apiDelete(`api/v1/entities/ado-work-items/${id}`),
}

// ─── Graph ────────────────────────────────────────────────────────────────────

export async function getEntityGraph(entityId: string, depth = 2): Promise<EntityGraph> {
  return apiGet<EntityGraph>(`api/v1/relationships/graph/${entityId}?depth=${depth}`)
}

// ─── User State ───────────────────────────────────────────────────────────────

export async function getMyState(): Promise<UserState> {
  return apiGet<UserState>('api/v1/userstate/me')
}
