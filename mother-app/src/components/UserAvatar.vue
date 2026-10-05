<script setup lang="ts">
// Initials on a soft tint from the system palette, picked from the name so each person keeps theirs.
import { computed } from 'vue'

const props = withDefaults(defineProps<{ name: string; size?: 'sm' | 'md' | 'lg' }>(), { size: 'md' })

const TINTS = [
  'bg-primary/15 text-primary', 'bg-secondary/25 text-secondary-content', 'bg-accent/50 text-accent-content',
  'bg-info/15 text-info', 'bg-error/15 text-error',
]
const SIZES = { sm: 'w-8 text-xs', md: 'w-10 text-sm', lg: 'w-16 text-xl' }

const initials = computed(() =>
  props.name.trim().split(/\s+/).slice(0, 2).map((part) => part[0] ?? '').join('‌') || '؟',
)
const tint = computed(() => {
  let hash = 0
  for (const ch of props.name) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0
  return TINTS[hash % TINTS.length]
})
</script>

<template>
  <div class="avatar avatar-placeholder" aria-hidden="true">
    <div class="rounded-full font-bold" :class="[tint, SIZES[size]]">
      <span>{{ initials }}</span>
    </div>
  </div>
</template>
