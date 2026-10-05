<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { patients } from '@/api/endpoints'
import AppIcon from '@/components/AppIcon.vue'
import AsyncState from '@/components/AsyncState.vue'
import EmptyState from '@/components/EmptyState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import SectionCard from '@/components/SectionCard.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { useAuth } from '@/stores/auth'
import { useAsync } from '@/utils/useAsync'
import { useFormat } from '@/utils/useFormat'

const PER_PAGE = 20
const route = useRoute()
const router = useRouter()
const auth = useAuth()
const { mobile, fullName, enumLabel, num, dateTime } = useFormat()

// Search text and page live in the URL, so the back button and shared links keep them.
const query = ref(typeof route.query.q === 'string' ? route.query.q : '')
const page = ref(Number(route.query.page) || 1)

const { data, loading, error, run } = useAsync(() =>
  patients.list({ q: query.value.trim(), page: page.value, per_page: PER_PAGE }),
)
onMounted(run)

const PATH_TONE: Record<string, string> = {
  pregnancy: 'badge-primary', fitness: 'badge-info', rehabilitation: 'badge-secondary',
}

let debounce: ReturnType<typeof setTimeout> | undefined
watch(query, () => {
  clearTimeout(debounce)
  debounce = setTimeout(() => go(1), 300)
})

function go(p: number) {
  page.value = p
  router.replace({ query: { ...(query.value ? { q: query.value } : {}), ...(p > 1 ? { page: p } : {}) } })
  run()
}
</script>

<template>
  <section class="flex flex-col gap-6">
    <PageHeader :title="$t('patients.title')"
                :subtitle="$t(auth.role === 'midwife' ? 'patients.subtitleMidwife' : 'patients.subtitleDoctor')">
      <label class="input w-full rounded-full sm:w-80">
        <AppIcon name="search" class="size-4 opacity-50" />
        <input v-model="query" type="search" class="grow" :placeholder="$t('patients.search')" :aria-label="$t('patients.search')" />
      </label>
    </PageHeader>

    <AsyncState :loading="loading" :error="error" @retry="run">
      <SectionCard v-if="!data?.items.length" flush>
        <EmptyState :icon="query ? 'search' : 'users'" :title="query ? $t('ui.noResultsTitle') : $t('patients.title')"
                    :text="query ? $t('ui.noResults') : $t('patients.empty')" />
      </SectionCard>
      <template v-else>
        <SectionCard flush>
          <div class="overflow-x-auto">
            <table class="table">
              <thead>
                <tr class="text-xs text-base-content/60">
                  <th>{{ $t('patients.name') }}</th>
                  <th>{{ $t('patients.mobile') }}</th>
                  <th>{{ $t('patients.path') }}</th>
                  <th>{{ $t('patients.openAlerts') }}</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in data.items" :key="p.id" class="cursor-pointer hover:bg-base-200"
                    @click="router.push(`/patients/${p.id}`)">
                  <td>
                    <RouterLink :to="`/patients/${p.id}`" class="flex items-center gap-3" @click.stop>
                      <UserAvatar :name="fullName(p.first_name, p.last_name) || '?'" />
                      <span class="font-semibold">{{ fullName(p.first_name, p.last_name) || $t('patients.noName') }}</span>
                    </RouterLink>
                  </td>
                  <td class="ltr text-start whitespace-nowrap">{{ mobile(p.mobile) }}</td>
                  <td>
                    <span class="badge badge-soft" :class="PATH_TONE[p.join_goal ?? ''] ?? 'badge-ghost'">
                      {{ enumLabel('join_goal', p.join_goal) }}
                    </span>
                    <span v-if="p.reproductive_status" class="ms-2 text-sm text-base-content/60">
                      {{ enumLabel('reproductive_status', p.reproductive_status) }}
                    </span>
                  </td>
                  <td>
                    <span v-if="p.open_alerts" class="badge badge-error tooltip" :data-tip="dateTime(p.last_alert_at)">
                      {{ num(p.open_alerts) }}
                    </span>
                    <span v-else class="text-sm text-base-content/40">—</span>
                  </td>
                  <td class="text-end"><AppIcon name="chevron" class="inline size-4 text-base-content/40 rtl:rotate-180" /></td>
                </tr>
              </tbody>
            </table>
          </div>
        </SectionCard>
        <PaginationBar :page="data.page" :per-page="data.per_page" :total="data.total" @go="go" />
      </template>
    </AsyncState>
  </section>
</template>
