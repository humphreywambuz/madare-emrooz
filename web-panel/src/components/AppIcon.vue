<script setup lang="ts">
import { type IconName, PATHS } from './icons'

defineProps<{ name: IconName }>()
</script>

<template>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"
       stroke-linejoin="round" aria-hidden="true" class="shrink-0">
    <path :d="PATHS[name]" />
  </svg>
</template>
