<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { alerts } from '@/api/endpoints'
import { setLocale } from '@/i18n'
import { useAuth } from '@/stores/auth'
import { load, store } from '@/utils/storage'
import { useFormat } from '@/utils/useFormat'

const auth = useAuth()
const router = useRouter()
const { locale, num } = useFormat()

const openAlerts = ref(0)
let timer: ReturnType<typeof setInterval> | undefined

const nav = computed(() => {
  const items: { to: string; label: string; badge?: boolean }[] = []
  if (auth.role === 'midwife') items.push({ to: '/alerts', label: 'nav.alerts', badge: true })
  if (auth.role === 'midwife' || auth.role === 'doctor') items.push({ to: '/patients', label: 'nav.patients' })
  if (auth.role === 'admin') {
    items.push({ to: '/admin/unassigned', label: 'nav.unassigned', badge: true })
    items.push({ to: '/admin/staff', label: 'nav.staff' })
  }
  return items
})

// Red alerts matter most: keep their count fresh in the menu.
async function refreshAlertCount() {
  if (auth.role !== 'midwife' && auth.role !== 'admin') return
  try {
    const result = auth.role === 'midwife' ? await alerts.mine() : await alerts.unassigned()
    openAlerts.value = result.items.length
  } catch {
    /* the page itself shows errors */
  }
}

onMounted(() => {
  refreshAlertCount()
  timer = setInterval(refreshAlertCount, 60_000)
  window.addEventListener('alerts-changed', refreshAlertCount)
})
onUnmounted(() => {
  clearInterval(timer)
  window.removeEventListener('alerts-changed', refreshAlertCount)
})

const THEME_KEY = 'madare.theme'
const theme = ref<string | null>(load(THEME_KEY))
if (theme.value) document.documentElement.dataset.theme = theme.value

function toggleTheme() {
  const dark = (theme.value ?? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')) === 'dark'
  theme.value = dark ? 'light' : 'dark'
  document.documentElement.dataset.theme = theme.value
  store(THEME_KEY, theme.value)
}

function toggleLanguage() {
  setLocale(locale.value === 'fa' ? 'en' : 'fa')
}

async function signOut() {
  await auth.signOut()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="drawer lg:drawer-open">
    <input id="nav-drawer" type="checkbox" class="drawer-toggle" />
    <div class="drawer-content flex min-h-screen flex-col bg-base-200">
      <header class="navbar sticky top-0 z-30 gap-2 border-b border-base-300 bg-base-100 px-4">
        <label for="nav-drawer" class="btn btn-square btn-ghost lg:hidden" :aria-label="$t('app.panel')">
          <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </label>
        <div class="flex-1 truncate whitespace-nowrap font-semibold lg:hidden">{{ $t('app.name') }}</div>
        <div class="hidden flex-1 lg:block" />
        <button class="btn btn-ghost btn-sm" @click="toggleLanguage">{{ $t('app.language') }}</button>
        <button class="btn btn-ghost btn-sm btn-square" :title="$t('app.theme')" :aria-label="$t('app.theme')" @click="toggleTheme">
          <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 3a9 9 0 1 0 9 9 7 7 0 0 1-9-9z" />
          </svg>
        </button>
        <div class="dropdown dropdown-end">
          <button tabindex="0" class="btn btn-ghost btn-sm">
            <span class="max-w-40 truncate">{{ auth.displayName }}</span>
            <span class="badge badge-sm badge-primary badge-soft">{{ $t(`roles.${auth.role}`) }}</span>
          </button>
          <ul tabindex="0" class="menu dropdown-content z-40 mt-2 w-44 rounded-box bg-base-100 p-2 shadow">
            <li><button @click="signOut">{{ $t('app.signOut') }}</button></li>
          </ul>
        </div>
      </header>
      <main class="mx-auto w-full max-w-6xl flex-1 p-4 md:p-6">
        <RouterView />
      </main>
    </div>
    <div class="drawer-side z-40">
      <label for="nav-drawer" aria-label="close" class="drawer-overlay" />
      <aside class="flex min-h-full w-64 flex-col border-e border-base-300 bg-base-100">
        <div class="px-5 py-5">
          <div class="text-lg font-bold text-primary">{{ $t('app.name') }}</div>
          <div class="text-sm text-base-content/60">{{ $t('app.panel') }}</div>
        </div>
        <ul class="menu w-full gap-1 px-3">
          <li v-for="item in nav" :key="item.to">
            <RouterLink :to="item.to" active-class="menu-active">
              <span class="flex-1">{{ $t(item.label) }}</span>
              <span v-if="item.badge && openAlerts" class="badge badge-error badge-sm">{{ num(openAlerts) }}</span>
            </RouterLink>
          </li>
        </ul>
      </aside>
    </div>
  </div>
</template>
