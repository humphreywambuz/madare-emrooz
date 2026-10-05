// A number that counts up to its value when it first appears, and jumps when it changes later.
import { type MaybeRefOrGetter, onMounted, ref, toValue, watch } from 'vue'

const DURATION_MS = 1400
const reducedMotion = () => matchMedia('(prefers-reduced-motion: reduce)').matches

export function useCountUp(target: MaybeRefOrGetter<number | null | undefined>) {
  const shown = ref(0)
  let frame = 0

  function animate(to: number) {
    cancelAnimationFrame(frame)
    if (reducedMotion()) {
      shown.value = to
      return
    }
    const start = performance.now()
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / DURATION_MS)
      shown.value = Math.round(to * (1 - Math.pow(1 - t, 3)))
      if (t < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
  }

  onMounted(() => animate(toValue(target) ?? 0))
  watch(() => toValue(target), (to) => animate(to ?? 0))

  return shown
}
