// Everything the pregnancy home shows: the pregnancy, her midwife, her logs, and the bleeding report.
import { computed, onMounted, ref, shallowRef } from 'vue'

import { logs as logsApi, midwives as midwivesApi, pregnancy as pregnancyApi } from '@/api/endpoints'
import type { DailyLog, Midwife, Pregnancy } from '@/api/types'

import { useAction } from './useAction'
import { useAsync } from './useAsync'

const DAY_MS = 24 * 60 * 60 * 1000

export function usePregnancyHome() {
  const { data, loading, error, run } = useAsync(async () => {
    const [pregnancy, mine, logs] = await Promise.all([pregnancyApi.current(), midwivesApi.mine(), logsApi.mine()])
    return { pregnancy, midwife: mine.midwife, logs: logs.items }
  })
  onMounted(run)

  const pregnancy = computed<Pregnancy | null>(() => data.value?.pregnancy ?? null)
  const midwife = computed<Midwife | null>(() => data.value?.midwife ?? null)
  const logs = computed<DailyLog[]>(() => data.value?.logs ?? [])

  const daysLeft = computed(() => {
    if (!pregnancy.value) return null
    const due = new Date(`${pregnancy.value.estimated_due_date}T12:00:00`).getTime()
    return Math.max(0, Math.round((due - Date.now()) / DAY_MS))
  })

  /** The latest of each vital sign her midwife recorded. */
  const vitals = computed(() => {
    const newest = [...logs.value].sort((a, b) => b.recorded_at.localeCompare(a.recorded_at))
    const bp = newest.find((log) => log.systolic_bp !== null)
    return {
      bp: bp ? { systolic: bp.systolic_bp!, diastolic: bp.diastolic_bp! } : null,
      glucose: newest.find((log) => log.blood_glucose_mg_dl !== null)?.blood_glucose_mg_dl ?? null,
      weight: newest.find((log) => log.weight_kg !== null)?.weight_kg ?? null,
    }
  })

  // --- the bleeding report -----------------------------------------------------------
  const { busy, act } = useAction()
  const confirming = ref(false)
  const lastReport = shallowRef<DailyLog | null>(null)
  const askingAgain = ref(false)
  /** Her latest own answer in the past day, so the question isn't asked again straight away. */
  const recentReport = computed(() => {
    if (askingAgain.value) return null
    if (lastReport.value) return lastReport.value
    const cutoff = Date.now() - DAY_MS
    return [...logs.value]
      .filter((log) => log.has_spotting_or_bleeding !== null && new Date(log.recorded_at).getTime() > cutoff)
      .sort((a, b) => b.recorded_at.localeCompare(a.recorded_at))[0] ?? null
  })

  async function report(bleeding: boolean) {
    const ok = await act(async () => {
      lastReport.value = await logsApi.report(bleeding)
      askingAgain.value = false
    })
    if (ok) confirming.value = false
  }

  function askAgain() {
    askingAgain.value = true
  }

  return { loading, error, run, pregnancy, midwife, daysLeft, vitals, busy, confirming, recentReport, report, askAgain }
}
