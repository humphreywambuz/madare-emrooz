<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { ApiError } from '@/api/client'
import { type NewStaff, staff as staffApi } from '@/api/endpoints'
import type { StaffMember } from '@/api/types'
import AppIcon from '@/components/AppIcon.vue'
import AsyncState from '@/components/AsyncState.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { useToasts } from '@/stores/toast'
import { asciiDigits } from '@/utils/format'
import { useAsync } from '@/utils/useAsync'
import { useFormat } from '@/utils/useFormat'

const { t } = useI18n()
const { mobile, fullName, errorText } = useFormat()
const toasts = useToasts()

const { data, loading, error, run } = useAsync(() => staffApi.list())
onMounted(run)

const ROLE_TONE: Record<string, string> = { midwife: 'badge-primary', doctor: 'badge-info', admin: 'badge-neutral' }

const blank = (): NewStaff => ({ mobile: '', role: 'midwife', first_name: '', last_name: '', bio: '', is_listed: true })
const creating = ref(false)
const form = reactive<NewStaff>(blank())
const formError = ref<unknown>(null)
const busy = ref(false)

function openCreate() {
  Object.assign(form, blank())
  formError.value = null
  creating.value = true
}

async function create() {
  busy.value = true
  formError.value = null
  try {
    await staffApi.create({ ...form, mobile: asciiDigits(form.mobile), bio: form.bio || null })
    creating.value = false
    toasts.show(t('staff.created'))
    await run()
  } catch (e) {
    formError.value = e
  } finally {
    busy.value = false
  }
}

const editing = ref<StaffMember | null>(null)
const editForm = reactive({ first_name: '', last_name: '', bio: '', is_listed: true, is_active: true })

function openEdit(member: StaffMember) {
  editing.value = member
  Object.assign(editForm, {
    first_name: member.first_name ?? '', last_name: member.last_name ?? '', bio: member.bio ?? '',
    is_listed: member.is_listed, is_active: member.is_active,
  })
  formError.value = null
}

async function saveEdit() {
  if (!editing.value) return
  busy.value = true
  formError.value = null
  try {
    await staffApi.update(editing.value.user_id, { ...editForm, bio: editForm.bio || null })
    editing.value = null
    toasts.show(t('staff.updated'))
    await run()
  } catch (e) {
    formError.value = e
  } finally {
    busy.value = false
  }
}

const fieldError = (name: string) => (formError.value instanceof ApiError ? formError.value.fieldErrors[name] : undefined)
</script>

<template>
  <section class="flex flex-col gap-6">
    <PageHeader :title="$t('staff.title')" :subtitle="$t('staff.subtitle')">
      <button class="btn btn-primary" @click="openCreate"><AppIcon name="plus" class="size-4" />{{ $t('staff.add') }}</button>
    </PageHeader>

    <AsyncState :loading="loading" :error="error" @retry="run">
      <SectionCard flush>
        <div class="overflow-x-auto">
          <table class="table">
            <thead>
              <tr class="text-xs text-base-content/60">
                <th>{{ $t('patients.name') }}</th>
                <th>{{ $t('staff.role') }}</th>
                <th>{{ $t('staff.mobile') }}</th>
                <th>{{ $t('staff.is_listed') }}</th>
                <th>{{ $t('staff.is_active') }}</th>
                <th />
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in data?.items" :key="m.user_id" :class="{ 'opacity-60': !m.is_active }">
                <td>
                  <div class="flex items-center gap-3">
                    <UserAvatar :name="fullName(m.first_name, m.last_name) || '?'" />
                    <div>
                      <div class="font-semibold">{{ fullName(m.first_name, m.last_name) || '—' }}</div>
                      <div v-if="m.bio" class="max-w-xs truncate text-sm text-base-content/60">{{ m.bio }}</div>
                    </div>
                  </div>
                </td>
                <td><span class="badge badge-soft" :class="ROLE_TONE[m.role]">{{ $t(`roles.${m.role}`) }}</span></td>
                <td class="ltr text-start whitespace-nowrap">{{ mobile(m.mobile) }}</td>
                <td>
                  <template v-if="m.role === 'midwife'">{{ m.is_listed ? $t('staff.listed') : $t('staff.hidden') }}</template>
                </td>
                <td>
                  <span class="inline-flex items-center gap-2">
                    <span class="status" :class="m.is_active ? 'status-success' : 'status-error'" />
                    {{ m.is_active ? $t('staff.active') : $t('staff.inactive') }}
                  </span>
                </td>
                <td class="text-end">
                  <button class="btn btn-ghost btn-sm" @click="openEdit(m)"><AppIcon name="pencil" class="size-4" />{{ $t('app.edit') }}</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </SectionCard>
    </AsyncState>

    <ModalDialog v-model:open="creating" :title="$t('staff.addTitle')">
      <form class="flex flex-col gap-2" @submit.prevent="create">
        <div v-if="formError" role="alert" class="alert alert-error alert-soft text-sm">{{ errorText(formError) }}</div>
        <div class="grid gap-2 sm:grid-cols-2">
          <label class="fieldset">
            <span class="fieldset-legend">{{ $t('staff.first_name') }}</span>
            <input v-model="form.first_name" class="input w-full" required maxlength="100" />
          </label>
          <label class="fieldset">
            <span class="fieldset-legend">{{ $t('staff.last_name') }}</span>
            <input v-model="form.last_name" class="input w-full" required maxlength="100" />
          </label>
          <label class="fieldset">
            <span class="fieldset-legend">{{ $t('staff.mobile') }}</span>
            <input v-model="form.mobile" class="input ltr w-full" inputmode="tel" required
                   :class="{ 'input-error': fieldError('mobile') }" :placeholder="$t('login.mobileHint')" />
          </label>
          <label class="fieldset">
            <span class="fieldset-legend">{{ $t('staff.role') }}</span>
            <select v-model="form.role" class="select w-full">
              <option value="midwife">{{ $t('roles.midwife') }}</option>
              <option value="doctor">{{ $t('roles.doctor') }}</option>
              <option value="admin">{{ $t('roles.admin') }}</option>
            </select>
          </label>
        </div>
        <label class="fieldset">
          <span class="fieldset-legend">{{ $t('staff.bio') }} <span class="text-base-content/50">({{ $t('app.optional') }})</span></span>
          <textarea v-model="form.bio" class="textarea w-full" rows="2" maxlength="2000" />
        </label>
        <label v-if="form.role === 'midwife'" class="label gap-2">
          <input v-model="form.is_listed" type="checkbox" class="toggle toggle-primary" />{{ $t('staff.is_listed') }}
        </label>
        <div class="modal-action">
          <button type="button" class="btn" @click="creating = false">{{ $t('app.cancel') }}</button>
          <button class="btn btn-primary" :disabled="busy">{{ $t('app.save') }}</button>
        </div>
      </form>
    </ModalDialog>

    <ModalDialog :open="editing !== null" :title="$t('staff.edit')" @update:open="(v) => !v && (editing = null)">
      <form v-if="editing" class="flex flex-col gap-2" @submit.prevent="saveEdit">
        <div v-if="formError" role="alert" class="alert alert-error alert-soft text-sm">{{ errorText(formError) }}</div>
        <div class="text-sm text-base-content/60">
          {{ $t(`roles.${editing.role}`) }} · <span class="ltr">{{ mobile(editing.mobile) }}</span>
        </div>
        <div class="grid gap-2 sm:grid-cols-2">
          <label class="fieldset">
            <span class="fieldset-legend">{{ $t('staff.first_name') }}</span>
            <input v-model="editForm.first_name" class="input w-full" required maxlength="100" />
          </label>
          <label class="fieldset">
            <span class="fieldset-legend">{{ $t('staff.last_name') }}</span>
            <input v-model="editForm.last_name" class="input w-full" required maxlength="100" />
          </label>
        </div>
        <label class="fieldset">
          <span class="fieldset-legend">{{ $t('staff.bio') }}</span>
          <textarea v-model="editForm.bio" class="textarea w-full" rows="2" maxlength="2000" />
        </label>
        <label v-if="editing.role === 'midwife'" class="label gap-2">
          <input v-model="editForm.is_listed" type="checkbox" class="toggle toggle-primary" />{{ $t('staff.is_listed') }}
        </label>
        <label class="label gap-2">
          <input v-model="editForm.is_active" type="checkbox" class="toggle toggle-primary" />{{ $t('staff.is_active') }}
        </label>
        <p v-if="editing.role === 'midwife'" class="text-sm text-base-content/60">{{ $t('staff.deactivateHelp') }}</p>
        <div class="modal-action">
          <button type="button" class="btn" @click="editing = null">{{ $t('app.cancel') }}</button>
          <button class="btn btn-primary" :disabled="busy">{{ $t('app.save') }}</button>
        </div>
      </form>
    </ModalDialog>
  </section>
</template>
