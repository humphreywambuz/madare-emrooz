<script setup lang="ts">
// A thick progress ring in the design system's "pregnancy progress" pattern: a soft track, a
// brand-green arc that fills once when it appears, and whatever belongs in the centre.
import { computed } from 'vue'

const props = withDefaults(defineProps<{ fraction: number; size?: number; thickness?: number; label?: string }>(), {
  size: 160,
  thickness: 14,
})

const R = 50
const LENGTH = 2 * Math.PI * R
const clamped = computed(() => Math.min(1, Math.max(0, props.fraction)))
const offset = computed(() => LENGTH * (1 - clamped.value))
const stroke = computed(() => (props.thickness / props.size) * 120)
</script>

<template>
  <figure class="relative grid shrink-0 place-items-center" :style="{ width: `${size}px`, height: `${size}px` }"
          :role="label ? 'img' : 'presentation'" :aria-label="label">
    <svg viewBox="0 0 120 120" class="absolute inset-0 size-full -rotate-90" aria-hidden="true">
      <circle cx="60" cy="60" :r="R" fill="none" :stroke-width="stroke" class="stroke-primary/15" />
      <circle cx="60" cy="60" :r="R" fill="none" :stroke-width="stroke" stroke-linecap="round"
              class="animate-ring stroke-primary motion-reduce:animate-none"
              :stroke-dasharray="LENGTH" :stroke-dashoffset="offset"
              :style="{ '--ring-length': LENGTH, '--ring-offset': offset }" />
    </svg>
    <figcaption class="relative flex flex-col items-center text-center leading-none">
      <slot />
    </figcaption>
  </figure>
</template>
