// A small fetch wrapper: JSON in and out, the bearer token, one automatic token renewal on 401,
// and the backend's error format ({"error": {code, message, details}}) as ApiError.
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details: Record<string, unknown> = {},
  ) {
    super(message)
  }

  /** Field-level messages from a 422, e.g. {"systolic_bp": "…"} */
  get fieldErrors(): Record<string, string> {
    const fields = (this.details.fields as { field: string; message: string }[] | undefined) ?? []
    const byField = Object.fromEntries(fields.map((f) => [f.field, f.message]))
    if (typeof this.details.field === 'string') byField[this.details.field] = this.message
    return byField
  }
}

export interface Session {
  accessToken(): string | null
  /**
   * Renew the access token; false if the session is over (the user must sign in again).
   * Throws when the server can't be reached: the request fails, and the session is kept.
   */
  renew(): Promise<boolean>
  onSignedOut(): void
}

let session: Session | null = null
let renewing: Promise<boolean> | null = null

export function useSession(s: Session) {
  session = s
}

const BASE = '/api/v1'

type Options = { method?: string; json?: unknown; form?: FormData; query?: Record<string, unknown>; auth?: boolean }

async function send(path: string, opts: Options): Promise<Response> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  const token = opts.auth === false ? null : session?.accessToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let body: BodyInit | undefined
  if (opts.json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(opts.json)
  } else if (opts.form) {
    body = opts.form
  }
  const query = new URLSearchParams()
  for (const [k, v] of Object.entries(opts.query ?? {})) {
    if (v !== undefined && v !== null && v !== '') query.set(k, String(v))
  }
  const url = BASE + path + (query.size ? `?${query}` : '')
  return fetch(url, { method: opts.method ?? 'GET', headers, body })
}

async function toError(response: Response): Promise<ApiError> {
  try {
    const { error } = await response.json()
    return new ApiError(response.status, error.code, error.message, error.details ?? {})
  } catch {
    return new ApiError(response.status, 'network_error', response.statusText || 'Request failed')
  }
}

async function request(path: string, opts: Options = {}): Promise<Response> {
  let response: Response
  try {
    response = await send(path, opts)
  } catch {
    throw new ApiError(0, 'network_error', 'The server could not be reached.')
  }
  if (response.status === 401 && opts.auth !== false && session) {
    // Several requests may hit an expired token at once: renew it only once.
    renewing ??= session.renew().finally(() => (renewing = null))
    if (await renewing) {
      response = await send(path, opts)
    } else {
      session.onSignedOut()
    }
  }
  if (!response.ok) throw await toError(response)
  return response
}

export async function api<T>(path: string, opts: Options = {}): Promise<T> {
  const response = await request(path, opts)
  // 204, and 201s like "note added", have no body.
  const text = await response.text()
  return (text ? JSON.parse(text) : undefined) as T
}

/** For files: the bytes, ready for URL.createObjectURL. */
export async function apiBlob(path: string): Promise<Blob> {
  return (await request(path)).blob()
}
