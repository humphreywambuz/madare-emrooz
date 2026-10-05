<script setup lang="ts">
// "Always make the next step clear": a tinted circle with an icon, a title, one line of help and
// room for a single action.
import AppIcon from '@/components/AppIcon.vue'
import type { IconName } from '@/components/icons'

withDefaults(defineProps<{ icon: IconName; title: string; text?: string; tone?: 'primary' | 'success' | 'warning' | 'error' | 'info' }>(), {
  tone: 'primary',
})

const TONES = {
  primary: 'bg-primary/10 text-primary',
  success: 'bg-success/10 text-success',
  warning: 'bg-warning/10 text-warning',
  error: 'bg-error/10 text-error',
  info: 'bg-info/10 text-info',
}
</script>

<template>
  <div class="flex flex-col items-center gap-3 px-6 py-12 text-center">
    <span class="grid size-16 place-items-center rounded-full" :class="TONES[tone]">
      <AppIcon :name="icon" class="size-7" />
    </span>
    <h3 class="text-base font-bold">{{ title }}</h3>
    <p v-if="text" class="max-w-sm text-sm leading-relaxed text-base-content/60">{{ text }}</p>
    <div v-if="$slots.default" class="mt-2"><slot /></div>
  </div>
</template>
