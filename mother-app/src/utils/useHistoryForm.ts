// The medical and midwifery history. Every question is optional: unanswered stays null,
// which is not the same as "no".
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { profile as profileApi } from '@/api/endpoints'
import type { MedicalHistory } from '@/api/types'

import { toNumber, toText } from './forms'
import { useAction } from './useAction'

/** The questions in the order asked. `detail` is a text field shown when the answer is yes. */
export const HISTORY_SECTIONS: { title: string; counts?: string[]; flags: { name: string; detail?: string }[]; notes?: string[] }[] = [
  { title: 'pregnancies', counts: ['previous_children_count', 'miscarriage_count'], flags: [] },
  {
    title: 'conditions',
    flags: [
      { name: 'has_diabetes' }, { name: 'has_hypertension' },
      { name: 'has_nutrient_deficiency', detail: 'nutrient_deficiency_details' },
      { name: 'has_thyroid_disorder' }, { name: 'has_breast_cyst' }, { name: 'has_ovarian_cyst_pcos' },
    ],
    notes: ['underlying_conditions', 'current_medications'],
  },
  {
    title: 'surgery',
    flags: [
      { name: 'has_previous_surgery', detail: 'previous_surgery_details' }, { name: 'has_anesthesia_history' },
      { name: 'has_dental_infection', detail: 'dental_notes' },
    ],
  },
  {
    title: 'infections',
    flags: [{ name: 'has_hiv' }, { name: 'has_hepatitis_b' }, { name: 'has_hepatitis_c' }],
    notes: ['other_infectious_diseases'],
  },
  {
    title: 'spouse',
    flags: [{ name: 'spouse_has_diabetes' }, { name: 'spouse_has_varicocele' }, { name: 'spouse_has_genetic_disorder' }],
    notes: ['spouse_health_notes'],
  },
]

export function useHistoryForm() {
  const router = useRouter()
  const { busy, error, act } = useAction()
  const loading = ref(true)
  const flags = reactive<Record<string, boolean | null>>({})
  const texts = reactive<Record<string, string>>({})

  for (const section of HISTORY_SECTIONS) {
    for (const name of [...(section.counts ?? []), ...(section.notes ?? [])]) texts[name] = ''
    for (const flag of section.flags) {
      flags[flag.name] = null
      if (flag.detail) texts[flag.detail] = ''
    }
  }

  onMounted(async () => {
    await act(async () => {
      const saved = await profileApi.history()
      if (!saved) return
      for (const name of Object.keys(flags)) flags[name] = (saved[name] as boolean | null) ?? null
      for (const name of Object.keys(texts)) texts[name] = saved[name] === null || saved[name] === undefined ? '' : String(saved[name])
    })
    loading.value = false
  })

  async function save() {
    const values: MedicalHistory = { ...flags }
    for (const section of HISTORY_SECTIONS) {
      for (const name of section.counts ?? []) values[name] = toNumber(texts[name])
      for (const name of section.notes ?? []) values[name] = toText(texts[name])
      // A detail only makes sense while its question is answered yes.
      for (const flag of section.flags) if (flag.detail) values[flag.detail] = flags[flag.name] ? toText(texts[flag.detail]) : null
    }
    if (await act(() => profileApi.saveHistory(values), 'history.saved', true)) router.back()
  }

  return { loading, busy, error, flags, texts, save }
}
