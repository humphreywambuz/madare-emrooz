import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { api, ApiError, useSession } from '@/api/client'

function json(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

describe('api client', () => {
  let token = 'old'
  const renew = vi.fn(async () => {
    token = 'new'
    return true
  })
  const onSignedOut = vi.fn()

  beforeEach(() => {
    token = 'old'
    renew.mockClear()
    onSignedOut.mockClear()
    useSession({ accessToken: () => token, renew, onSignedOut })
  })
  afterEach(() => vi.unstubAllGlobals())

  it('renews an expired token once for parallel requests and retries them', async () => {
    const fetchMock = vi.fn(async (_url: string, init: RequestInit) => {
      const auth = (init.headers as Record<string, string>).Authorization
      return auth === 'Bearer new' ? json(200, { ok: true }) : json(401, { error: { code: 'unauthenticated', message: 'expired' } })
    })
    vi.stubGlobal('fetch', fetchMock)
    const results = await Promise.all([api('/a'), api('/b'), api('/c')])
    expect(results).toEqual([{ ok: true }, { ok: true }, { ok: true }])
    expect(renew).toHaveBeenCalledTimes(1)
    expect(onSignedOut).not.toHaveBeenCalled()
  })

  it('signs out when the session cannot be renewed', async () => {
    renew.mockResolvedValueOnce(false)
    vi.stubGlobal('fetch', vi.fn(async () => json(401, { error: { code: 'unauthenticated', message: 'no' } })))
    await expect(api('/a')).rejects.toBeInstanceOf(ApiError)
    expect(onSignedOut).toHaveBeenCalledTimes(1)
  })

  it('turns the backend error format into ApiError with field messages', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => json(422, {
      error: { code: 'validation_error', message: 'The request body is invalid.', details: { fields: [{ field: 'systolic_bp', message: 'too high' }] } },
    })))
    const error = (await api('/a').catch((e) => e)) as ApiError
    expect(error.status).toBe(422)
    expect(error.code).toBe('validation_error')
    expect(error.fieldErrors).toEqual({ systolic_bp: 'too high' })
  })

  it('reports an unreachable server', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new TypeError('Failed to fetch') }))
    const error = (await api('/a').catch((e) => e)) as ApiError
    expect(error.code).toBe('network_error')
  })

  it('accepts a 201 with no body', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(null, { status: 201 })))
    await expect(api('/notes', { method: 'POST', json: { body: 'x' } })).resolves.toBeUndefined()
  })

  it('sends JSON, query strings and 204s', async () => {
    const fetchMock = vi.fn(async () => new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)
    await expect(api('/x', { method: 'POST', json: { a: 1 }, query: { q: 'سارا', page: 2, empty: '' } })).resolves.toBeUndefined()
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('/api/v1/x?q=%D8%B3%D8%A7%D8%B1%D8%A7&page=2')
    expect(init.body).toBe('{"a":1}')
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer old')
  })
})
