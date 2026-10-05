<script setup lang="ts">
// The pregnancy in the design system's "pregnancy progress" pattern: a thick ring with the week in
// the centre and the three trimesters as labelled segments beside it.
import { computed } from 'vue'

import ProgressRing from '@/components/ProgressRing.vue'
import { useFormat } from '@/utils/useFormat'
import { TOTAL_WEEKS, TRIMESTER_STARTS, usePregnancyProgress } from '@/utils/usePregnancyProgress'

const props = defineProps<{ week: number; dueDate: string | null }>()
const { num, date } = useFormat()
const { week: current, trimester, weeksLeft } = usePregnancyProgress(() => props.week)

const segments = computed(() => {
  const bounds = [...TRIMESTER_STARTS, TOTAL_WEEKS]
  const week = current.value ?? 0
  return ([1, 2, 3] as const).map((n) => {
    const from = bounds[n - 1]
    const to = bounds[n]
    const fill = Math.min(1, Math.max(0, (week - from) / (to - from)))
    const status = fill >= 1 ? 'done' : fill > 0 ? 'now' : 'ahead'
    return { n, from, to, fill, status, remaining: to - Math.max(week, from) }
  })
})
</script>

<template>
  <figure class="flex flex-col items-center gap-6 sm:flex-row sm:items-center" role="img"
          :aria-label="`${$t('patient.week', { n: num(week) })}, ${$t(`ui.trimester${trimester}`)}`">
    <ProgressRing :fraction="week / TOTAL_WEEKS" :size="148" :thickness="14">
      <span class="font-display text-4xl tabular-nums">{{ num(week) }}</span>
      <span class="mt-1 text-xs text-base-content/60">{{ $t('ui.ofWeeks') }}</span>
    </ProgressRing>

    <div class="flex w-full min-w-0 flex-1 flex-col gap-4">
      <div class="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <span class="text-base font-bold">{{ $t(`ui.trimester${trimester}`) }}</span>
        <span class="text-sm text-base-content/60">
          {{ $t('patient.due', { date: date(dueDate) }) }} ·
          {{ weeksLeft ? $t('ui.weeksLeft', { n: num(weeksLeft) }) : $t('ui.dueToday') }}
        </span>
      </div>
      <div class="grid grid-cols-3 gap-2">
        <div v-for="s in segments" :key="s.n" class="flex flex-col gap-2">
          <div class="h-2 overflow-hidden rounded-full bg-primary/15">
            <div class="h-full origin-left rounded-full bg-primary animate-grow motion-reduce:animate-none rtl:origin-right"
                 :style="{ width: `${s.fill * 100}%`, animationDelay: `${(s.n - 1) * 120}ms` }" />
          </div>
          <div class="text-xs leading-tight">
            <div class="font-semibold" :class="s.status === 'ahead' ? 'text-base-content/50' : ''">{{ $t(`ui.trimester${s.n}`) }}</div>
            <div class="text-base-content/60">
              <template v-if="s.status === 'done'">{{ $t('ui.segmentDone') }}</template>
              <template v-else-if="s.status === 'now'">{{ $t('patient.week', { n: num(week) }) }}</template>
              <template v-else>{{ $t('ui.segmentWeeks', { n: num(s.to - s.from) }) }}</template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </figure>
</template>
