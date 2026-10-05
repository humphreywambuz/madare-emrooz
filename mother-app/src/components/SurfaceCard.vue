<script setup lang="ts">
// The system's card: a white surface on the canvas with a hairline outline and a level-1 shadow.
defineProps<{ as?: string }>()
</script>

<template>
  <component :is="as ?? 'section'" class="card card-border border-base-300 bg-base-100 shadow-level-1">
    <slot />
  </component>
</template>
