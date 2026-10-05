<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { PatientRecord } from '@/api/types'
import SectionCard from '@/components/SectionCard.vue'
import { useFormat } from '@/utils/useFormat'

import FieldList from './FieldList.vue'

const props = defineProps<{ record: PatientRecord }>()
const { t } = useI18n()
const { num, date, digits, enumLabel, yesNo } = useFormat()

const profileRows = computed(() => {
  const p = props.record.profile
  if (!p) return []
  return [
    { label: t('profile.national_code'), value: digits(p.national_code) },
    { label: t('profile.birth_date'), value: date(p.birth_date) },
    { label: t('profile.height_cm'), value: num(p.height_cm) },
    { label: t('profile.initial_weight_kg'), value: num(p.initial_weight_kg) },
    { label: t('profile.mother_blood_type'), value: p.mother_blood_type ?? '—' },
    { label: t('profile.spouse_blood_type'), value: p.spouse_blood_type ?? '—' },
    { label: t('profile.join_goal'), value: enumLabel('join_goal', p.join_goal) },
    { label: t('profile.reproductive_status'), value: enumLabel('reproductive_status', p.reproductive_status) },
  ]
})

const COUNTS = ['previous_children_count', 'miscarriage_count']
const TEXTS = [
  'nutrient_deficiency_details', 'underlying_conditions', 'previous_surgery_details', 'current_medications',
  'dental_notes', 'other_infectious_diseases', 'spouse_health_notes',
]
const HISTORY_ORDER = [
  'previous_children_count', 'miscarriage_count', 'has_diabetes', 'has_hypertension', 'has_nutrient_deficiency',
  'nutrient_deficiency_details', 'has_thyroid_disorder', 'has_breast_cyst', 'has_ovarian_cyst_pcos',
  'underlying_conditions', 'has_previous_surgery', 'previous_surgery_details', 'has_anesthesia_history',
  'current_medications', 'has_dental_infection', 'dental_notes', 'has_hiv', 'has_hepatitis_b', 'has_hepatitis_c',
  'other_infectious_diseases', 'spouse_has_diabetes', 'spouse_has_varicocele', 'spouse_has_genetic_disorder',
  'spouse_health_notes',
]

const historyRows = computed(() => {
  const h = props.record.medical_history
  if (!h) return []
  return HISTORY_ORDER.filter((k) => !TEXTS.includes(k) || h[k]).map((k) => ({
    label: t(`history.${k}`),
    value: COUNTS.includes(k) ? num(h[k] as number | null) : TEXTS.includes(k) ? String(h[k]) : yesNo(h[k]),
  }))
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <SectionCard :title="$t('profile.title')">
      <FieldList v-if="profileRows.length" :rows="profileRows" />
      <p v-else class="text-sm text-base-content/60">{{ $t('profile.none') }}</p>
    </SectionCard>
    <SectionCard :title="$t('history.title')">
      <FieldList v-if="historyRows.length" :rows="historyRows" />
      <p v-else class="text-sm text-base-content/60">{{ $t('history.none') }}</p>
    </SectionCard>
  </div>
</template>
