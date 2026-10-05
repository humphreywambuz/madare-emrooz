<script setup lang="ts">
// Who she is, and where her pregnancy stands.
import { computed } from 'vue'

import type { PatientHeader } from '@/api/types'
import AppIcon from '@/components/AppIcon.vue'
import GestationRuler from '@/components/GestationRuler.vue'
import SectionCard from '@/components/SectionCard.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { useFormat } from '@/utils/useFormat'

const props = defineProps<{ patient: PatientHeader }>()
const { fullName, mobile, num, enumLabel } = useFormat()

const name = computed(() => fullName(props.patient.first_name, props.patient.last_name))
const chips = computed(() => [
  props.patient.join_goal ? { text: enumLabel('join_goal', props.patient.join_goal), tone: 'badge-primary badge-soft' } : null,
  props.patient.reproductive_status ? { text: enumLabel('reproductive_status', props.patient.reproductive_status), tone: 'badge-ghost' } : null,
].filter((c): c is { text: string; tone: string } => c !== null))
</script>

<template>
  <SectionCard>
    <div class="flex flex-wrap items-center gap-4">
      <UserAvatar :name="name || '?'" size="lg" />
      <div class="min-w-0 flex-1">
        <h1 class="font-display text-2xl leading-tight md:text-3xl">{{ name || $t('patients.noName') }}</h1>
        <div class="mt-2 flex flex-wrap items-center gap-2 text-sm text-base-content/60">
          <span v-if="patient.age !== null">{{ $t('patient.age', { n: num(patient.age) }) }}</span>
          <span v-for="chip in chips" :key="chip.text" class="badge badge-sm" :class="chip.tone">{{ chip.text }}</span>
        </div>
      </div>
      <a class="btn btn-outline ltr" :href="`tel:${patient.mobile}`"><AppIcon name="phone" class="size-4" />{{ mobile(patient.mobile) }}</a>
    </div>
    <template v-if="patient.gestational_week !== null">
      <div class="divider my-0" />
      <GestationRuler :week="patient.gestational_week" :due-date="patient.estimated_due_date" />
    </template>
  </SectionCard>
</template>
