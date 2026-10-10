// Who is signed in, and her profile. The access token lives in memory only; the refresh token
// is kept in localStorage so a page reload can renew the session.
import { defineStore } from 'pinia'
import { computed, ref, shallowRef } from 'vue'

import { ApiError, useSession } from '@/api/client'
import { auth as authApi, profile as profileApi } from '@/api/endpoints'
import type { Profile, Tokens } from '@/api/types'
import { exclusive } from '@/utils/exclusive'
import { load, store } from '@/utils/storage'

const REFRESH_KEY = 'madare.mother.refresh'

export const useAuth = defineStore('auth', () => {
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(load(REFRESH_KEY))
  const mobile = ref<string | null>(null)
  const profile = shallowRef<Profile | null>(null)
  const signedOutHandlers: (() => void)[] = []

  const isSignedIn = computed(() => mobile.value !== null)
  const hasProfile = computed(() => profile.value !== null)

  function keep(tokens: Tokens) {
    accessToken.value = tokens.access_token
    refreshToken.value = tokens.refresh_token
    store(REFRESH_KEY, tokens.refresh_token)
  }

  function clear() {
    accessToken.value = null
    refreshToken.value = null
    mobile.value = null
    profile.value = null
    store(REFRESH_KEY, null)
  }

  /**
   * Renew the access token. False only when the server has ended the session; a network or
   * server error throws instead and keeps the session, so a dropped connection doesn't sign out.
   * One tab renews at a time: the refresh token is shared, and each one works once.
   */
  async function renew(): Promise<boolean> {
    return exclusive(REFRESH_KEY, async () => {
      // Another tab may have renewed meanwhile: its newer token is in storage.
      const token = load(REFRESH_KEY) ?? refreshToken.value
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

  async function loadAccount() {
    const me = await authApi.me()
    profile.value = await profileApi.get()
    mobile.value = me.mobile
  }

  async function signIn(mobileNumber: string, code: string) {
    const tokens = await authApi.verify(mobileNumber, code)
    if (tokens.user.role !== 'user') {
      // Staff use the care team panel; end the session this sign-in just opened.
      await authApi.logout(tokens.refresh_token).catch(() => undefined)
      throw new ApiError(403, 'staff_account', 'staff_account')
    }
    keep(tokens)
    await loadAccount()
  }

  /** On page load: use the stored refresh token, if any. */
  async function restore(): Promise<void> {
    try {
      if (!refreshToken.value || !(await renew())) return
      await loadAccount()
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

  function setProfile(value: Profile) {
    profile.value = value
  }

  function onSignedOut(handler: () => void) {
    signedOutHandlers.push(handler)
  }

  return { mobile, profile, isSignedIn, hasProfile, signIn, restore, signOut, setProfile, onSignedOut }
})
