<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { auth as authApi } from '@/api/endpoints'
import { setLocale } from '@/i18n'
import { homeFor } from '@/router'
import { useAuth } from '@/stores/auth'
import { asciiDigits } from '@/utils/format'
import { useFormat } from '@/utils/useFormat'

const auth = useAuth()
const router = useRouter()
const route = useRoute()
const { errorText, num, locale } = useFormat()

const step = ref<'mobile' | 'code'>('mobile')
const mobile = ref('')
const code = ref('')
const busy = ref(false)
const error = ref<unknown>(null)
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
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-base-200 p-4">
    <div class="card w-full max-w-sm bg-base-100 shadow-sm">
      <div class="card-body gap-4">
        <div class="flex items-start justify-between gap-2">
          <div>
            <div class="text-xl font-bold text-primary">{{ $t('app.name') }}</div>
            <h1 class="text-base-content/70">{{ $t('login.title') }}</h1>
          </div>
          <button class="btn btn-ghost btn-xs" @click="setLocale(locale === 'fa' ? 'en' : 'fa')">
            {{ $t('app.language') }}
          </button>
        </div>

        <div v-if="error" role="alert" class="alert alert-error alert-soft text-sm">{{ errorText(error) }}</div>

        <form v-if="step === 'mobile'" class="flex flex-col gap-3" @submit.prevent="sendCode">
          <label class="fieldset">
            <span class="fieldset-legend">{{ $t('login.mobile') }}</span>
            <input v-model="mobile" class="input ltr w-full" inputmode="tel" autocomplete="tel" required
                   :placeholder="$t('login.mobileHint')" autofocus />
          </label>
          <button class="btn btn-primary" :disabled="busy">
            <span v-if="busy" class="loading loading-spinner loading-sm" />{{ $t('login.sendCode') }}
          </button>
        </form>

        <form v-else class="flex flex-col gap-3" @submit.prevent="signIn">
          <label class="fieldset">
            <span class="fieldset-legend">{{ $t('login.code') }}</span>
            <input v-model="code" class="input ltr w-full text-center text-lg tracking-[0.5em]" inputmode="numeric"
                   autocomplete="one-time-code" maxlength="6" required autofocus />
            <span class="label">{{ $t('login.codeHint') }}</span>
          </label>
          <button class="btn btn-primary" :disabled="busy">
            <span v-if="busy" class="loading loading-spinner loading-sm" />{{ $t('login.signIn') }}
          </button>
          <div class="flex justify-between text-sm">
            <button type="button" class="link" @click="step = 'mobile'">{{ $t('login.changeNumber') }}</button>
            <button type="button" class="link" :disabled="!canResend || busy" :class="{ 'opacity-50': !canResend }"
                    @click="sendCode">
              {{ canResend ? $t('login.resend') : $t('login.resendIn', { s: num(wait) }) }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
