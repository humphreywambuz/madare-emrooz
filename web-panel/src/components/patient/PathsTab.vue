<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { patients } from '@/api/endpoints'
import type { PatientRecord } from '@/api/types'
import { useAuth } from '@/stores/auth'
import { useAction } from '@/utils/useAction'
import { useFormat } from '@/utils/useFormat'

import FieldList from './FieldList.vue'

const props = defineProps<{ record: PatientRecord }>()
const emit = defineEmits<{ changed: [] }>()
const { t } = useI18n()
const auth = useAuth()
const { num, dateTime, enumLabel, yesNo } = useFormat()
const { busy, act } = useAction()
const id = computed(() => props.record.patient.id)

const fitness = computed(() => props.record.fitness_profile)
const rehab = computed(() => props.record.rehab_profile)

// Rehab answers: the common questions, then only the ones of her sub-type that she answered.
const ENUM_FIELDS: Record<string, string> = {
  subcategory: 'subcategory', injury_onset: 'injury_onset', pain_type: 'pain_type',
  time_since_delivery: 'time_since_delivery', training_goal: 'training_goal',
  fitness_level: 'fitness_level', referral_reason: 'referral_reason',
}
const REHAB_FIELDS = [
  'subcategory', 'pain_level', 'had_related_surgery', 'related_surgery_name', 'uses_pain_medication',
  'injury_onset', 'pain_type', 'has_daily_movement_limitation', 'time_since_delivery', 'has_pelvic_warning_signs',
  'has_diastasis_recti_or_stitch_pain', 'training_goal', 'fitness_level', 'has_recurrent_muscle_spasms', 'referral_reason',
]
const rehabRows = computed(() => {
  const r = rehab.value
  if (!r) return []
  return REHAB_FIELDS.filter((f) => r[f] !== null && r[f] !== undefined).map((f) => {
    const v = r[f]
    const value = ENUM_FIELDS[f] ? enumLabel(ENUM_FIELDS[f], v as string)
      : typeof v === 'boolean' ? yesNo(v) : typeof v === 'number' ? num(v) : String(v)
    return { label: t(`rehab.${f}`), value }
  })
})

const imagingDocs = computed(() => props.record.documents.filter((d) => d.document_type === 'imaging'))
const imagingDoc = computed(() => props.record.documents.find((d) => d.id === rehab.value?.imaging_document_id))
const chosenImaging = ref('')

const approval = computed(() =>
  props.record.approvals.find((a) => a.scope === 'rehabilitation_plan' && a.is_active),
)

async function run(call: () => Promise<unknown>, success: string) {
  if (await act(call, success)) emit('changed')
}
</script>

<template>
  <div class="grid gap-6 lg:grid-cols-2">
    <section class="rounded-box border border-base-300 p-4">
      <h2 class="mb-3 text-lg font-semibold">{{ $t('paths.fitness') }}</h2>
      <p v-if="!fitness" class="text-base-content/60">{{ $t('paths.noFitness') }}</p>
      <div v-else class="flex flex-col gap-3">
        <FieldList :rows="[
          { label: $t('paths.goal'), value: enumLabel('fitness_goal', fitness.goal) },
          { label: $t('paths.goalNote'), value: fitness.goal_note || '—' },
          { label: $t('paths.dashboard'), value: fitness.dashboard_unlocked ? $t('paths.unlocked') : $t('paths.locked') },
        ]" />
        <div class="flex flex-wrap items-center justify-between gap-2">
          <span>
            {{ $t('paths.visit') }}:
            <b>{{ fitness.specialist_visit_completed ? $t('paths.visitDone', { date: dateTime(fitness.specialist_visit_at) }) : $t('paths.visitPending') }}</b>
          </span>
          <button v-if="!fitness.specialist_visit_completed" class="btn btn-sm" :disabled="busy"
                  @click="run(() => patients.fitnessVisit(id), 'paths.visitRecorded')">{{ $t('paths.markVisit') }}</button>
        </div>
      </div>
    </section>

    <section class="rounded-box border border-base-300 p-4">
      <h2 class="mb-3 text-lg font-semibold">{{ $t('paths.rehab') }}</h2>
      <p v-if="!rehab" class="text-base-content/60">{{ $t('paths.noRehab') }}</p>
      <div v-else class="flex flex-col gap-4">
        <FieldList :rows="rehabRows" />

        <div class="flex flex-wrap items-center justify-between gap-2">
          <span>
            {{ $t('paths.visit') }}:
            <b>{{ rehab.specialist_visit_completed ? $t('paths.visitDone', { date: dateTime(rehab.specialist_visit_at) }) : $t('paths.visitPending') }}</b>
          </span>
          <button v-if="!rehab.specialist_visit_completed" class="btn btn-sm" :disabled="busy"
                  @click="run(() => patients.rehabVisit(id), 'paths.visitRecorded')">{{ $t('paths.markVisit') }}</button>
        </div>

        <div class="flex flex-wrap items-center justify-between gap-2">
          <span>
            {{ $t('paths.approval') }}:
            <b>{{ approval ? $t('paths.approved', { date: dateTime(approval.approved_at) }) : $t('paths.notApproved') }}</b>
          </span>
          <template v-if="auth.role === 'doctor'">
            <button v-if="!approval" class="btn btn-sm btn-primary" :disabled="busy"
                    @click="run(() => patients.approve(id, 'rehabilitation_plan'), 'paths.approvedDone')">{{ $t('paths.approve') }}</button>
            <button v-else class="btn btn-sm btn-ghost text-error" :disabled="busy"
                    @click="run(() => patients.revoke(id, 'rehabilitation_plan'), 'paths.revokedDone')">{{ $t('paths.revoke') }}</button>
          </template>
        </div>

        <div class="alert" :class="rehab.is_advanced_locked ? 'alert-warning alert-soft' : 'alert-success alert-soft'">
          {{ $t('paths.advanced') }}: {{ rehab.is_advanced_locked ? $t('paths.advancedLocked') : $t('paths.advancedOpen') }}
        </div>

        <div class="flex flex-col gap-2">
          <span>{{ $t('paths.imaging') }}: <b>{{ imagingDoc?.original_filename ?? $t('paths.noImaging') }}</b></span>
          <div v-if="auth.role === 'midwife' && imagingDocs.length" class="join">
            <select v-model="chosenImaging" class="select select-sm join-item flex-1">
              <option value="" disabled>{{ $t('paths.linkImaging') }}</option>
              <option v-for="d in imagingDocs" :key="d.id" :value="d.id">{{ d.original_filename }}</option>
            </select>
            <button class="btn btn-sm join-item" :disabled="busy || !chosenImaging"
                    @click="run(() => patients.linkImaging(id, chosenImaging), 'paths.linked')">{{ $t('app.save') }}</button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
