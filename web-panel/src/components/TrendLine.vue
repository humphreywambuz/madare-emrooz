<script setup lang="ts">
// A single-series sparkline with a hover read-out. Points are oldest → newest; gaps are skipped.
import { computed, ref } from 'vue'

const props = defineProps<{
  points: { value: number; label: string }[]
  format: (n: number) => string
  name: string
}>()

const W = 240
const H = 64
const PAD = 8

const geometry = computed(() => {
  const values = props.points.map((p) => p.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const span = max - min || 1
  const step = props.points.length > 1 ? (W - PAD * 2) / (props.points.length - 1) : 0
  return props.points.map((p, i) => ({
    x: props.points.length > 1 ? PAD + i * step : W / 2,
    y: PAD + (1 - (p.value - min) / span) * (H - PAD * 2),
  }))
})

const line = computed(() => geometry.value.map((g, i) => `${i ? 'L' : 'M'}${g.x.toFixed(1)},${g.y.toFixed(1)}`).join(' '))
const area = computed(() => {
  const g = geometry.value
  if (!g.length) return ''
  return `${line.value} L${g[g.length - 1].x.toFixed(1)},${H} L${g[0].x.toFixed(1)},${H} Z`
})

const hover = ref<number | null>(null)
const active = computed(() => hover.value ?? geometry.value.length - 1)

function onMove(event: PointerEvent) {
  const box = (event.currentTarget as SVGElement).getBoundingClientRect()
  const x = ((event.clientX - box.left) / box.width) * W
  let best = 0
  geometry.value.forEach((g, i) => {
    if (Math.abs(g.x - x) < Math.abs(geometry.value[best].x - x)) best = i
  })
  hover.value = best
}

const gradientId = `trend-${Math.random().toString(36).slice(2, 8)}`
</script>

<template>
  <figure class="relative" dir="ltr">
    <svg :viewBox="`0 0 ${W} ${H}`" class="h-16 w-full overflow-visible" role="img" :aria-label="name"
         @pointermove="onMove" @pointerleave="hover = null">
      <defs>
        <linearGradient :id="gradientId" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stop-color="var(--color-primary)" stop-opacity="0.28" />
          <stop offset="100%" stop-color="var(--color-primary)" stop-opacity="0" />
        </linearGradient>
      </defs>
      <path :d="area" :fill="`url(#${gradientId})`" />
      <path :d="line" fill="none" stroke="var(--color-primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
            vector-effect="non-scaling-stroke" />
      <line v-if="hover !== null" :x1="geometry[active].x" :x2="geometry[active].x" y1="0" :y2="H"
            stroke="var(--color-base-content)" stroke-opacity="0.2" stroke-dasharray="2 3" vector-effect="non-scaling-stroke" />
      <circle :cx="geometry[active].x" :cy="geometry[active].y" r="4.5" fill="var(--color-primary)"
              stroke="var(--color-base-100)" stroke-width="2" vector-effect="non-scaling-stroke" />
      <!-- A wide invisible hit area so hovering doesn't need precision. -->
      <rect x="0" y="0" :width="W" :height="H" fill="transparent" />
    </svg>
    <figcaption v-if="hover !== null"
                class="badge badge-neutral border-0 pointer-events-none absolute -top-8 whitespace-nowrap"
                :style="{ left: `${(geometry[active].x / W) * 100}%`, transform: 'translateX(-50%)' }">
      <b>{{ format(points[active].value) }}</b> · {{ points[active].label }}
    </figcaption>
  </figure>
</template>
