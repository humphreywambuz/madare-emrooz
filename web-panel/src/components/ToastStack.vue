<script setup lang="ts">
import { useToasts } from '@/stores/toast'

const toasts = useToasts()
const style = { success: 'alert-success', error: 'alert-error', info: 'alert-info' } as const
</script>

<template>
  <div class="toast toast-end toast-bottom z-50" aria-live="polite">
    <div
      v-for="t in toasts.items"
      :key="t.id"
      class="alert shadow-md"
      :class="style[t.kind]"
      role="status"
      @click="toasts.dismiss(t.id)"
    >
      <span>{{ t.text }}</span>
    </div>
  </div>
</template>
