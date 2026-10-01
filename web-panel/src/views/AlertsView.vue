<script setup lang="ts">
// A midwife's red alerts, or (mode "admin") alerts from mothers who have no midwife yet.
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { alerts as alertsApi } from '@/api/endpoints'
import type { Alert } from '@/api/types'
import AsyncState from '@/components/AsyncState.vue'
import { useToasts } from '@/stores/toast'
import { useAsync } from '@/utils/useAsync'
import { useFormat } from '@/utils/useFormat'

const props = defineProps<{ mode: 'midwife' | 'admin' }>()
const { dateTime, mobile, fullName, errorText } = useFormat()
const { t } = useI18n()
const toasts = useToasts()
const busy = ref<string | null>(null)

const { data, loading, error, run } = useAsync(() =>
  props.mode === 'midwife' ? alertsApi.mine() : alertsApi.unassigned(),
)
onMounted(run)

async function markSeen(alert: Alert) {
  busy.value = alert.id
  try {
    await alertsApi.seen(alert.id)
    toasts.show(t('alerts.seenDone'))
    window.dispatchEvent(new Event('alerts-changed'))
    await run()
  } catch (e) {
    toasts.show(errorText(e), 'error')
  } finally {
    busy.value = null
  }
}
</script>

<template>
  <section class="flex flex-col gap-4">
    <header>
      <h1 class="text-2xl font-bold">{{ $t(mode === 'midwife' ? 'alerts.title' : 'alerts.unassignedTitle') }}</h1>
      <p class="text-base-content/70">{{ $t(mode === 'midwife' ? 'alerts.subtitle' : 'alerts.unassignedSubtitle') }}</p>
    </header>

    <AsyncState :loading="loading" :error="error" @retry="run">
      <div v-if="!data?.items.length" class="rounded-box bg-base-100 p-10 text-center text-base-content/60">
        {{ $t('alerts.empty') }}
      </div>
      <ul v-else class="flex flex-col gap-3">
        <li v-for="alert in data.items" :key="alert.id"
            class="card card-border border-error/40 bg-base-100 shadow-xs">
          <div class="card-body flex-row flex-wrap items-center gap-4 p-4">
            <span class="badge badge-error">{{ $t(`alerts.kind.${alert.kind}`) }}</span>
            <div class="min-w-48 flex-1">
              <div class="font-semibold">
                {{ fullName(alert.patient_first_name, alert.patient_last_name) || $t('patients.noName') }}
              </div>
              <div class="text-sm text-base-content/70">
                {{ $t('alerts.reportedAt') }}: {{ dateTime(alert.created_at) }}
              </div>
            </div>
            <a class="btn btn-sm btn-ghost ltr" :href="`tel:${alert.patient_mobile}`">
              {{ mobile(alert.patient_mobile) }}
            </a>
            <RouterLink v-if="mode === 'midwife'" class="btn btn-sm" :to="`/patients/${alert.patient_id}`">
              {{ $t('alerts.openRecord') }}
            </RouterLink>
            <button class="btn btn-sm btn-primary" :disabled="busy === alert.id" @click="markSeen(alert)">
              <span v-if="busy === alert.id" class="loading loading-spinner loading-xs" />{{ $t('alerts.markSeen') }}
            </button>
          </div>
        </li>
      </ul>
    </AsyncState>
  </section>
</template>
