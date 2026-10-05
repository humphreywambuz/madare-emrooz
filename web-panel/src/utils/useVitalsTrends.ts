// The latest readings of each vital sign from a mother's daily logs, for the trend charts.
import { computed, type MaybeRefOrGetter, toValue } from 'vue'

import type { DailyLog } from '@/api/types'

import { useFormat } from './useFormat'

const MAX_POINTS = 12

/** Blood pressure at or above 140/90 needs attention in pregnancy. */
export const isHighBp = (log: Pick<DailyLog, 'systolic_bp' | 'diastolic_bp'>) =>
  (log.systolic_bp ?? 0) >= 140 || (log.diastolic_bp ?? 0) >= 90

export function useVitalsTrends(logs: MaybeRefOrGetter<DailyLog[]>) {
  const { num, dateTime } = useFormat()

  const chronological = computed(() =>
    [...toValue(logs)].sort((a, b) => a.recorded_at.localeCompare(b.recorded_at)),
  )

  function series(pick: (log: DailyLog) => number | null) {
    return chronological.value
      .filter((log) => pick(log) !== null)
      .slice(-MAX_POINTS)
      .map((log) => ({ value: Number(pick(log)), label: dateTime(log.recorded_at) }))
  }

  const trends = computed(() => {
    const lastBp = [...chronological.value].reverse().find((log) => log.systolic_bp !== null)
    const glucose = series((log) => log.blood_glucose_mg_dl)
    const weight = series((log) => log.weight_kg)
    const last = (points: { value: number }[]) => (points.length ? num(points[points.length - 1].value) : null)
    return [
      {
        key: 'bp', title: 'logs.bp', points: series((log) => log.systolic_bp),
        latest: lastBp ? `${num(lastBp.systolic_bp)}/${num(lastBp.diastolic_bp)}` : null,
        high: lastBp ? isHighBp(lastBp) : false,
      },
      { key: 'glucose', title: 'logs.blood_glucose_mg_dl', points: glucose, latest: last(glucose), high: false },
      { key: 'weight', title: 'logs.weight_kg', points: weight, latest: last(weight), high: false },
    ]
  })

  return { trends }
}
