<script setup lang="ts">
import { onUnmounted, reactive, ref } from 'vue'

import { ApiError } from '@/api/client'
import { documents } from '@/api/endpoints'
import type { MedicalDocument, PatientRecord } from '@/api/types'
import DateInput from '@/components/DateInput.vue'
import ModalDialog from '@/components/ModalDialog.vue'
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
  <div class="flex flex-col gap-4">
    <div v-if="isMidwife" class="flex justify-end">
      <button class="btn btn-primary btn-sm" @click="startUpload">{{ $t('documents.upload') }}</button>
    </div>
    <p v-if="!record.documents.length" class="text-base-content/60">{{ $t('documents.empty') }}</p>
    <ul v-else class="divide-y divide-base-200">
      <li v-for="doc in record.documents" :key="doc.id" class="flex flex-wrap items-center gap-3 py-3">
        <span class="badge badge-primary badge-soft">{{ $t(`documents.types.${doc.document_type}`) }}</span>
        <div class="min-w-40 flex-1">
          <div class="font-medium break-all">{{ doc.original_filename }}</div>
          <div class="text-xs text-base-content/60">
            {{ dateTime(doc.created_at) }} · {{ sizeKb(doc.file_size_bytes) }} KB
            <template v-if="doc.performed_at"> · {{ $t('documents.performed_at') }}: {{ date(doc.performed_at) }}</template>
            <template v-if="doc.fundal_height_cm"> · {{ $t('documents.fundal_height_cm') }}: {{ num(doc.fundal_height_cm) }}</template>
            <template v-if="doc.fetal_heart_rate_bpm"> · {{ $t('documents.fetal_heart_rate_bpm') }}: {{ num(doc.fetal_heart_rate_bpm) }}</template>
          </div>
          <div v-if="doc.notes" class="text-sm">{{ doc.notes }}</div>
        </div>
        <button class="btn btn-sm" :disabled="busy" @click="view(doc)">{{ $t('documents.view') }}</button>
        <button v-if="isMidwife" class="btn btn-sm btn-ghost text-error" @click="startRemove(doc)">{{ $t('app.remove') }}</button>
      </li>
    </ul>

    <ModalDialog v-model:open="preview.open" :title="preview.doc?.original_filename ?? ''" wide>
      <img v-if="preview.doc?.content_type.startsWith('image/')" :src="preview.url" :alt="preview.doc.original_filename"
           class="max-h-[70vh] w-full rounded object-contain" />
      <iframe v-else-if="preview.url" :src="preview.url" class="h-[70vh] w-full rounded border-0" :title="preview.doc?.original_filename" />
      <div class="modal-action">
        <a class="btn btn-sm" :href="preview.url" :download="preview.doc?.original_filename">⬇</a>
        <button class="btn btn-sm" @click="preview.open = false">{{ $t('app.close') }}</button>
      </div>
    </ModalDialog>

    <ModalDialog v-model:open="uploading" :title="$t('documents.uploadTitle')" wide>
      <form class="flex flex-col gap-3" @submit.prevent="upload">
        <div v-if="error" role="alert" class="alert alert-error alert-soft text-sm">{{ errorText(error) }}</div>
        <label class="fieldset">
          <span class="fieldset-legend">{{ $t('documents.file') }}</span>
          <input type="file" class="file-input w-full" accept="image/jpeg,image/png,application/pdf" required
                 :class="{ 'file-input-error': fieldError('file') }"
                 @change="file = ($event.target as HTMLInputElement).files?.[0] ?? null" />
        </label>
        <div class="grid gap-2 sm:grid-cols-2">
          <label class="fieldset">
            <span class="fieldset-legend">{{ $t('documents.document_type') }}</span>
            <select v-model="form.document_type" class="select w-full">
              <option v-for="t in TYPES" :key="t" :value="t">{{ $t(`documents.types.${t}`) }}</option>
            </select>
          </label>
          <label class="fieldset">
            <span class="fieldset-legend">{{ $t('documents.performed_at') }}</span>
            <DateInput v-model="form.performed_at" :years-back="1" :years-ahead="0" />
          </label>
          <label class="fieldset">
            <span class="fieldset-legend">{{ $t('documents.fundal_height_cm') }}</span>
            <input v-model="form.fundal_height_cm" class="input ltr w-full" inputmode="decimal"
                   :class="{ 'input-error': fieldError('fundal_height_cm') }" />
          </label>
          <label class="fieldset">
            <span class="fieldset-legend">{{ $t('documents.fetal_heart_rate_bpm') }}</span>
            <input v-model="form.fetal_heart_rate_bpm" class="input ltr w-full" inputmode="numeric"
                   :class="{ 'input-error': fieldError('fetal_heart_rate_bpm') }" />
          </label>
        </div>
        <label class="fieldset">
          <span class="fieldset-legend">{{ $t('documents.notes') }}</span>
          <textarea v-model="form.notes" class="textarea w-full" rows="2" maxlength="2000" />
        </label>
        <div class="modal-action">
          <button type="button" class="btn" @click="uploading = false">{{ $t('app.cancel') }}</button>
          <button class="btn btn-primary" :disabled="busy || !file">
            <span v-if="busy" class="loading loading-spinner loading-sm" />{{ $t('documents.upload') }}
          </button>
        </div>
      </form>
    </ModalDialog>

    <ModalDialog :open="removing !== null" :title="$t('documents.removeTitle')" @update:open="(v) => !v && (removing = null)">
      <form class="flex flex-col gap-3" @submit.prevent="remove">
        <p class="text-sm">
          <span class="font-medium break-all">{{ removing?.original_filename }}</span><br />
          <span class="text-base-content/70">{{ $t('documents.removeHelp') }}</span>
        </p>
        <label class="fieldset">
          <span class="fieldset-legend">{{ $t('documents.removeReason') }}</span>
          <input v-model="reason" class="input w-full" maxlength="500" :placeholder="$t('documents.removeReasonPlaceholder')" />
        </label>
        <div class="modal-action">
          <button type="button" class="btn" @click="removing = null">{{ $t('app.cancel') }}</button>
          <button class="btn btn-error" :disabled="busy">{{ $t('app.remove') }}</button>
        </div>
      </form>
    </ModalDialog>
  </div>
</template>
