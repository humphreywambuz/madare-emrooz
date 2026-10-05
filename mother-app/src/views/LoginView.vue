<script setup lang="ts">
import { useTemplateRef } from 'vue'

import AppIcon from '@/components/AppIcon.vue'
import BrandMark from '@/components/BrandMark.vue'
import ProgressRing from '@/components/ProgressRing.vue'
import { useFormat } from '@/utils/useFormat'
import { CODE_LENGTH, useOtpLogin } from '@/utils/useOtpLogin'
import { TOTAL_WEEKS } from '@/utils/usePregnancyProgress'

const { errorText, num, mobile: formatMobile } = useFormat()
const codeInput = useTemplateRef<HTMLInputElement>('codeInput')
const { step, mobile, code, busy, error, wait, canResend, sendCode, signIn, changeNumber } = useOtpLogin(codeInput)

// The week on the welcome card, the same one the design system uses in its own mock-ups.
const DEMO_WEEK = 24
</script>

<template>
  <div class="mx-auto flex min-h-screen w-full max-w-md flex-col gap-5 p-4 pt-6 lg:max-w-5xl lg:grid lg:grid-cols-2 lg:items-center lg:gap-8 lg:p-8">
    <!-- The welcome panel: the brand, the promise and a glimpse of the progress card. -->
    <aside class="relative overflow-hidden rounded-3xl border border-base-300 bg-linear-to-br from-primary/15 via-base-100 to-accent/40 p-6 lg:p-10">
      <div class="pointer-events-none absolute -end-16 -top-16 size-56 rounded-full bg-primary/10" aria-hidden="true" />
      <div class="pointer-events-none absolute -bottom-24 -start-10 size-64 rounded-full bg-accent/30" aria-hidden="true" />

      <div class="relative flex items-center gap-3">
        <BrandMark />
        <span class="text-lg font-bold">{{ $t('app.name') }}</span>
      </div>

      <div class="relative mt-6 flex items-center gap-5 lg:mt-10 lg:flex-col lg:items-start lg:gap-8">
        <div class="min-w-0 flex-1">
          <h2 class="font-display text-2xl leading-tight text-balance lg:text-4xl">{{ $t('login.heroTitle') }}</h2>
          <p class="mt-2 hidden leading-relaxed text-base-content/70 lg:block">{{ $t('login.heroText') }}</p>
        </div>
        <div class="card card-border animate-rise shrink-0 border-base-300 bg-base-100 shadow-level-2 motion-reduce:animate-none lg:self-center">
          <div class="card-body items-center gap-2 p-4 text-center lg:p-6">
            <span class="badge badge-accent badge-sm">{{ $t('home.weekLine', { week: num(DEMO_WEEK), trimester: $t('home.trimester2') }) }}</span>
            <ProgressRing :fraction="DEMO_WEEK / TOTAL_WEEKS" :size="104" :thickness="11">
              <span class="font-display text-3xl tabular-nums">{{ num(DEMO_WEEK) }}</span>
              <span class="mt-1 text-[11px] text-base-content/60">{{ $t('ui.ofWeeks') }}</span>
            </ProgressRing>
          </div>
        </div>
      </div>
    </aside>

    <main class="card card-border rounded-3xl border-base-300 bg-base-100 shadow-level-2">
      <div class="card-body gap-5 p-6 sm:p-8">
        <div>
          <h1 class="font-display text-2xl text-balance">{{ $t('login.title') }}</h1>
          <p class="mt-1 text-sm leading-relaxed text-base-content/60">{{ $t('login.subtitle') }}</p>
        </div>

        <div v-if="error" role="alert" class="alert alert-error alert-soft text-sm">{{ errorText(error) }}</div>

        <form v-if="step === 'mobile'" class="flex flex-col gap-4" @submit.prevent="sendCode">
          <fieldset class="fieldset">
            <legend class="fieldset-legend">{{ $t('login.mobile') }}</legend>
            <label class="input input-lg w-full">
              <AppIcon name="phone" class="size-5 opacity-50" />
              <input v-model="mobile" class="ltr grow" inputmode="tel" autocomplete="tel" required
                     :placeholder="$t('login.mobileHint')" />
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
            <p class="label whitespace-normal">{{ $t('login.codeSentTo', { mobile: formatMobile(mobile) }) }}</p>
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
    </main>
  </div>
</template>
