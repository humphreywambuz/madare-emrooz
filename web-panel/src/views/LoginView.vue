<script setup lang="ts">
import { useTemplateRef } from 'vue'

import AppIcon from '@/components/AppIcon.vue'
import BrandMark from '@/components/BrandMark.vue'
import ProgressRing from '@/components/ProgressRing.vue'
import { setLocale } from '@/i18n'
import { useFormat } from '@/utils/useFormat'
import { CODE_LENGTH, useOtpLogin } from '@/utils/useOtpLogin'
import { TOTAL_WEEKS } from '@/utils/usePregnancyProgress'

const { errorText, num, locale, mobile: formatMobile } = useFormat()
const codeInput = useTemplateRef<HTMLInputElement>('codeInput')
const { step, mobile, code, busy, error, wait, canResend, sendCode, signIn, changeNumber } = useOtpLogin(codeInput)

// The week shown on the welcome panel, the same one the design system uses in its own mock-ups.
const DEMO_WEEK = 24
</script>

<template>
  <div class="min-h-screen bg-base-200 p-4 sm:p-6 lg:p-8">
    <div class="mx-auto grid min-h-[calc(100vh-4rem)] max-w-6xl gap-6 lg:grid-cols-2">
      <!-- The welcome panel: the brand gradient, the promise and a glimpse of a mother's progress card. -->
      <aside class="relative hidden overflow-hidden rounded-3xl border border-base-300 bg-linear-to-br from-primary/15 via-base-100 to-accent/40 p-10 lg:flex lg:flex-col lg:justify-between">
        <div class="pointer-events-none absolute -end-24 -top-24 size-80 rounded-full bg-primary/10" aria-hidden="true" />
        <div class="pointer-events-none absolute -bottom-32 -start-16 size-96 rounded-full bg-accent/30" aria-hidden="true" />

        <div class="relative flex items-center gap-3">
          <BrandMark />
          <div>
            <div class="text-lg font-bold leading-tight">{{ $t('app.name') }}</div>
            <div class="text-xs text-base-content/60">{{ $t('app.panel') }}</div>
          </div>
        </div>

        <div class="relative grid gap-10 xl:grid-cols-5 xl:items-center">
          <div class="xl:col-span-3">
            <h2 class="font-display text-4xl leading-tight text-balance xl:text-5xl">{{ $t('ui.heroTitle') }}</h2>
            <p class="mt-5 max-w-md text-lg leading-relaxed text-base-content/70">{{ $t('ui.heroText') }}</p>
          </div>
          <div class="card card-border animate-rise border-base-300 bg-base-100 shadow-level-2 motion-reduce:animate-none xl:col-span-2">
            <div class="card-body items-center gap-3 p-6 text-center">
              <span class="badge badge-accent badge-sm">{{ $t('patient.week', { n: num(DEMO_WEEK) }) }}</span>
              <ProgressRing :fraction="DEMO_WEEK / TOTAL_WEEKS" :size="132" :thickness="12">
                <span class="font-display text-4xl tabular-nums">{{ num(DEMO_WEEK) }}</span>
                <span class="mt-1 text-xs text-base-content/60">{{ $t('ui.ofWeeks') }}</span>
              </ProgressRing>
              <div class="text-sm font-bold">{{ $t('ui.trimester2') }}</div>
              <div class="text-xs text-base-content/60">{{ $t('ui.weeksLeft', { n: num(TOTAL_WEEKS - DEMO_WEEK) }) }}</div>
            </div>
          </div>
        </div>

        <p class="relative flex items-center gap-2 text-sm text-base-content/60">
          <AppIcon name="shieldCheck" class="size-4 text-primary" />{{ $t('ui.heroSecure') }}
        </p>
      </aside>

      <main class="flex items-center justify-center">
        <div class="card card-border w-full max-w-md rounded-3xl border-base-300 bg-base-100 shadow-level-2">
          <div class="card-body gap-6 p-6 sm:p-8">
            <div class="flex items-center justify-between gap-4">
              <div class="flex items-center gap-3 lg:invisible">
                <BrandMark />
                <span class="font-bold">{{ $t('app.name') }}</span>
              </div>
              <button class="btn btn-ghost btn-sm border border-base-300 px-3" @click="setLocale(locale === 'fa' ? 'en' : 'fa')">
                <AppIcon name="globe" class="size-4" />{{ $t('app.language') }}
              </button>
            </div>

            <div>
              <h1 class="font-display text-2xl text-balance sm:text-3xl">{{ $t('login.title') }}</h1>
              <p class="mt-2 text-sm leading-relaxed text-base-content/60">{{ $t('login.notStaff') }}</p>
            </div>

            <div v-if="error" role="alert" class="alert alert-error alert-soft text-sm">{{ errorText(error) }}</div>

            <form v-if="step === 'mobile'" class="flex flex-col gap-4" @submit.prevent="sendCode">
              <fieldset class="fieldset">
                <legend class="fieldset-legend">{{ $t('login.mobile') }}</legend>
                <label class="input input-lg w-full">
                  <AppIcon name="phone" class="size-5 opacity-50" />
                  <input v-model="mobile" class="ltr grow" inputmode="tel" autocomplete="tel" required
                         :placeholder="$t('login.mobileHint')" autofocus />
                </label>
              </fieldset>
              <button class="btn btn-primary btn-lg btn-block" :disabled="busy">
                <span v-if="busy" class="loading loading-spinner loading-sm" />{{ $t('login.sendCode') }}
                <AppIcon name="chevron" class="size-4 rtl:rotate-180" />
              </button>
            </form>

            <form v-else class="flex flex-col gap-4" @submit.prevent="signIn">
              <fieldset class="fieldset">
                <legend class="fieldset-legend">{{ $t('login.code') }}</legend>
                <label class="otp otp-lg" dir="ltr">
                  <span v-for="n in CODE_LENGTH" :key="n" />
                  <input ref="codeInput" v-model="code" type="text" autocomplete="one-time-code" inputmode="numeric"
                         :maxlength="CODE_LENGTH" :pattern="`[0-9۰-۹]{${CODE_LENGTH}}`" required />
                </label>
                <p class="label">{{ $t('ui.codeSentTo', { mobile: formatMobile(mobile) }) }} {{ $t('login.codeHint') }}</p>
              </fieldset>
              <button class="btn btn-primary btn-lg btn-block" :disabled="busy || code.length < CODE_LENGTH">
                <span v-if="busy" class="loading loading-spinner loading-sm" />{{ $t('login.signIn') }}
              </button>
              <div class="flex justify-between">
                <button type="button" class="btn btn-ghost btn-sm" @click="changeNumber">{{ $t('login.changeNumber') }}</button>
                <button type="button" class="btn btn-ghost btn-sm" :disabled="!canResend || busy" @click="sendCode">
                  {{ canResend ? $t('login.resend') : $t('login.resendIn', { s: num(wait) }) }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>
