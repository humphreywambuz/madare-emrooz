// Who is signed in. The access token lives in memory only; the refresh token is kept in
// localStorage so a page reload can renew the session.
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { ApiError, useSession } from '@/api/client'
import { auth as authApi } from '@/api/endpoints'
import type { Role, StaffMember, Tokens } from '@/api/types'
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

  async function renew(): Promise<boolean> {
    if (!refreshToken.value) return false
    try {
      keep(await authApi.refresh(refreshToken.value))
      return true
    } catch {
      clear()
      return false
    }
  }

  useSession({
    accessToken: () => accessToken.value,
    renew,
    onSignedOut: () => {
      clear()
      signedOutHandlers.forEach((handler) => handler())
    },
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
    if (!refreshToken.value || !(await renew())) return
    try {
      me.value = await authApi.staffMe()
    } catch {
      clear()
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
