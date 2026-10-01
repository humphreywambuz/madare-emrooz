<script setup lang="ts">
import { ref } from 'vue'

import { patients } from '@/api/endpoints'
import type { PatientRecord } from '@/api/types'
import { useAction } from '@/utils/useAction'
import { useFormat } from '@/utils/useFormat'

const props = defineProps<{ record: PatientRecord }>()
const emit = defineEmits<{ changed: [] }>()
const { dateTime } = useFormat()
const { busy, act } = useAction()
const body = ref('')

async function add() {
  if (await act(() => patients.addNote(props.record.patient.id, body.value.trim()), 'notes.added')) {
    body.value = ''
    emit('changed')
  }
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <form class="flex flex-col gap-2" @submit.prevent="add">
      <textarea v-model="body" class="textarea w-full" rows="3" maxlength="5000" :placeholder="$t('notes.placeholder')" />
      <div class="flex justify-end">
        <button class="btn btn-primary btn-sm" :disabled="busy || !body.trim()">{{ $t('notes.add') }}</button>
      </div>
    </form>
    <p v-if="!record.notes.length" class="text-base-content/60">{{ $t('notes.empty') }}</p>
    <ul v-else class="flex flex-col gap-3">
      <li v-for="note in record.notes" :key="note.id" class="rounded-box bg-base-200 p-3">
        <div class="mb-1 flex flex-wrap gap-2 text-sm text-base-content/60">
          <span class="font-medium text-base-content">{{ note.author_name ?? '—' }}</span>
          <span>{{ $t(`roles.${note.author_role}`) }}</span>
          <span>·</span>
          <span>{{ dateTime(note.created_at) }}</span>
        </div>
        <p class="whitespace-pre-line">{{ note.body }}</p>
      </li>
    </ul>
  </div>
</template>
