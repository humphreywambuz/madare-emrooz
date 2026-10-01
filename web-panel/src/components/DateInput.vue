<script setup lang="ts">
// A date field: day / month / year in the Jalali calendar in Persian, the browser's date
// picker in English. The value is always an ISO Gregorian date ("2026-10-01") or "".
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { formatNumber } from '@/utils/format'
import { jalaliMonthLength, parseIsoDate, toGregorian, toIsoDate, toJalali } from '@/utils/jalali'

const model = defineModel<string>({ required: true })
const props = withDefaults(defineProps<{ id?: string; yearsBack?: number; yearsAhead?: number; required?: boolean }>(), {
  yearsBack: 2,
  yearsAhead: 1,
})

const { locale } = useI18n()
const MONTHS = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']

const now = new Date()
const todayJalali = toJalali({ year: now.getFullYear(), month: now.getMonth() + 1, day: now.getDate() })
const parts = computed(() => (model.value ? toJalali(parseIsoDate(model.value)) : null))
const years = computed(() => {
  const list: number[] = []
  for (let y = todayJalali.year + props.yearsAhead; y >= todayJalali.year - props.yearsBack; y--) list.push(y)
  return list
})
const days = computed(() =>
  Array.from({ length: parts.value ? jalaliMonthLength(parts.value.year, parts.value.month) : 31 }, (_, i) => i + 1),
)

function update(part: 'year' | 'month' | 'day', value: string) {
  const current = parts.value ?? { ...todayJalali }
  const next = { ...current, [part]: Number(value) }
  next.day = Math.min(next.day, jalaliMonthLength(next.year, next.month))
  model.value = toIsoDate(toGregorian(next))
}

const fa = (n: number) => formatNumber(n, 'fa').replace(/٬/g, '')
</script>

<template>
  <div v-if="locale === 'fa'" class="join w-full">
    <select :id="id" class="select join-item" :value="parts?.day ?? ''" :required="required" aria-label="روز"
            @change="update('day', ($event.target as HTMLSelectElement).value)">
      <option value="" disabled>روز</option>
      <option v-for="d in days" :key="d" :value="d">{{ fa(d) }}</option>
    </select>
    <select class="select join-item" :value="parts?.month ?? ''" aria-label="ماه"
            @change="update('month', ($event.target as HTMLSelectElement).value)">
      <option value="" disabled>ماه</option>
      <option v-for="(name, i) in MONTHS" :key="i" :value="i + 1">{{ name }}</option>
    </select>
    <select class="select join-item" :value="parts?.year ?? ''" aria-label="سال"
            @change="update('year', ($event.target as HTMLSelectElement).value)">
      <option value="" disabled>سال</option>
      <option v-for="y in years" :key="y" :value="y">{{ fa(y) }}</option>
    </select>
  </div>
  <input v-else :id="id" v-model="model" type="date" class="input w-full" :required="required" />
</template>
