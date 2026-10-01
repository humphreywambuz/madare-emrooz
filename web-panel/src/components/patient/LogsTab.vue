<script setup lang="ts">
import { reactive, ref } from 'vue'

import { ApiError } from '@/api/client'
import { patients } from '@/api/endpoints'
import type { DailyLog, PatientRecord } from '@/api/types'
import ModalDialog from '@/components/ModalDialog.vue'
import { useAuth } from '@/stores/auth'
import { asciiDigits } from '@/utils/format'
import { useAction } from '@/utils/useAction'
import { useFormat } from '@/utils/useFormat'

const props = defineProps<{ record: PatientRecord }>()
const emit = defineEmits<{ changed: [] }>()
const auth = useAuth()
const { num, dateTime, errorText } = useFormat()
const { busy, error, act } = useAction()

const SYMPTOMS = [
  'has_acid_reflux', 'has_blurred_vision', 'has_headache', 'has_palpitations', 'has_heartburn',
  'has_reduced_fetal_movement',
] as const

const symptomsOf = (log: DailyLog) => SYMPTOMS.filter((s) => log[s])

const open = ref(false)
const blank = () => ({
  systolic_bp: '', diastolic_bp: '', blood_glucose_mg_dl: '', weight_kg: '', other_complaints: '',
  symptoms: [] as string[],
})
const form = reactive(blank())

function start() {
  Object.assign(form, blank())
  error.value = null
  open.value = true
}

const number = (v: string) => (v.trim() ? Number(asciiDigits(v.trim())) : undefined)

async function save() {
  const values: Record<string, unknown> = {
    systolic_bp: number(form.systolic_bp),
    diastolic_bp: number(form.diastolic_bp),
    blood_glucose_mg_dl: number(form.blood_glucose_mg_dl),
    weight_kg: number(form.weight_kg),
    other_complaints: form.other_complaints.trim() || undefined,
  }
  for (const s of SYMPTOMS) if (form.symptoms.includes(s)) values[s] = true
  const ok = await act(() => patients.addVitals(props.record.patient.id, values), 'logs.added', true)
  if (ok) {
    open.value = false
    emit('changed')
  }
}

const fieldError = (name: string) => (error.value instanceof ApiError ? error.value.fieldErrors[name] : undefined)
</script>

<template>
  <div class="flex flex-col gap-4">
    <div v-if="auth.role === 'midwife'" class="flex justify-end">
      <button class="btn btn-primary btn-sm" @click="start">{{ $t('logs.add') }}</button>
    </div>
    <p v-if="!record.daily_logs.length" class="text-base-content/60">{{ $t('logs.empty') }}</p>
    <div v-else class="overflow-x-auto">
      <table class="table table-sm">
        <thead>
          <tr>
            <th>{{ $t('logs.when') }}</th>
            <th>{{ $t('logs.by') }}</th>
            <th>{{ $t('logs.bp') }}</th>
            <th>{{ $t('logs.blood_glucose_mg_dl') }}</th>
            <th>{{ $t('logs.weight_kg') }}</th>
            <th>{{ $t('logs.symptoms') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in record.daily_logs" :key="log.id" :class="{ 'bg-error/10': log.is_red_alert }">
            <td class="whitespace-nowrap">{{ dateTime(log.recorded_at) }}</td>
            <td>{{ log.recorded_by_id === record.patient.id ? $t('logs.byMother') : $t('logs.byStaff') }}</td>
            <td class="ltr text-start">
              {{ log.systolic_bp ? `${num(log.systolic_bp)}/${num(log.diastolic_bp)}` : '—' }}
            </td>
            <td>{{ num(log.blood_glucose_mg_dl) }}</td>
            <td>{{ num(log.weight_kg) }}</td>
            <td>
              <div class="flex flex-wrap gap-1">
                <span v-if="log.is_red_alert" class="badge badge-error badge-sm">{{ $t('logs.has_spotting_or_bleeding') }}</span>
                <span v-for="s in symptomsOf(log)" :key="s" class="badge badge-sm">{{ $t(`logs.${s}`) }}</span>
                <span v-if="log.other_complaints" class="text-xs">{{ log.other_complaints }}</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <ModalDialog v-model:open="open" :title="$t('logs.addTitle')" wide>
      <form class="flex flex-col gap-3" @submit.prevent="save">
        <div v-if="error" role="alert" class="alert alert-error alert-soft text-sm">{{ errorText(error) }}</div>
        <div class="grid gap-2 sm:grid-cols-4">
          <label v-for="f in ['systolic_bp', 'diastolic_bp', 'blood_glucose_mg_dl', 'weight_kg'] as const" :key="f" class="fieldset">
            <span class="fieldset-legend">{{ $t(`logs.${f}`) }}</span>
            <input v-model="form[f]" class="input ltr w-full" inputmode="decimal" :class="{ 'input-error': fieldError(f) }" />
          </label>
        </div>
        <fieldset class="fieldset">
          <legend class="fieldset-legend">{{ $t('logs.symptoms') }}</legend>
          <div class="grid gap-2 sm:grid-cols-3">
            <label v-for="s in SYMPTOMS" :key="s" class="label gap-2">
              <input v-model="form.symptoms" type="checkbox" class="checkbox checkbox-sm" :value="s" />{{ $t(`logs.${s}`) }}
            </label>
          </div>
        </fieldset>
        <label class="fieldset">
          <span class="fieldset-legend">{{ $t('logs.other_complaints') }}</span>
          <textarea v-model="form.other_complaints" class="textarea w-full" rows="2" maxlength="2000" />
        </label>
        <div class="modal-action">
          <button type="button" class="btn" @click="open = false">{{ $t('app.cancel') }}</button>
          <button class="btn btn-primary" :disabled="busy">{{ $t('app.save') }}</button>
        </div>
      </form>
    </ModalDialog>
  </div>
</template>
