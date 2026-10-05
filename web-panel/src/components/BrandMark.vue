<script setup lang="ts">
// The Madare Emrooz mark as the design system draws it: a heart on a filled green tile.
withDefaults(defineProps<{ size?: 'md' | 'lg' }>(), { size: 'md' })
</script>

<template>
  <span class="grid shrink-0 place-items-center rounded-xl bg-primary text-primary-content shadow-level-1"
        :class="size === 'lg' ? 'size-14 rounded-2xl' : 'size-10'" aria-hidden="true">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
         :class="size === 'lg' ? 'size-7' : 'size-5'">
      <path d="M12 20.5 4.6 13.3a4.6 4.6 0 0 1 6.5-6.5l.9.9.9-.9a4.6 4.6 0 0 1 6.5 6.5z" />
    </svg>
  </span>
</template>
