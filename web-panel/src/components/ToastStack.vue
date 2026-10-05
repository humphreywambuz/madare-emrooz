<script setup lang="ts">
// Snackbars in the design system's style: a dark green band with the icon in a coloured circle.
import AppIcon from '@/components/AppIcon.vue'
import { useToasts } from '@/stores/toast'

const toasts = useToasts()
const look = {
  success: { icon: 'check', tone: 'bg-primary text-primary-content' },
  error: { icon: 'x', tone: 'bg-error text-error-content' },
  info: { icon: 'bell', tone: 'bg-info text-info-content' },
} as const
</script>

<template>
  <div class="toast toast-center toast-bottom z-50 sm:toast-end" aria-live="polite">
    <div v-for="t in toasts.items" :key="t.id" role="status"
         class="alert animate-rise cursor-pointer border-0 bg-neutral text-neutral-content shadow-level-3 motion-reduce:animate-none"
         @click="toasts.dismiss(t.id)">
      <span class="grid size-7 place-items-center rounded-full" :class="look[t.kind].tone">
        <AppIcon :name="look[t.kind].icon" class="size-4" />
      </span>
      <span class="text-sm font-semibold">{{ t.text }}</span>
    </div>
  </div>
</template>
