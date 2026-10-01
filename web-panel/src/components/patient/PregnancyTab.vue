<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { patients } from '@/api/endpoints'
import type { PatientRecord } from '@/api/types'
import DateInput from '@/components/DateInput.vue'
import ModalDialog from '@/components/ModalDialog.vue'
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
  <p v-if="!p" class="text-base-content/60">{{ $t('pregnancy.none') }}</p>
  <div v-else class="flex flex-col gap-5">
    <div class="flex flex-wrap items-end justify-between gap-3 rounded-box bg-base-200 p-4">
      <div>
        <div class="text-sm text-base-content/60">{{ $t('pregnancy.estimated_due_date') }}</div>
        <div class="text-xl font-bold">{{ date(p.estimated_due_date) }}</div>
        <div class="text-sm text-base-content/70">
          {{ $t(`pregnancy.source.${p.due_date_source}`) }}
          <span v-if="p.due_date_corrected_at"> · {{ dateTime(p.due_date_corrected_at) }}</span>
        </div>
      </div>
      <button class="btn btn-sm" @click="start">{{ $t('pregnancy.correct') }}</button>
    </div>
    <FieldList :rows="rows" />

    <ModalDialog v-model:open="open" :title="$t('pregnancy.correctTitle')">
      <form class="flex flex-col gap-3" @submit.prevent="save">
        <p class="text-sm text-base-content/70">{{ $t('pregnancy.correctHelp') }}</p>
        <div v-if="error" role="alert" class="alert alert-error alert-soft text-sm">{{ errorText(error) }}</div>
        <label class="fieldset">
          <span class="fieldset-legend">{{ $t('pregnancy.estimated_due_date') }}</span>
          <DateInput v-model="dueDate" :years-back="0" :years-ahead="1" required />
        </label>
        <label class="fieldset">
          <span class="fieldset-legend">{{ $t('pregnancy.reason') }}</span>
          <input v-model="reason" class="input w-full" maxlength="500" :placeholder="$t('pregnancy.reasonPlaceholder')" />
        </label>
        <div class="modal-action">
          <button type="button" class="btn" @click="open = false">{{ $t('app.cancel') }}</button>
          <button class="btn btn-primary" :disabled="busy || !dueDate">{{ $t('app.save') }}</button>
        </div>
      </form>
    </ModalDialog>
  </div>
</template>
