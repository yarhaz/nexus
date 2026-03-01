export interface ApiResponse<T> {
  data: T | null
  meta: {
    next_cursor?: string | null
    has_more?: boolean
    total?: number
  }
  error: ApiError | null
}

export interface ApiError {
  code: string
  message: string
  details: Record<string, unknown>
  correlation_id: string
  timestamp: string
}

export class ApiClientError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly correlationId: string,
    public readonly details: Record<string, unknown> = {},
    public readonly statusCode: number = 500,
  ) {
    super(message)
    this.name = 'ApiClientError'
  }
}

export interface CursorPage<T> {
  data: T[]
  next_cursor: string | null
  has_more: boolean
  total?: number
}
