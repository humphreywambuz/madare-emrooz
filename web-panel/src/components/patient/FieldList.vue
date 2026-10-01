<script setup lang="ts">
// A two-column label/value list.
defineProps<{ rows: { label: string; value: string }[] }>()
</script>

<template>
  <dl class="grid gap-x-6 gap-y-2 sm:grid-cols-2">
    <div v-for="row in rows" :key="row.label" class="flex justify-between gap-3 border-b border-base-200 py-1.5">
      <dt class="text-base-content/60">{{ row.label }}</dt>
      <!-- <bdi> keeps values like "A+" or a Latin note readable inside Persian text. -->
      <dd class="text-end font-medium"><bdi>{{ row.value }}</bdi></dd>
    </div>
  </dl>
</template>
