// Who is signed in. The access token lives in memory only; the refresh token is kept in
// localStorage so a page reload can renew the session.
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { ApiError, useSession } from '@/api/client'
import { auth as authApi } from '@/api/endpoints'
import type { Role, StaffMember, Tokens } from '@/api/types'
import { exclusive } from '@/utils/exclusive'
import { load, store } from '@/utils/storage'

const REFRESH_KEY = 'madare.refresh'

const storedRefresh = () => load(REFRESH_KEY)
const storeRefresh = (token: string | null) => store(REFRESH_KEY, token)

export const useAuth = defineStore('auth', () => {
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(storedRefresh())
  const me = ref<StaffMember | null>(null)
  const signedOutHandlers: (() => void)[] = []

  const role = computed<Role | null>(() => me.value?.role ?? null)
  const isSignedIn = computed(() => me.value !== null)
  const displayName = computed(() =>
    [me.value?.first_name, me.value?.last_name].filter(Boolean).join(' ') || me.value?.mobile || '',
  )

  function keep(tokens: Tokens) {
    accessToken.value = tokens.access_token
    refreshToken.value = tokens.refresh_token
    storeRefresh(tokens.refresh_token)
  }

  function clear() {
    accessToken.value = null
    refreshToken.value = null
    me.value = null
    storeRefresh(null)
  }

  /**
   * Renew the access token. False only when the server has ended the session; a network or
   * server error throws instead and keeps the session, so a dropped connection doesn't sign out.
   * One tab renews at a time: the refresh token is shared, and each one works once.
   */
  async function renew(): Promise<boolean> {
    return exclusive(REFRESH_KEY, async () => {
      // Another tab may have renewed meanwhile: its newer token is in storage.
      const token = storedRefresh() ?? refreshToken.value
      if (!token) return false
      try {
        keep(await authApi.refresh(token))
        return true
      } catch (error) {
        if (!(error instanceof ApiError) || error.status !== 401) throw error
        clear()
        return false
      }
    })
  }

  function endSession() {
    clear()
    signedOutHandlers.forEach((handler) => handler())
  }

  useSession({ accessToken: () => accessToken.value, renew, onSignedOut: endSession })

  // Follow the other tabs: a renewal there replaces the token here; a sign-out there ends this tab too.
  addEventListener('storage', (event) => {
    if (event.key !== REFRESH_KEY) return
    if (event.newValue) refreshToken.value = event.newValue
    else if (isSignedIn.value) endSession()
  })

  async function signIn(mobile: string, code: string) {
    const tokens = await authApi.verify(mobile, code)
    if (tokens.user.role === 'user') {
      // Mothers use the mobile app; end the session this sign-in just opened.
      await authApi.logout(tokens.refresh_token).catch(() => undefined)
      throw new ApiError(403, 'not_staff', 'not_staff')
    }
    keep(tokens)
    me.value = await authApi.staffMe()
  }

  /** On page load: use the stored refresh token, if any. */
  async function restore(): Promise<void> {
    try {
      if (!refreshToken.value || !(await renew())) return
      me.value = await authApi.staffMe()
    } catch (error) {
      // Offline or the server is down: show the sign-in page, but keep the token for next time.
      if (error instanceof ApiError && (error.status === 401 || error.status === 403)) clear()
    }
  }

  async function signOut() {
    const token = refreshToken.value
    clear()
    if (token) await authApi.logout(token).catch(() => undefined)
  }

  function onSignedOut(handler: () => void) {
    signedOutHandlers.push(handler)
  }

  return { me, role, isSignedIn, displayName, signIn, restore, signOut, onSignedOut }
})
