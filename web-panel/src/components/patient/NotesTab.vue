<script setup lang="ts">
import { ref } from 'vue'

import { patients } from '@/api/endpoints'
import type { PatientRecord } from '@/api/types'
import EmptyState from '@/components/EmptyState.vue'
import SectionCard from '@/components/SectionCard.vue'
import UserAvatar from '@/components/UserAvatar.vue'
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
  <div class="flex flex-col gap-6">
    <SectionCard :title="$t('notes.add')">
      <form class="flex flex-col gap-3" @submit.prevent="add">
        <textarea v-model="body" class="textarea w-full" rows="3" maxlength="5000" :placeholder="$t('notes.placeholder')" />
        <div class="flex justify-end">
          <button class="btn btn-primary btn-sm" :disabled="busy || !body.trim()">{{ $t('notes.add') }}</button>
        </div>
      </form>
    </SectionCard>

    <SectionCard :title="$t('patient.tabs.notes')" :flush="!record.notes.length">
      <EmptyState v-if="!record.notes.length" icon="note" :title="$t('patient.tabs.notes')" :text="$t('notes.empty')" />
      <div v-else class="flex flex-col gap-2">
        <div v-for="note in record.notes" :key="note.id" class="chat chat-start">
          <UserAvatar :name="note.author_name ?? '?'" class="chat-image" />
          <div class="chat-header gap-2">
            {{ note.author_name ?? '—' }}
            <span class="text-base-content/60">{{ $t(`roles.${note.author_role}`) }}</span>
          </div>
          <div class="chat-bubble bg-primary/10 text-base-content whitespace-pre-line">{{ note.body }}</div>
          <div class="chat-footer text-base-content/60">{{ dateTime(note.created_at) }}</div>
        </div>
      </div>
    </SectionCard>
  </div>
</template>
