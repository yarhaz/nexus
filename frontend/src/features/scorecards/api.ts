import { apiGet } from '@/lib/api/client'

export interface ScorecardRule {
  id: string
  name: string
  description: string
  weight: number
  check_type: string
  check_config: Record<string, unknown>
  remedy_url: string
}

export interface ScorecardTemplate {
  id: string
  name: string
  description: string
  applies_to: string[]
  rules: ScorecardRule[]
}

export interface RuleResult {
  rule_id: string
  rule_name: string
  passed: boolean
  weight: number
  remedy_url: string
  reason: string
}

export interface ScorecardResult {
  id: string
  template_id: string
  template_name: string
  entity_id: string
  entity_name: string
  entity_kind: string
  score: number
  max_score: number
  percentage: number
  level: 'bronze' | 'silver' | 'gold' | 'platinum' | 'failing'
  rules: RuleResult[]
  evaluated_at: string
}

export function listTemplates(): Promise<ScorecardTemplate[]> {
  return apiGet<ScorecardTemplate[]>('api/v1/scorecards/templates')
}

export function getTemplate(id: string): Promise<ScorecardTemplate> {
  return apiGet<ScorecardTemplate>(`api/v1/scorecards/templates/${id}`)
}

export function scoreService(serviceId: string): Promise<ScorecardResult[]> {
  return apiGet<ScorecardResult[]>(`api/v1/scorecards/services/${serviceId}`)
}

export function scoreAllServices(): Promise<ScorecardResult[]> {
  return apiGet<ScorecardResult[]>('api/v1/scorecards/services')
}
