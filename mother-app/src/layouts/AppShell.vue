<script setup lang="ts">
import AppIcon from '@/components/AppIcon.vue'
import type { IconName } from '@/components/icons'

const tabs: { to: string; label: string; icon: IconName }[] = [
  { to: '/', label: 'nav.home', icon: 'home' },
  { to: '/midwife', label: 'nav.midwife', icon: 'stethoscope' },
  { to: '/documents', label: 'nav.documents', icon: 'file' },
  { to: '/me', label: 'nav.me', icon: 'user' },
]
</script>

<template>
  <div class="mx-auto min-h-screen w-full max-w-md pb-24">
    <RouterView v-slot="{ Component }">
      <Transition name="page" mode="out-in">
        <component :is="Component" />
      </Transition>
    </RouterView>

    <!-- The system's bottom navigation: a white bar with a hairline top edge; the open tab turns green. -->
    <nav class="dock mx-auto max-w-md border-t border-base-300 bg-base-100">
      <RouterLink v-for="tab in tabs" :key="tab.to" :to="tab.to" exact-active-class="dock-active text-primary"
                  class="transition-transform active:scale-90">
        <AppIcon :name="tab.icon" class="size-5" />
        <span class="dock-label">{{ $t(tab.label) }}</span>
      </RouterLink>
    </nav>
  </div>
</template>
