<script setup lang="ts">
// The chart margin: her midwife, her risk flags and her latest vitals, in view on every tab.
import type { PatientRecord } from '@/api/types'
import AppIcon from '@/components/AppIcon.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import SectionCard from '@/components/SectionCard.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { useFormat } from '@/utils/useFormat'
import { useRiskTags } from '@/utils/useRiskTags'
import { useVitalsTrends } from '@/utils/useVitalsTrends'

const props = defineProps<{ record: PatientRecord }>()
const emit = defineEmits<{ changed: [] }>()
const { fullName, enumLabel } = useFormat()
const { trends } = useVitalsTrends(() => props.record.daily_logs)
const { busy, available, adding, newTag, newNote, openAdd, add, remove } = useRiskTags(
  () => props.record.patient.id, () => props.record.risk_tags, () => emit('changed'),
)
const midwifeName = () => fullName(props.record.patient.midwife?.first_name, props.record.patient.midwife?.last_name)
</script>

<template>
  <aside class="flex flex-col gap-6">
    <SectionCard :title="$t('patient.midwife')">
      <div v-if="record.patient.midwife" class="flex items-center gap-3">
        <UserAvatar :name="midwifeName()" />
        <span class="font-semibold">{{ midwifeName() }}</span>
      </div>
      <div v-else class="flex items-center gap-3 text-warning">
        <span class="grid size-10 place-items-center rounded-full bg-warning/10"><AppIcon name="user" class="size-5" /></span>
        <span class="font-semibold">{{ $t('patient.noMidwife') }}</span>
      </div>
    </SectionCard>

    <SectionCard :title="$t('patient.riskTags')" :subtitle="$t('ui.riskTagsHelp')">
      <template #actions>
        <button v-if="available.length" class="btn btn-ghost btn-sm btn-circle" :aria-label="$t('patient.addTag')" :title="$t('patient.addTag')"
                @click="openAdd"><AppIcon name="plus" class="size-4" /></button>
      </template>
      <p v-if="!record.risk_tags.length" class="text-sm text-base-content/60">{{ $t('patient.noTags') }}</p>
      <ul v-else class="flex flex-col gap-2">
        <li v-for="t in record.risk_tags" :key="t.tag" class="flex items-start gap-3 rounded-field bg-warning/10 px-3 py-2">
          <AppIcon name="tag" class="mt-0.5 size-4 shrink-0 text-warning" />
          <div class="min-w-0 flex-1">
            <div class="text-sm font-semibold">{{ enumLabel('risk_tag', t.tag) }}</div>
            <div class="text-xs text-base-content/60">{{ t.note || (t.source === 'record' ? $t('patient.fromRecord') : '') }}</div>
          </div>
          <button v-if="t.source === 'staff'" class="btn btn-ghost btn-xs btn-circle" :disabled="busy"
                  :aria-label="$t('app.remove')" @click="remove(t.tag)"><AppIcon name="x" class="size-3" /></button>
        </li>
      </ul>
    </SectionCard>

    <SectionCard :title="$t('ui.latestVitals')">
      <dl class="flex flex-col divide-y divide-base-300">
        <div v-for="trend in trends" :key="trend.key" class="flex items-baseline justify-between gap-2 py-2 first:pt-0 last:pb-0">
          <dt class="text-sm text-base-content/60">{{ $t(trend.title) }}</dt>
          <dd class="font-display text-xl tabular-nums" :class="{ 'text-error': trend.high }"><bdi>{{ trend.latest ?? '—' }}</bdi></dd>
        </div>
      </dl>
    </SectionCard>

    <ModalDialog v-model:open="adding" :title="$t('patient.addTag')">
      <form class="flex flex-col gap-2" @submit.prevent="add">
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
  </aside>
</template>
