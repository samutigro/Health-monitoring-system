import {
  Configuration,
  FetchError,
  MetricsApi,
  PatientsApi,
  ResponseError,
  SystemApi,
} from '@health-monitoring/api-client'

export const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const apiKey = import.meta.env.VITE_API_KEY ?? 'demo-secret-key'

const configuration = new Configuration({
  basePath: apiBaseUrl,
  apiKey,
})

export const api = {
  metrics: new MetricsApi(configuration),
  patients: new PatientsApi(configuration),
  system: new SystemApi(configuration),
}

type ApiErrorBody = {
  code?: string
  message?: string
  details?: Array<{
    field?: string
    issue?: string
  }>
}

export async function getApiErrorMessage(error: unknown): Promise<string> {
  if (error instanceof FetchError) {
    return `Cannot reach the backend at ${apiBaseUrl}. Check that FastAPI is running and CORS allows this frontend origin.`
  }

  if (error instanceof ResponseError) {
    let body: ApiErrorBody | undefined

    try {
      body = (await error.response.clone().json()) as ApiErrorBody
    } catch {
      body = undefined
    }

    if (body?.code && body.message) {
      const details = body.details
        ?.slice(0, 2)
        .map((detail) =>
          [detail.field, detail.issue].filter(Boolean).join(': '),
        )
        .filter(Boolean)
        .join(' | ')

      return details
        ? `${body.code}: ${body.message} (${details})`
        : `${body.code}: ${body.message}`
    }

    return `${error.response.status} ${error.response.statusText || 'API error'}`
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'Unexpected API error'
}
