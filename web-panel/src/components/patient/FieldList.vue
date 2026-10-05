<script setup lang="ts">
// A two-column label/value list.
defineProps<{ rows: { label: string; value: string }[] }>()
</script>

<template>
  <dl class="grid gap-x-8 sm:grid-cols-2">
    <div v-for="row in rows" :key="row.label" class="flex items-baseline justify-between gap-4 border-b border-base-300 py-2.5 last:border-0 sm:nth-last-[2]:border-0">
      <dt class="text-sm text-base-content/60">{{ row.label }}</dt>
      <!-- <bdi> keeps values like "A+" or a Latin note readable inside Persian text. -->
      <dd class="text-end text-sm font-semibold"><bdi>{{ row.value }}</bdi></dd>
    </div>
  </dl>
</template>
