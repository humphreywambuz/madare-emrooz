<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppIcon from '@/components/AppIcon.vue'
import BrandMark from '@/components/BrandMark.vue'
import type { IconName } from '@/components/icons'
import UserAvatar from '@/components/UserAvatar.vue'
import { setLocale } from '@/i18n'
import { useAuth } from '@/stores/auth'
import { useFormat } from '@/utils/useFormat'
import { useOpenAlerts } from '@/utils/useOpenAlerts'
import { useTheme } from '@/utils/useTheme'

const auth = useAuth()
const route = useRoute()
const router = useRouter()
const { locale, num } = useFormat()
const { isDark, toggle: toggleTheme } = useTheme()
const { count: openAlerts } = useOpenAlerts()

type NavItem = { to: string; name: string; label: string; icon: IconName; badge?: boolean }

const groups = computed(() => {
  const care: NavItem[] = []
  const admin: NavItem[] = []
  if (auth.role === 'midwife') care.push({ to: '/alerts', name: 'alerts', label: 'nav.alerts', icon: 'siren', badge: true })
  if (auth.role === 'midwife' || auth.role === 'doctor') care.push({ to: '/patients', name: 'patients', label: 'nav.patients', icon: 'users' })
  if (auth.role === 'admin') {
    admin.push({ to: '/admin/unassigned', name: 'unassigned', label: 'nav.unassigned', icon: 'inbox', badge: true })
    admin.push({ to: '/admin/staff', name: 'staff', label: 'nav.staff', icon: 'stethoscope' })
  }
  return [
    { label: 'nav.groupCare', items: care },
    { label: 'nav.groupAdmin', items: admin },
  ].filter((g) => g.items.length)
})

const alertsTo = computed(() => (auth.role === 'admin' ? '/admin/unassigned' : '/alerts'))

// The page the breadcrumb names: the nav item whose route is open (a mother's record counts as "patients").
const current = computed(() => {
  const name = route.name === 'patient' ? 'patients' : route.name
  return groups.value.flatMap((g) => g.items).find((i) => i.name === name) ?? null
})

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
      <header class="navbar sticky top-0 z-30 min-h-16 gap-2 border-b border-base-300 bg-base-100 px-4 md:px-6">
        <div class="navbar-start gap-2">
          <label for="nav-drawer" class="btn btn-ghost btn-circle drawer-button lg:hidden" :aria-label="$t('app.panel')">
            <AppIcon name="menu" class="size-5" />
          </label>
          <nav class="breadcrumbs hidden p-0 text-sm sm:block" :aria-label="$t('app.panel')">
            <ul>
              <li class="text-base-content/60">{{ $t('app.panel') }}</li>
              <li v-if="current" class="font-semibold">{{ $t(current.label) }}</li>
            </ul>
          </nav>
          <span class="font-bold sm:hidden">{{ current ? $t(current.label) : $t('app.name') }}</span>
        </div>

        <div class="navbar-end gap-1">
          <button class="btn btn-ghost btn-sm border border-base-300 px-3" @click="toggleLanguage">
            <AppIcon name="globe" class="size-4" />{{ $t('app.language') }}
          </button>
          <button class="btn btn-ghost btn-circle btn-sm swap swap-rotate border border-base-300" :class="{ 'swap-active': isDark }"
                  :title="$t('app.theme')" :aria-label="$t('app.theme')" @click="toggleTheme">
            <AppIcon name="sun" class="swap-on size-4" />
            <AppIcon name="moon" class="swap-off size-4" />
          </button>
          <RouterLink v-if="auth.role !== 'doctor'" :to="alertsTo" class="btn btn-ghost btn-circle btn-sm indicator border border-base-300"
                      :aria-label="$t('nav.alerts')">
            <span v-if="openAlerts" class="indicator-item status status-error" />
            <AppIcon name="bell" class="size-4" />
          </RouterLink>
          <div class="dropdown dropdown-end">
            <button tabindex="0" class="btn btn-ghost btn-circle" :aria-label="auth.displayName">
              <UserAvatar :name="auth.displayName" size="sm" />
            </button>
            <ul tabindex="0" class="menu dropdown-content z-40 mt-2 w-56 rounded-box border border-base-300 bg-base-100 p-2 shadow-level-3">
              <li class="menu-title">{{ auth.displayName }} · {{ $t(`roles.${auth.role}`) }}</li>
              <li><button @click="signOut"><AppIcon name="logout" class="size-4" />{{ $t('app.signOut') }}</button></li>
            </ul>
          </div>
        </div>
      </header>

      <main class="w-full max-w-6xl flex-1 p-4 md:p-6 xl:p-8">
        <RouterView v-slot="{ Component }">
          <Transition name="page" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>

    <div class="drawer-side z-40">
      <label for="nav-drawer" aria-label="close sidebar" class="drawer-overlay" />
      <aside class="flex min-h-full w-72 flex-col border-e border-base-300 bg-base-100">
        <div class="flex items-center gap-3 px-5 pt-6 pb-4">
          <BrandMark />
          <div class="min-w-0">
            <div class="text-lg font-bold leading-tight">{{ $t('app.name') }}</div>
            <div class="truncate text-xs text-base-content/60">{{ $t('app.panel') }}</div>
          </div>
        </div>

        <nav class="flex-1 px-3">
          <template v-for="group in groups" :key="group.label">
            <p class="px-3 pt-4 pb-1 text-[11px] font-semibold text-base-content/50">{{ $t(group.label) }}</p>
            <ul class="menu w-full gap-0.5 p-0 [--menu-active-bg:color-mix(in_oklab,var(--color-primary)_12%,transparent)] [--menu-active-fg:var(--color-primary)]">
              <li v-for="item in group.items" :key="item.to">
                <RouterLink :to="item.to" active-class="menu-active font-semibold" class="rounded-field py-2.5">
                  <AppIcon :name="item.icon" class="size-5" />
                  <span class="flex-1">{{ $t(item.label) }}</span>
                  <span v-if="item.badge && openAlerts" class="badge badge-error badge-sm">{{ num(openAlerts) }}</span>
                </RouterLink>
              </li>
            </ul>
          </template>
        </nav>

        <div class="m-3 flex items-center gap-3 rounded-box border border-base-300 bg-base-200 p-3">
          <UserAvatar :name="auth.displayName" size="sm" />
          <div class="min-w-0 flex-1">
            <div class="truncate text-sm font-semibold">{{ auth.displayName }}</div>
            <div class="text-xs text-base-content/60">{{ $t(`roles.${auth.role}`) }}</div>
          </div>
          <button class="btn btn-ghost btn-circle btn-sm" :aria-label="$t('app.signOut')" :title="$t('app.signOut')" @click="signOut">
            <AppIcon name="logout" class="size-4" />
          </button>
        </div>
      </aside>
    </div>
  </div>
</template>
