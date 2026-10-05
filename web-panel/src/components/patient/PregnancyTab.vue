<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { patients } from '@/api/endpoints'
import type { PatientRecord } from '@/api/types'
import AppIcon from '@/components/AppIcon.vue'
import DateInput from '@/components/DateInput.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import SectionCard from '@/components/SectionCard.vue'
import { useAction } from '@/utils/useAction'
import { useFormat } from '@/utils/useFormat'

import FieldList from './FieldList.vue'

const props = defineProps<{ record: PatientRecord }>()
const emit = defineEmits<{ changed: [] }>()
const { t } = useI18n()
const { num, date, dateTime, enumLabel, errorText } = useFormat()
const { busy, error, act } = useAction()

const p = computed(() => props.record.pregnancy)
const rows = computed(() => {
  if (!p.value) return []
  return [
    { label: t('pregnancy.gestational_week'), value: num(p.value.gestational_week) },
    { label: t('pregnancy.lmp_date'), value: date(p.value.lmp_date) },
    { label: t('pregnancy.avg_cycle_length_days'), value: num(p.value.avg_cycle_length_days) },
    { label: t('pregnancy.conception_type'), value: enumLabel('conception_type', p.value.conception_type) },
    { label: t('pregnancy.care_provider_type'), value: enumLabel('care_provider_type', p.value.care_provider_type) },
    { label: t('pregnancy.care_provider_name'), value: p.value.care_provider_name || '—' },
  ]
})

const open = ref(false)
const dueDate = ref('')
const reason = ref('')

function start() {
  dueDate.value = p.value?.estimated_due_date ?? ''
  reason.value = ''
  error.value = null
  open.value = true
}

async function save() {
  const ok = await act(() => patients.correctDueDate(props.record.patient.id, dueDate.value, reason.value || null),
    'pregnancy.corrected', true)
  if (ok) {
    open.value = false
    emit('changed')
  }
}
</script>

<template>
  <SectionCard v-if="!p"><p class="text-sm text-base-content/60">{{ $t('pregnancy.none') }}</p></SectionCard>
  <div v-else class="flex flex-col gap-6">
    <SectionCard>
      <div class="flex flex-wrap items-center gap-4">
        <span class="grid size-12 place-items-center rounded-xl bg-accent/40 text-accent-content">
          <AppIcon name="calendar" class="size-6" />
        </span>
        <div class="min-w-0 flex-1">
          <h2 class="text-xs font-semibold text-base-content/60">{{ $t('pregnancy.estimated_due_date') }}</h2>
          <div class="font-display text-2xl">{{ date(p.estimated_due_date) }}</div>
          <p class="text-xs text-base-content/60">
            {{ $t(`pregnancy.source.${p.due_date_source}`) }}
            <template v-if="p.due_date_corrected_at">، {{ dateTime(p.due_date_corrected_at) }}</template>
          </p>
        </div>
        <button class="btn btn-outline btn-sm" @click="start"><AppIcon name="pencil" class="size-4" />{{ $t('pregnancy.correct') }}</button>
      </div>
    </SectionCard>
    <SectionCard :title="$t('patient.tabs.pregnancy')">
      <FieldList :rows="rows" />
    </SectionCard>

    <ModalDialog v-model:open="open" :title="$t('pregnancy.correctTitle')">
      <form class="flex flex-col gap-2" @submit.prevent="save">
        <p class="text-sm leading-relaxed text-base-content/60">{{ $t('pregnancy.correctHelp') }}</p>
        <div v-if="error" role="alert" class="alert alert-error alert-soft text-sm">{{ errorText(error) }}</div>
        <fieldset class="fieldset">
          <legend class="fieldset-legend">{{ $t('pregnancy.estimated_due_date') }}</legend>
          <DateInput v-model="dueDate" :years-back="0" :years-ahead="1" required />
        </fieldset>
        <fieldset class="fieldset">
          <legend class="fieldset-legend">{{ $t('pregnancy.reason') }}</legend>
          <input v-model="reason" class="input w-full" maxlength="500" :placeholder="$t('pregnancy.reasonPlaceholder')" />
        </fieldset>
        <div class="modal-action">
          <button type="button" class="btn" @click="open = false">{{ $t('app.cancel') }}</button>
          <button class="btn btn-primary" :disabled="busy || !dueDate">{{ $t('app.save') }}</button>
        </div>
      </form>
    </ModalDialog>
  </div>
</template>
