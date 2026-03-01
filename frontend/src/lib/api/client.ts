import ky, { type KyInstance, type Options } from 'ky'
import { v4 as uuidv4 } from 'uuid'
import { ApiClientError, type ApiResponse } from '@/types/api'

type TokenProvider = () => Promise<string | null>

let _tokenProvider: TokenProvider = async () => null

export function setTokenProvider(provider: TokenProvider) {
  _tokenProvider = provider
}

const baseClient = ky.create({
  prefixUrl: import.meta.env.VITE_API_URL || '',
  timeout: 30_000,
  retry: {
    limit: 2,
    methods: ['get'],
    statusCodes: [408, 429, 500, 502, 503, 504],
  },
  hooks: {
    beforeRequest: [
      async (request) => {
        const correlationId = uuidv4()
        request.headers.set('X-Correlation-ID', correlationId)

        const token = await _tokenProvider()
        if (token) {
          request.headers.set('Authorization', `Bearer ${token}`)
        }
      },
    ],
    afterResponse: [
      async (_request, _options, response) => {
        if (!response.ok) {
          let body: Partial<ApiResponse<unknown>> = {}
          try {
            body = await response.clone().json()
          } catch {}

          const err = body.error
          const correlationId =
            response.headers.get('X-Correlation-ID') ||
            err?.correlation_id ||
            'unknown'

          throw new ApiClientError(
            err?.code || 'HTTP_ERROR',
            err?.message || `HTTP ${response.status}`,
            correlationId,
            err?.details || {},
            response.status,
          )
        }
      },
    ],
  },
})

export async function apiGet<T>(url: string, options?: Options): Promise<T> {
  const response = await baseClient.get(url, options).json<ApiResponse<T>>()
  return response.data as T
}

export async function apiPost<T>(url: string, body: unknown, options?: Options): Promise<T> {
  const response = await baseClient.post(url, { json: body, ...options }).json<ApiResponse<T>>()
  return response.data as T
}

export async function apiPut<T>(url: string, body: unknown, options?: Options): Promise<T> {
  const response = await baseClient.put(url, { json: body, ...options }).json<ApiResponse<T>>()
  return response.data as T
}

export async function apiDelete(url: string, options?: Options): Promise<void> {
  await baseClient.delete(url, options)
}

export { baseClient }
