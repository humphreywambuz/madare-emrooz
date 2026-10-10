import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '@/api/client'
import { useAuth } from '@/stores/auth'

const REFRESH_KEY = 'madare.refresh'

function json(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

const tokens = (n: number) => ({
  access_token: `access-${n}`, refresh_token: `refresh-${n}`, token_type: 'Bearer', expires_in: 900,
  user: { id: 'u1', role: 'midwife' },
})
const staffMe = { id: 'u1', mobile: '+989120000002', role: 'midwife', first_name: 'مریم', last_name: 'احمدی' }

const expired = () => json(401, { error: { code: 'unauthenticated', message: 'expired' } })

/**
 * A fake backend. Sign-in gives access-1, which works for /staff/me but has expired by the time
 * /staff/patients is asked for, so that request needs a renewal; `refresh` answers the renewal.
 */
function backend(refresh: (token: string) => Response | Promise<Response>) {
  const fetchMock = vi.fn(async (url: string, init: RequestInit) => {
    const auth = (init.headers as Record<string, string>).Authorization
    if (url.endsWith('/auth/otp/verify')) return json(200, tokens(1))
    if (url.endsWith('/auth/token/refresh')) return refresh(JSON.parse(init.body as string).refresh_token)
    if (url.endsWith('/staff/me')) return auth === 'Bearer access-1' ? json(200, staffMe) : expired()
    return auth && auth !== 'Bearer access-1' ? json(200, { items: [] }) : expired()
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

async function signedIn() {
  const auth = useAuth()
  await auth.signIn('09120000002', '123456')
  const signedOut = vi.fn()
  auth.onSignedOut(signedOut)
  return { auth, signedOut }
}

describe('staff session', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })
  afterEach(() => vi.unstubAllGlobals())

  it('stays signed in when the connection drops during a renewal', async () => {
    backend(() => { throw new TypeError('Failed to fetch') })
    const { auth, signedOut } = await signedIn()
    await expect(api('/staff/patients')).rejects.toMatchObject({ code: 'network_error' })
    expect(signedOut).not.toHaveBeenCalled()
    expect(auth.isSignedIn).toBe(true)
    expect(localStorage.getItem(REFRESH_KEY)).toBe('refresh-1')
  })

  it('signs out when the server ends the session', async () => {
    backend(() => json(401, { error: { code: 'unauthenticated', message: 'Your session has ended.' } }))
    const { auth, signedOut } = await signedIn()
    await expect(api('/staff/patients')).rejects.toMatchObject({ status: 401 })
    expect(signedOut).toHaveBeenCalledTimes(1)
    expect(auth.isSignedIn).toBe(false)
    expect(localStorage.getItem(REFRESH_KEY)).toBeNull()
  })

  it('stays signed in when the server fails during a renewal', async () => {
    backend(() => json(503, { error: { code: 'service_unavailable', message: 'down' } }))
    const { auth, signedOut } = await signedIn()
    await expect(api('/staff/patients')).rejects.toMatchObject({ status: 503 })
    expect(signedOut).not.toHaveBeenCalled()
    expect(auth.isSignedIn).toBe(true)
  })

  it('renews with the newer token another tab has stored', async () => {
    const fetchMock = backend(() => json(200, tokens(3)))
    await signedIn()
    localStorage.setItem(REFRESH_KEY, 'refresh-2') // another tab renewed meanwhile
    await api('/staff/patients').catch(() => undefined)
    const renewal = fetchMock.mock.calls.find(([url]) => String(url).endsWith('/auth/token/refresh'))!
    expect(JSON.parse(renewal[1].body as string).refresh_token).toBe('refresh-2')
    expect(localStorage.getItem(REFRESH_KEY)).toBe('refresh-3')
  })

  it('signs out when another tab signs out', async () => {
    backend(() => json(200, tokens(2)))
    const { auth, signedOut } = await signedIn()
    localStorage.removeItem(REFRESH_KEY)
    dispatchEvent(new StorageEvent('storage', { key: REFRESH_KEY, oldValue: 'refresh-1', newValue: null }))
    expect(signedOut).toHaveBeenCalledTimes(1)
    expect(auth.isSignedIn).toBe(false)
  })

  it('keeps the stored token when the server is unreachable on page load', async () => {
    localStorage.setItem(REFRESH_KEY, 'refresh-1')
    setActivePinia(createPinia())
    backend(() => { throw new TypeError('Failed to fetch') })
    const auth = useAuth()
    await auth.restore()
    expect(auth.isSignedIn).toBe(false)
    expect(localStorage.getItem(REFRESH_KEY)).toBe('refresh-1')
  })
})
