<script setup lang="ts">
defineProps<{ title: string; subtitle?: string; eyebrow?: string }>()
</script>

<template>
  <header class="flex flex-wrap items-end justify-between gap-4">
    <div class="min-w-0">
      <p v-if="eyebrow" class="mb-1 text-xs font-semibold text-primary">{{ eyebrow }}</p>
      <h1 class="font-display text-3xl leading-tight text-balance md:text-4xl">{{ title }}</h1>
      <p v-if="subtitle" class="mt-2 max-w-2xl leading-relaxed text-base-content/60">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.default" class="flex flex-wrap items-center gap-2"><slot /></div>
  </header>
</template>
