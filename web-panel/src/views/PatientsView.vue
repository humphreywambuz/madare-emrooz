<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { patients } from '@/api/endpoints'
import AsyncState from '@/components/AsyncState.vue'
import PaginationBar from '@/components/PaginationBar.vue'
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
  <section class="flex flex-col gap-4">
    <header>
      <h1 class="text-2xl font-bold">{{ $t('patients.title') }}</h1>
      <p class="text-base-content/70">
        {{ $t(auth.role === 'midwife' ? 'patients.subtitleMidwife' : 'patients.subtitleDoctor') }}
      </p>
    </header>

    <label class="input w-full max-w-md">
      <svg viewBox="0 0 24 24" class="size-4 opacity-60" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
      </svg>
      <input v-model="query" type="search" :placeholder="$t('patients.search')" :aria-label="$t('patients.search')" />
    </label>

    <AsyncState :loading="loading" :error="error" @retry="run">
      <div v-if="!data?.items.length" class="rounded-box bg-base-100 p-10 text-center text-base-content/60">
        {{ $t('patients.empty') }}
      </div>
      <template v-else>
        <div class="overflow-x-auto rounded-box border border-base-300 bg-base-100">
          <table class="table">
            <thead>
              <tr>
                <th>{{ $t('patients.name') }}</th>
                <th>{{ $t('patients.mobile') }}</th>
                <th>{{ $t('patients.path') }}</th>
                <th>{{ $t('patients.openAlerts') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in data.items" :key="p.id" class="hover:bg-base-200 cursor-pointer"
                  @click="router.push(`/patients/${p.id}`)">
                <td>
                  <RouterLink :to="`/patients/${p.id}`" class="font-medium link-hover" @click.stop>
                    {{ fullName(p.first_name, p.last_name) || $t('patients.noName') }}
                  </RouterLink>
                </td>
                <td class="ltr whitespace-nowrap text-start">{{ mobile(p.mobile) }}</td>
                <td>
                  {{ enumLabel('join_goal', p.join_goal) }}
                  <span v-if="p.reproductive_status" class="text-base-content/60">
                    · {{ enumLabel('reproductive_status', p.reproductive_status) }}
                  </span>
                </td>
                <td>
                  <span v-if="p.open_alerts" class="badge badge-error gap-1" :title="dateTime(p.last_alert_at)">
                    {{ num(p.open_alerts) }}
                  </span>
                  <span v-else class="text-base-content/40">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <PaginationBar :page="data.page" :per-page="data.per_page" :total="data.total" @go="go" />
      </template>
    </AsyncState>
  </section>
</template>
