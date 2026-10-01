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
  <section class="flex flex-col gap-4">
    <RouterLink to="/patients" class="link link-hover w-fit text-sm">← {{ $t('patient.back') }}</RouterLink>
    <AsyncState :loading="loading" :error="error" @retry="run">
      <template v-if="record">
        <PatientHeader :patient="record.patient" :tags="record.risk_tags" @changed="run" />
        <div class="card bg-base-100 shadow-xs">
          <div role="tablist" class="tabs tabs-border overflow-x-auto px-2 pt-1">
            <button v-for="(_, name) in TABS" :key="name" role="tab" class="tab whitespace-nowrap"
                    :class="{ 'tab-active': tab === name }" :aria-selected="tab === name" @click="select(name)">
              {{ $t(`patient.tabs.${name}`) }}
            </button>
          </div>
          <div class="card-body p-5">
            <component :is="TABS[tab]" :record="record" @changed="run" />
          </div>
        </div>
      </template>
    </AsyncState>
  </section>
</template>
