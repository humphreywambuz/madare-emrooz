<script setup lang="ts">
// A midwife's red alerts, or (mode "admin") alerts from mothers who have no midwife yet.
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { alerts as alertsApi } from '@/api/endpoints'
import type { Alert } from '@/api/types'
import AppIcon from '@/components/AppIcon.vue'
import AsyncState from '@/components/AsyncState.vue'
import EmptyState from '@/components/EmptyState.vue'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import { useToasts } from '@/stores/toast'
import { useAsync } from '@/utils/useAsync'
import { useFormat } from '@/utils/useFormat'

const props = defineProps<{ mode: 'midwife' | 'admin' }>()
const { dateTime, timeAgo, mobile, fullName, errorText, num } = useFormat()
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
  <section class="flex flex-col gap-6">
    <PageHeader :title="$t(mode === 'midwife' ? 'alerts.title' : 'alerts.unassignedTitle')"
                :subtitle="$t(mode === 'midwife' ? 'alerts.subtitle' : 'alerts.unassignedSubtitle')" />

    <AsyncState :loading="loading" :error="error" @retry="run">
      <SectionCard v-if="!data?.items.length" flush>
        <EmptyState icon="checkCircle" tone="success" :title="$t('ui.allClear')" :text="$t('ui.allClearText')" />
      </SectionCard>

      <SectionCard v-else flush :title="$t('ui.alertsWaiting', { n: num(data.items.length) })">
        <ul class="list">
          <li v-for="(alert, i) in data.items" :key="alert.id"
              class="list-row animate-rise items-center motion-reduce:animate-none" :style="{ animationDelay: `${Math.min(i, 8) * 60}ms` }">
            <span class="grid size-11 place-items-center rounded-full bg-error/10 text-error">
              <AppIcon name="droplet" class="size-5" />
            </span>
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <span class="font-bold">
                  {{ fullName(alert.patient_first_name, alert.patient_last_name) || $t('patients.noName') }}
                </span>
                <span class="badge badge-error badge-soft badge-sm">{{ $t(`alerts.kind.${alert.kind}`) }}</span>
              </div>
              <div class="mt-0.5 text-sm text-base-content/60">
                <span class="font-semibold text-base-content">{{ timeAgo(alert.created_at) }}</span>،
                {{ dateTime(alert.created_at) }}
              </div>
            </div>
            <div class="max-md:list-col-wrap flex flex-wrap items-center gap-2">
              <a class="btn btn-sm btn-outline ltr" :href="`tel:${alert.patient_mobile}`">
                <AppIcon name="phone" class="size-4" />{{ mobile(alert.patient_mobile) }}
              </a>
              <RouterLink v-if="mode === 'midwife'" class="btn btn-sm btn-soft btn-primary" :to="`/patients/${alert.patient_id}`">
                {{ $t('alerts.openRecord') }}
              </RouterLink>
              <button class="btn btn-sm btn-primary" :disabled="busy === alert.id" @click="markSeen(alert)">
                <span v-if="busy === alert.id" class="loading loading-spinner loading-xs" />
                <AppIcon v-else name="check" class="size-4" />{{ $t('alerts.markSeen') }}
              </button>
            </div>
          </li>
        </ul>
      </SectionCard>
    </AsyncState>
  </section>
</template>
