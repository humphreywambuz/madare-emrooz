<script setup lang="ts">
// The system's card: a white surface on the canvas with a hairline outline and a level-1 shadow.
// The header carries a title, an optional subtitle and whatever actions belong to the section.
defineProps<{ title?: string; subtitle?: string; flush?: boolean }>()
</script>

<template>
  <section class="card card-border border-base-300 bg-base-100 shadow-level-1">
    <header v-if="title || $slots.actions" class="flex flex-wrap items-start justify-between gap-3 px-5 pt-5"
            :class="{ 'pb-4': flush }">
      <div class="min-w-0">
        <h2 v-if="title" class="text-base font-bold">{{ title }}</h2>
        <p v-if="subtitle" class="mt-0.5 text-xs text-base-content/60">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="flex flex-wrap items-center gap-2"><slot name="actions" /></div>
    </header>
    <div :class="flush ? '' : 'card-body gap-4 p-5'"><slot /></div>
  </section>
</template>
