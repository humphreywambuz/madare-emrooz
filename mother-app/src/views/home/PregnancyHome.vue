<script setup lang="ts">
import AppIcon from '@/components/AppIcon.vue'
import AsyncState from '@/components/AsyncState.vue'
import HomeHeader from '@/components/HomeHeader.vue'
import type { IconName } from '@/components/icons'
import LinkRow from '@/components/LinkRow.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import ProgressRing from '@/components/ProgressRing.vue'
import SurfaceCard from '@/components/SurfaceCard.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { useAuth } from '@/stores/auth'
import { useCountUp } from '@/utils/useCountUp'
import { useFormat } from '@/utils/useFormat'
import { usePregnancyHome } from '@/utils/usePregnancyHome'
import { TOTAL_WEEKS, usePregnancyProgress } from '@/utils/usePregnancyProgress'

const auth = useAuth()
const { num, date, fullName, timeAgo } = useFormat()
const {
  loading, error, run, pregnancy, midwife, daysLeft, vitals, busy, confirming, recentReport, report, askAgain,
} = usePregnancyHome()
const { trimester } = usePregnancyProgress(() => pregnancy.value?.gestational_week)
const shownWeek = useCountUp(() => pregnancy.value?.gestational_week ?? 0)

// Health cards: one per vital her midwife records.
const VITALS: { key: 'bp' | 'glucose' | 'weight'; icon: IconName }[] = [
  { key: 'bp', icon: 'heartPulse' }, { key: 'glucose', icon: 'droplet' }, { key: 'weight', icon: 'scale' },
]
const vitalText = (key: 'bp' | 'glucose' | 'weight') =>
  key === 'bp' ? (vitals.value.bp ? `${num(vitals.value.bp.systolic)}/${num(vitals.value.bp.diastolic)}` : '—') : num(vitals.value[key])
</script>

<template>
  <AsyncState :loading="loading" :error="error" @retry="run">
    <template v-if="!pregnancy">
      <HomeHeader :text="$t('home.noPregnancy')" />
      <div class="p-4">
        <RouterLink to="/pregnancy" class="btn btn-primary btn-lg btn-block">{{ $t('pregnancy.start') }}</RouterLink>
      </div>
    </template>

    <template v-else>
      <header class="animate-rise flex items-start justify-between gap-4 px-5 pt-6 motion-reduce:animate-none">
        <div class="min-w-0">
          <p class="text-sm text-base-content/60">{{ $t('home.hello', { name: auth.profile?.first_name }) }}</p>
          <h1 class="mt-1 font-display text-2xl leading-tight">
            {{ $t('home.weekLine', { week: num(pregnancy.gestational_week), trimester: $t(`home.trimester${trimester}`) }) }}
          </h1>
        </div>
        <RouterLink to="/me" :aria-label="$t('nav.me')">
          <UserAvatar :name="fullName(auth.profile?.first_name, auth.profile?.last_name)" />
        </RouterLink>
      </header>

      <div class="flex flex-col gap-4 p-4">
        <!-- Her progress, in the system's cover-card pattern: a mint card, the ring and the due date. -->
        <section class="animate-rise relative overflow-hidden rounded-3xl bg-primary/10 p-5 motion-reduce:animate-none" style="animation-delay: 0.1s">
          <div class="pointer-events-none absolute -end-10 -bottom-12 size-40 rounded-full bg-accent/50" aria-hidden="true" />
          <div class="relative flex items-center gap-5">
            <ProgressRing :fraction="pregnancy.gestational_week / TOTAL_WEEKS" :size="124" :thickness="12"
                          :label="$t('home.weekLine', { week: num(pregnancy.gestational_week), trimester: $t(`home.trimester${trimester}`) })">
              <span class="font-display text-4xl tabular-nums">{{ num(shownWeek) }}</span>
              <span class="mt-1 text-[11px] text-base-content/60">{{ $t('ui.ofWeeks') }}</span>
            </ProgressRing>
            <div class="min-w-0 flex-1">
              <span class="badge badge-accent badge-sm">{{ $t('home.daysLeft', { n: num(daysLeft) }) }}</span>
              <p class="mt-2 text-base font-bold">{{ $t(`home.trimester${trimester}`) }}</p>
              <p class="mt-1 text-sm leading-relaxed text-base-content/70">
                {{ $t('home.dueLine', { date: date(pregnancy.estimated_due_date), days: num(daysLeft) }) }}
              </p>
            </div>
          </div>
        </section>

        <!-- The one thing she reports herself. -->
        <SurfaceCard class="animate-rise motion-reduce:animate-none" style="animation-delay: 0.2s">
          <div class="card-body gap-3 p-5">
            <template v-if="!recentReport">
              <div class="flex items-start gap-3">
                <span class="grid size-11 shrink-0 place-items-center rounded-xl bg-error/10 text-error"><AppIcon name="droplet" class="size-5" /></span>
                <div>
                  <h2 class="font-bold">{{ $t('bleeding.question') }}</h2>
                  <p class="mt-1 text-sm leading-relaxed text-base-content/60">{{ $t('bleeding.help') }}</p>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <button class="btn btn-outline" :disabled="busy" @click="report(false)">{{ $t('bleeding.no') }}</button>
                <button class="btn btn-error" :disabled="busy" @click="confirming = true">{{ $t('bleeding.yes') }}</button>
              </div>
            </template>
            <template v-else-if="recentReport.has_spotting_or_bleeding">
              <div role="alert" class="alert alert-error alert-soft alert-vertical text-start">
                <div>
                  <h2 class="font-bold">{{ $t(midwife ? 'bleeding.sentMidwife' : 'bleeding.sentTeam') }}</h2>
                  <p class="mt-1 text-sm leading-relaxed">{{ $t('bleeding.emergency') }}</p>
                </div>
                <a class="btn btn-error btn-block" href="tel:115"><AppIcon name="phone" class="size-4" />{{ $t('bleeding.call115') }}</a>
              </div>
              <p class="text-xs text-base-content/60">{{ timeAgo(recentReport.recorded_at) }}</p>
            </template>
            <template v-else>
              <div class="flex items-center gap-3">
                <span class="grid size-11 shrink-0 place-items-center rounded-xl bg-success/10 text-success"><AppIcon name="checkCircle" class="size-5" /></span>
                <h2 class="font-bold">{{ $t('bleeding.noneRecorded') }}</h2>
              </div>
              <button class="btn btn-ghost btn-sm self-start" @click="askAgain">{{ $t('bleeding.change') }}</button>
            </template>
          </div>
        </SurfaceCard>

        <div v-if="!midwife" role="alert" class="alert alert-warning alert-soft text-sm">
          <span class="leading-relaxed">{{ $t('home.noMidwife') }}</span>
          <RouterLink to="/midwife" class="btn btn-sm btn-primary">{{ $t('home.chooseMidwife') }}</RouterLink>
        </div>

        <section class="animate-rise motion-reduce:animate-none" style="animation-delay: 0.3s">
          <h2 class="px-1 text-base font-bold">{{ $t('home.vitalsTitle') }}</h2>
          <p v-if="!vitals.bp && vitals.glucose === null && vitals.weight === null" class="mt-1 px-1 text-sm leading-relaxed text-base-content/60">
            {{ $t('home.vitalsEmpty') }}
          </p>
          <dl v-else class="mt-2 grid grid-cols-3 gap-3">
            <SurfaceCard v-for="v in VITALS" :key="v.key" as="div" class="p-3">
              <span class="grid size-9 place-items-center rounded-xl bg-primary/10 text-primary"><AppIcon :name="v.icon" class="size-4" /></span>
              <dd class="mt-3 font-display text-2xl leading-none tabular-nums"><bdi class="ltr">{{ vitalText(v.key) }}</bdi></dd>
              <dt class="mt-1 text-xs text-base-content/60">{{ $t(`home.${v.key}`) }}</dt>
            </SurfaceCard>
          </dl>
        </section>

        <section class="animate-rise motion-reduce:animate-none" style="animation-delay: 0.4s">
          <h2 class="px-1 pb-2 text-base font-bold">{{ $t('home.quickActions') }}</h2>
          <SurfaceCard as="ul" class="list">
            <LinkRow to="/midwife" icon="stethoscope" :title="$t('nav.midwife')"
                     :detail="midwife ? fullName(midwife.first_name, midwife.last_name) : $t('home.noMidwifeShort')" />
            <LinkRow to="/partner" icon="qr" :title="$t('pages.partner')" :detail="$t('home.partnerDetail')" />
            <LinkRow to="/history" icon="heart" :title="$t('pages.history')" :detail="$t('home.historyDetail')" />
            <LinkRow to="/pregnancy" icon="calendar" :title="$t('pages.pregnancy')" :detail="$t('home.pregnancyDetail')" />
          </SurfaceCard>
        </section>
      </div>

      <ModalDialog v-model:open="confirming" :title="$t('bleeding.confirmTitle')">
        <p class="leading-relaxed text-base-content/70">{{ $t(midwife ? 'bleeding.confirmMidwife' : 'bleeding.confirmTeam') }}</p>
        <div class="modal-action">
          <button class="btn" @click="confirming = false">{{ $t('app.cancel') }}</button>
          <button class="btn btn-error" :disabled="busy" @click="report(true)">
            <span v-if="busy" class="loading loading-spinner loading-sm" />{{ $t('bleeding.send') }}
          </button>
        </div>
      </ModalDialog>
    </template>
  </AsyncState>
</template>
