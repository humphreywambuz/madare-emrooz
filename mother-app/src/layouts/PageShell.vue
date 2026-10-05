<script setup lang="ts">
// An inner page: a back button and the page title above its content.
import { useRoute, useRouter } from 'vue-router'

import AppIcon from '@/components/AppIcon.vue'

const route = useRoute()
const router = useRouter()

function back() {
  if (window.history.length > 1) router.back()
  else router.replace({ name: 'home' })
}
</script>

<template>
  <div class="mx-auto min-h-screen w-full max-w-md">
    <header class="navbar sticky top-0 z-30 min-h-14 gap-2 border-b border-base-300 bg-base-100 px-2">
      <button class="btn btn-ghost btn-circle" :aria-label="$t('app.back')" @click="back">
        <AppIcon name="arrowBack" class="size-5 rtl:rotate-180" />
      </button>
      <h1 class="text-lg font-bold">{{ route.meta.title ? $t(route.meta.title) : '' }}</h1>
    </header>
    <main class="p-4 pb-12">
      <RouterView v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>
  </div>
</template>
