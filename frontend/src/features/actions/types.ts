export type ExecutorType = 'ado_pipeline' | 'github_actions' | 'http_webhook' | 'azure_function' | 'manual'
export type ExecutionStatus =
  | 'pending_approval'
  | 'approved'
  | 'running'
  | 'succeeded'
  | 'failed'
  | 'rejected'
  | 'expired'
  | 'cancelled'

export interface ActionParameter {
  name: string
  label: string
  type: 'string' | 'integer' | 'boolean' | 'select'
  required: boolean
  default: unknown
  options: string[]
  description: string
  secret: boolean
}

export interface ApprovalConfig {
  required: boolean
  approvers: string[]
  timeout_minutes: number
  auto_approve_roles: string[]
}

export interface ActionManifest {
  id: string
  name: string
  description: string
  category: string
  executor_type: ExecutorType
  executor_config: Record<string, unknown>
  parameters: ActionParameter[]
  approval: ApprovalConfig
  allowed_roles: string[]
  target_entity_types: string[]
  tags: string[]
  enabled: boolean
  created_by: string
  created_at: string
  updated_at: string
}

export interface ActionExecution {
  id: string
  action_id: string
  action_name: string
  target_entity_id: string
  parameters: Record<string, unknown>
  comment: string
  status: ExecutionStatus
  triggered_by: string
  triggered_by_name: string
  approved_by: string
  rejected_by: string
  rejection_reason: string
  executor_run_id: string
  result: Record<string, unknown>
  error_message: string
  started_at: string | null
  completed_at: string | null
  expires_at: string | null
  created_at: string
  updated_at: string
}

export interface ExecutionRequest {
  action_id: string
  target_entity_id?: string
  parameters: Record<string, unknown>
  comment?: string
}
