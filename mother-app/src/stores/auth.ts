// Who is signed in, and her profile. The access token lives in memory only; the refresh token
// is kept in localStorage so a page reload can renew the session.
import { defineStore } from 'pinia'
import { computed, ref, shallowRef } from 'vue'

import { ApiError, useSession } from '@/api/client'
import { auth as authApi, profile as profileApi } from '@/api/endpoints'
import type { Profile, Tokens } from '@/api/types'
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
    if (!refreshToken.value || !(await renew())) return
    try {
      await loadAccount()
    } catch {
      clear()
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
