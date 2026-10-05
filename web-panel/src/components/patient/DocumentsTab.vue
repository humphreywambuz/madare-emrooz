<script setup lang="ts">
import { onUnmounted, reactive, ref } from 'vue'

import { ApiError } from '@/api/client'
import { documents } from '@/api/endpoints'
import type { MedicalDocument, PatientRecord } from '@/api/types'
import AppIcon from '@/components/AppIcon.vue'
import DateInput from '@/components/DateInput.vue'
import EmptyState from '@/components/EmptyState.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import SectionCard from '@/components/SectionCard.vue'
import { useAuth } from '@/stores/auth'
import { asciiDigits, localMidnight } from '@/utils/format'
import { useAction } from '@/utils/useAction'
import { useFormat } from '@/utils/useFormat'

const props = defineProps<{ record: PatientRecord }>()
const emit = defineEmits<{ changed: [] }>()
const auth = useAuth()
const isMidwife = auth.role === 'midwife'
const { num, date, dateTime, errorText } = useFormat()
const { busy, error, act } = useAction()

const TYPES = ['blood_test', 'urine_test', 'thyroid_test', 'ultrasound', 'screening', 'imaging', 'other']
const sizeKb = (bytes: number) => num(Math.max(1, Math.round(bytes / 1024)))

// --- preview --------------------------------------------------------------------
const preview = reactive({ open: false, url: '', doc: null as MedicalDocument | null })
async function view(doc: MedicalDocument) {
  await act(async () => {
    const blob = await documents.file(props.record.patient.id, doc.id)
    URL.revokeObjectURL(preview.url)
    preview.url = URL.createObjectURL(blob)
    preview.doc = doc
    preview.open = true
  })
}
onUnmounted(() => URL.revokeObjectURL(preview.url))

// --- upload ---------------------------------------------------------------------
const uploading = ref(false)
const file = ref<File | null>(null)
const blank = () => ({ document_type: 'ultrasound', performed_at: '', fundal_height_cm: '', fetal_heart_rate_bpm: '', notes: '' })
const form = reactive(blank())

function startUpload() {
  Object.assign(form, blank())
  file.value = null
  error.value = null
  uploading.value = true
}

async function upload() {
  const data = new FormData()
  if (file.value) data.append('file', file.value)
  data.append('document_type', form.document_type)
  if (form.performed_at) data.append('performed_at', localMidnight(form.performed_at))
  if (form.fundal_height_cm.trim()) data.append('fundal_height_cm', asciiDigits(form.fundal_height_cm.trim()))
  if (form.fetal_heart_rate_bpm.trim()) data.append('fetal_heart_rate_bpm', asciiDigits(form.fetal_heart_rate_bpm.trim()))
  if (form.notes.trim()) data.append('notes', form.notes.trim())
  if (await act(() => documents.upload(props.record.patient.id, data), 'documents.uploaded', true)) {
    uploading.value = false
    emit('changed')
  }
}

// --- remove ---------------------------------------------------------------------
const removing = ref<MedicalDocument | null>(null)
const reason = ref('')
function startRemove(doc: MedicalDocument) {
  removing.value = doc
  reason.value = ''
}
async function remove() {
  const doc = removing.value!
  if (await act(() => documents.remove(props.record.patient.id, doc.id, reason.value || null), 'documents.removed')) {
    removing.value = null
    emit('changed')
  }
}

const fieldError = (name: string) => (error.value instanceof ApiError ? error.value.fieldErrors[name] : undefined)
</script>

<template>
  <div class="flex flex-col gap-6">
    <SectionCard flush :title="$t('patient.tabs.documents')">
      <template #actions>
        <button v-if="isMidwife" class="btn btn-primary btn-sm" @click="startUpload">
          <AppIcon name="upload" class="size-4" />{{ $t('documents.upload') }}
        </button>
      </template>

      <EmptyState v-if="!record.documents.length" icon="file" :title="$t('patient.tabs.documents')" :text="$t('documents.empty')" />
      <ul v-else class="list">
        <li v-for="doc in record.documents" :key="doc.id" class="list-row items-center">
          <span class="grid size-11 place-items-center rounded-xl bg-primary/10 text-primary">
            <AppIcon :name="doc.content_type.startsWith('image/') ? 'image' : 'file'" class="size-5" />
          </span>
          <div class="min-w-0">
            <div class="truncate font-semibold">{{ doc.original_filename }}</div>
            <div class="text-xs text-base-content/60">
              {{ $t(`documents.types.${doc.document_type}`) }}، {{ dateTime(doc.created_at) }}، {{ sizeKb(doc.file_size_bytes) }} KB
            </div>
          </div>
          <div v-if="doc.performed_at || doc.fundal_height_cm || doc.fetal_heart_rate_bpm || doc.notes"
               class="list-col-wrap flex flex-wrap gap-x-6 gap-y-1 text-sm">
            <span v-if="doc.performed_at">{{ $t('documents.performed_at') }}: <b>{{ date(doc.performed_at) }}</b></span>
            <span v-if="doc.fundal_height_cm">{{ $t('documents.fundal_height_cm') }}: <b>{{ num(doc.fundal_height_cm) }}</b></span>
            <span v-if="doc.fetal_heart_rate_bpm">{{ $t('documents.fetal_heart_rate_bpm') }}: <b>{{ num(doc.fetal_heart_rate_bpm) }}</b></span>
            <span v-if="doc.notes" class="w-full text-base-content/60">{{ doc.notes }}</span>
          </div>
          <button class="btn btn-sm btn-outline" :disabled="busy" @click="view(doc)"><AppIcon name="eye" class="size-4" />{{ $t('documents.view') }}</button>
          <button v-if="isMidwife" class="btn btn-sm btn-ghost btn-circle" :aria-label="$t('app.remove')" @click="startRemove(doc)">
            <AppIcon name="trash" class="size-4 text-error" />
          </button>
        </li>
      </ul>
    </SectionCard>

    <ModalDialog v-model:open="preview.open" :title="preview.doc?.original_filename ?? ''" wide>
      <img v-if="preview.doc?.content_type.startsWith('image/')" :src="preview.url" :alt="preview.doc.original_filename"
           class="max-h-[70vh] w-full rounded-box object-contain" />
      <iframe v-else-if="preview.url" :src="preview.url" class="h-[70vh] w-full rounded-box border-0" :title="preview.doc?.original_filename" />
      <div class="modal-action">
        <a class="btn" :href="preview.url" :download="preview.doc?.original_filename">
          <AppIcon name="download" class="size-4" />{{ $t('ui.download') }}
        </a>
      </div>
    </ModalDialog>

    <ModalDialog v-model:open="uploading" :title="$t('documents.uploadTitle')" wide>
      <form class="flex flex-col gap-2" @submit.prevent="upload">
        <div v-if="error" role="alert" class="alert alert-error alert-soft text-sm">{{ errorText(error) }}</div>
        <fieldset class="fieldset">
          <legend class="fieldset-legend">{{ $t('documents.file') }}</legend>
          <input type="file" class="file-input w-full" accept="image/jpeg,image/png,application/pdf" required
                 :class="{ 'file-input-error': fieldError('file') }"
                 @change="file = ($event.target as HTMLInputElement).files?.[0] ?? null" />
        </fieldset>
        <div class="grid gap-2 sm:grid-cols-2">
          <fieldset class="fieldset">
            <legend class="fieldset-legend">{{ $t('documents.document_type') }}</legend>
            <select v-model="form.document_type" class="select w-full">
              <option v-for="t in TYPES" :key="t" :value="t">{{ $t(`documents.types.${t}`) }}</option>
            </select>
          </fieldset>
          <fieldset class="fieldset">
            <legend class="fieldset-legend">{{ $t('documents.performed_at') }}</legend>
            <DateInput v-model="form.performed_at" :years-back="1" :years-ahead="0" />
          </fieldset>
          <fieldset class="fieldset">
            <legend class="fieldset-legend">{{ $t('documents.fundal_height_cm') }}</legend>
            <input v-model="form.fundal_height_cm" class="input ltr w-full" inputmode="decimal"
                   :class="{ 'input-error': fieldError('fundal_height_cm') }" />
          </fieldset>
          <fieldset class="fieldset">
            <legend class="fieldset-legend">{{ $t('documents.fetal_heart_rate_bpm') }}</legend>
            <input v-model="form.fetal_heart_rate_bpm" class="input ltr w-full" inputmode="numeric"
                   :class="{ 'input-error': fieldError('fetal_heart_rate_bpm') }" />
          </fieldset>
        </div>
        <fieldset class="fieldset">
          <legend class="fieldset-legend">{{ $t('documents.notes') }}</legend>
          <textarea v-model="form.notes" class="textarea w-full" rows="2" maxlength="2000" />
        </fieldset>
        <div class="modal-action">
          <button type="button" class="btn" @click="uploading = false">{{ $t('app.cancel') }}</button>
          <button class="btn btn-primary" :disabled="busy || !file">
            <span v-if="busy" class="loading loading-spinner loading-sm" />{{ $t('documents.upload') }}
          </button>
        </div>
      </form>
    </ModalDialog>

    <ModalDialog :open="removing !== null" :title="$t('documents.removeTitle')" @update:open="(v) => !v && (removing = null)">
      <form class="flex flex-col gap-2" @submit.prevent="remove">
        <p class="text-sm leading-relaxed">
          <span class="font-semibold break-all">{{ removing?.original_filename }}</span><br />
          <span class="text-base-content/60">{{ $t('documents.removeHelp') }}</span>
        </p>
        <fieldset class="fieldset">
          <legend class="fieldset-legend">{{ $t('documents.removeReason') }}</legend>
          <input v-model="reason" class="input w-full" maxlength="500" :placeholder="$t('documents.removeReasonPlaceholder')" />
        </fieldset>
        <div class="modal-action">
          <button type="button" class="btn" @click="removing = null">{{ $t('app.cancel') }}</button>
          <button class="btn btn-error" :disabled="busy">{{ $t('documents.removeConfirm') }}</button>
        </div>
      </form>
    </ModalDialog>
  </div>
</template>
