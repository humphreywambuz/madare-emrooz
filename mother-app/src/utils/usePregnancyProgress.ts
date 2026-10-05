// Where a pregnancy stands on the 40-week scale: the trimester and the weeks still to go.
import { computed, type MaybeRefOrGetter, toValue } from 'vue'

export const TOTAL_WEEKS = 40
/** First week of each trimester, counted from 0. */
export const TRIMESTER_STARTS = [0, 13, 27] as const

export function trimesterOf(week: number): 1 | 2 | 3 {
  return week < TRIMESTER_STARTS[1] ? 1 : week < TRIMESTER_STARTS[2] ? 2 : 3
}

export function usePregnancyProgress(week: MaybeRefOrGetter<number | null | undefined>) {
  const current = computed(() => {
    const value = toValue(week)
    return value === null || value === undefined ? null : Math.min(TOTAL_WEEKS, Math.max(0, value))
  })
  const trimester = computed(() => (current.value === null ? null : trimesterOf(current.value)))
  const weeksLeft = computed(() => (current.value === null ? null : TOTAL_WEEKS - current.value))
  return { week: current, trimester, weeksLeft }
}
