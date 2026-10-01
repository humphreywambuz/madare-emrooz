<script setup lang="ts">
// The summary card: who she is, her pregnancy at a glance, and her red flags.
import { computed, ref } from 'vue'

import { patients } from '@/api/endpoints'
import type { PatientHeader, RiskTag } from '@/api/types'
import ModalDialog from '@/components/ModalDialog.vue'
import { useAction } from '@/utils/useAction'
import { useFormat } from '@/utils/useFormat'

const props = defineProps<{ patient: PatientHeader; tags: RiskTag[] }>()
const emit = defineEmits<{ changed: [] }>()
const { fullName, mobile, num, date, enumLabel } = useFormat()
const { busy, error, act } = useAction()

const TAGS = ['needs_rhogam', 'thyroid', 'miscarriage_history', 'diabetes', 'hypertension', 'anemia', 'infectious_disease', 'other']
const available = computed(() => TAGS.filter((tag) => !props.tags.some((t) => t.tag === tag)))

const adding = ref(false)
const newTag = ref('')
const newNote = ref('')

function openAdd() {
  newTag.value = available.value[0] ?? ''
  newNote.value = ''
  error.value = null
  adding.value = true
}

async function addTag() {
  if (await act(() => patients.addTag(props.patient.id, newTag.value, newNote.value || null), 'app.saved', true)) {
    adding.value = false
    emit('changed')
  }
}

async function removeTag(tag: string) {
  if (await act(() => patients.removeTag(props.patient.id, tag), 'app.saved')) emit('changed')
}
</script>

<template>
  <div class="card bg-base-100 shadow-xs">
    <div class="card-body gap-4 p-5">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 class="text-2xl font-bold">
            {{ fullName(patient.first_name, patient.last_name) || $t('patients.noName') }}
          </h1>
          <div class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-base-content/70">
            <a class="ltr link-hover" :href="`tel:${patient.mobile}`">{{ mobile(patient.mobile) }}</a>
            <span v-if="patient.age !== null">{{ $t('patient.age', { n: num(patient.age) }) }}</span>
            <span v-if="patient.join_goal">{{ enumLabel('join_goal', patient.join_goal) }}</span>
            <span v-if="patient.reproductive_status">{{ enumLabel('reproductive_status', patient.reproductive_status) }}</span>
          </div>
        </div>
        <div v-if="patient.gestational_week !== null" class="stats bg-base-200">
          <div class="stat px-4 py-2">
            <div class="stat-value text-2xl text-primary">{{ $t('patient.week', { n: num(patient.gestational_week) }) }}</div>
            <div class="stat-desc">{{ $t('patient.due', { date: date(patient.estimated_due_date) }) }}</div>
          </div>
        </div>
      </div>

      <div class="text-sm">
        <span class="text-base-content/60">{{ $t('patient.midwife') }}:</span>{{ ' ' }}
        <span v-if="patient.midwife" class="font-medium">
          {{ fullName(patient.midwife.first_name, patient.midwife.last_name) }}
        </span>
        <span v-else class="text-warning">{{ $t('patient.noMidwife') }}</span>
      </div>

      <div>
        <div class="mb-2 flex items-center justify-between">
          <h2 class="font-semibold">{{ $t('patient.riskTags') }}</h2>
          <button v-if="available.length" class="btn btn-ghost btn-xs" @click="openAdd">+ {{ $t('patient.addTag') }}</button>
        </div>
        <p v-if="!tags.length" class="text-sm text-base-content/60">{{ $t('patient.noTags') }}</p>
        <div v-else class="flex flex-wrap gap-2">
          <span v-for="t in tags" :key="t.tag" class="badge badge-lg gap-1"
                :class="t.source === 'record' ? 'badge-warning badge-soft' : 'badge-error badge-soft'"
                :title="t.note ?? ''">
            {{ enumLabel('risk_tag', t.tag) }}
            <span v-if="t.source === 'record'" class="text-xs opacity-70">({{ $t('patient.fromRecord') }})</span>
            <span v-if="t.note" class="text-xs opacity-80">· {{ t.note }}</span>
            <button v-if="t.source === 'staff'" class="ms-1 opacity-60 hover:opacity-100" :disabled="busy"
                    :aria-label="$t('app.remove')" @click="removeTag(t.tag)">✕</button>
          </span>
        </div>
      </div>
    </div>

    <ModalDialog v-model:open="adding" :title="$t('patient.addTag')">
      <form class="flex flex-col gap-2" @submit.prevent="addTag">
        <select v-model="newTag" class="select w-full" required>
          <option v-for="tag in available" :key="tag" :value="tag">{{ enumLabel('risk_tag', tag) }}</option>
        </select>
        <input v-model="newNote" class="input w-full" maxlength="255" :placeholder="$t('patient.tagNote')" />
        <div class="modal-action">
          <button type="button" class="btn" @click="adding = false">{{ $t('app.cancel') }}</button>
          <button class="btn btn-primary" :disabled="busy">{{ $t('app.save') }}</button>
        </div>
      </form>
    </ModalDialog>
  </div>
</template>
