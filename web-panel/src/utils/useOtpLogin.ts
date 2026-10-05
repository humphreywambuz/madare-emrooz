// The two-step sign-in: request an SMS code for a mobile number, then verify it.
import { computed, nextTick, onUnmounted, ref, shallowRef, type ShallowRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { auth as authApi } from '@/api/endpoints'
import { homeFor } from '@/router'
import { useAuth } from '@/stores/auth'

import { asciiDigits } from './format'

export const CODE_LENGTH = 6

export function useOtpLogin(codeInput: Readonly<ShallowRef<HTMLInputElement | null>>) {
  const auth = useAuth()
  const router = useRouter()
  const route = useRoute()

  const step = ref<'mobile' | 'code'>('mobile')
  const mobile = ref('')
  const code = ref('')
  const busy = ref(false)
  const error = shallowRef<unknown>(null)
  const wait = ref(0)
  let timer: ReturnType<typeof setInterval> | undefined

  const canResend = computed(() => wait.value === 0)

  function countdown(seconds: number) {
    wait.value = seconds
    clearInterval(timer)
    timer = setInterval(() => {
      wait.value = Math.max(0, wait.value - 1)
      if (!wait.value) clearInterval(timer)
    }, 1000)
  }
  onUnmounted(() => clearInterval(timer))

  async function sendCode() {
    busy.value = true
    error.value = null
    try {
      const sent = await authApi.requestCode(asciiDigits(mobile.value))
      step.value = 'code'
      code.value = ''
      countdown(sent.resend_after)
      await nextTick()
      codeInput.value?.focus()
    } catch (e) {
      error.value = e
    } finally {
      busy.value = false
    }
  }

  async function signIn() {
    busy.value = true
    error.value = null
    try {
      await auth.signIn(asciiDigits(mobile.value), asciiDigits(code.value))
      const next = typeof route.query.next === 'string' ? route.query.next : null
      router.replace(next ?? homeFor(auth.role))
    } catch (e) {
      error.value = e
    } finally {
      busy.value = false
    }
  }

  function changeNumber() {
    step.value = 'mobile'
    error.value = null
  }

  return { step, mobile, code, busy, error, wait, canResend, sendCode, signIn, changeNumber }
}
