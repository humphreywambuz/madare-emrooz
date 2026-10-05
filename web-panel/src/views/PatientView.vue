<script setup lang="ts">
// One mother's record. Opening it is written to the audit log by the backend.
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { patients } from '@/api/endpoints'
import AsyncState from '@/components/AsyncState.vue'
import DocumentsTab from '@/components/patient/DocumentsTab.vue'
import LogsTab from '@/components/patient/LogsTab.vue'
import NotesTab from '@/components/patient/NotesTab.vue'
import OverviewTab from '@/components/patient/OverviewTab.vue'
import PathsTab from '@/components/patient/PathsTab.vue'
import PatientHeader from '@/components/patient/PatientHeader.vue'
import PatientMargin from '@/components/patient/PatientMargin.vue'
import PregnancyTab from '@/components/patient/PregnancyTab.vue'
import { useAsync } from '@/utils/useAsync'

const props = defineProps<{ id: string }>()
const route = useRoute()
const router = useRouter()

const TABS = {
  overview: OverviewTab,
  pregnancy: PregnancyTab,
  logs: LogsTab,
  documents: DocumentsTab,
  paths: PathsTab,
  notes: NotesTab,
} as const
type Tab = keyof typeof TABS

const tab = computed<Tab>(() => (route.query.tab as Tab) in TABS ? (route.query.tab as Tab) : 'overview')
const { data: record, loading, error, run } = useAsync(() => patients.record(props.id))
watch(() => props.id, run, { immediate: true })

function select(name: Tab) {
  router.replace({ query: { ...route.query, tab: name } })
}
</script>

<template>
  <section class="flex flex-col gap-6">
    <div class="breadcrumbs p-0 text-sm">
      <ul>
        <li><RouterLink to="/patients">{{ $t('patient.back') }}</RouterLink></li>
        <li v-if="record" class="font-semibold">{{ [record.patient.first_name, record.patient.last_name].filter(Boolean).join(' ') }}</li>
      </ul>
    </div>
    <AsyncState :loading="loading" :error="error" @retry="run">
      <template v-if="record">
        <PatientHeader :patient="record.patient" />
        <div class="grid gap-6 lg:grid-cols-3">
          <div class="flex min-w-0 flex-col gap-6 lg:col-span-2">
            <div class="overflow-x-auto">
              <div role="tablist" class="tabs tabs-box w-max border border-base-300 bg-base-100">
                <button v-for="(_, name) in TABS" :key="name" role="tab" class="tab whitespace-nowrap [--tab-bg:var(--color-primary)]"
                        :class="{ 'tab-active text-primary-content': tab === name }" :aria-selected="tab === name" @click="select(name)">
                  {{ $t(`patient.tabs.${name}`) }}
                </button>
              </div>
            </div>
            <Transition name="page" mode="out-in">
              <component :is="TABS[tab]" :key="tab" :record="record" @changed="run" />
            </Transition>
          </div>
          <PatientMargin :record="record" @changed="run" />
        </div>
      </template>
    </AsyncState>
  </section>
</template>
