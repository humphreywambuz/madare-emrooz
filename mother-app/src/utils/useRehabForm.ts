// The rehabilitation questionnaire: the common questions, then the ones of her sub-type.
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { rehab as rehabApi } from '@/api/endpoints'
import type { RehabAnswers } from '@/api/types'
import { useAuth } from '@/stores/auth'

import { toText } from './forms'
import { useAction } from './useAction'

type Question = { name: string; options?: string[] }

const PERFORMANCE: Question[] = [
  { name: 'training_goal', options: ['stress_reduction', 'flexibility', 'posture_correction', 'chronic_stiffness_relief'] },
  { name: 'fitness_level', options: ['inactive', 'beginner', 'professional'] },
  { name: 'has_recurrent_muscle_spasms' },
]

/** Only the questions of the chosen sub-type may be answered (the backend rejects the others). */
export const SUBCATEGORY_QUESTIONS: Record<string, Question[]> = {
  injury_correction: [
    { name: 'injury_onset', options: ['recent', 'one_to_six_months', 'chronic'] },
    { name: 'pain_type', options: ['shooting', 'burning_tingling', 'dull_aching'] },
    { name: 'has_daily_movement_limitation' },
  ],
  postpartum_recovery: [
    { name: 'time_since_delivery', options: ['under_40_days', 'two_to_six_months', 'over_six_months'] },
    { name: 'has_pelvic_warning_signs' },
    { name: 'has_diastasis_recti_or_stitch_pain' },
  ],
  performance_improvement: PERFORMANCE,
  yoga_meditation: PERFORMANCE,
  orthopedic_referral: [{ name: 'referral_reason', options: ['severe_joint_pain', 'injury_fracture', 'spine_checkup'] }],
}

export function useRehabForm() {
  const auth = useAuth()
  const router = useRouter()
  const { busy, error, act } = useAction()
  const loading = ref(true)
  // Her plan is approved now; changing the answers sends it back to the doctor.
  const approved = ref(false)

  // A mother who has given birth starts on "postpartum recovery".
  const subcategory = ref(auth.profile?.home === 'postpartum' ? 'postpartum_recovery' : 'injury_correction')
  const painLevel = ref(5)
  const hadSurgery = ref<boolean | null>(null)
  const surgeryName = ref('')
  const usesMedication = ref<boolean | null>(null)
  const extra = reactive<Record<string, string | boolean | null>>({})

  const questions = computed(() => SUBCATEGORY_QUESTIONS[subcategory.value] ?? [])
  // Every question of the sub-type starts unanswered.
  watch(questions, (list) => {
    for (const q of list) extra[q.name] ??= null
  }, { immediate: true })

  const canSave = computed(() =>
    hadSurgery.value !== null && usesMedication.value !== null && (!hadSurgery.value || surgeryName.value.trim() !== ''),
  )

  onMounted(async () => {
    await act(async () => {
      const saved = await rehabApi.get()
      if (!saved) return
      approved.value = !saved.is_advanced_locked
      subcategory.value = saved.subcategory
      painLevel.value = saved.pain_level
      hadSurgery.value = saved.had_related_surgery as boolean
      surgeryName.value = (saved.related_surgery_name as string | null) ?? ''
      usesMedication.value = saved.uses_pain_medication as boolean
      for (const q of questions.value) extra[q.name] = (saved[q.name] as string | boolean | null) ?? null
    })
    loading.value = false
  })

  async function save() {
    const answers: RehabAnswers = {
      subcategory: subcategory.value,
      pain_level: painLevel.value,
      had_related_surgery: hadSurgery.value,
      related_surgery_name: hadSurgery.value ? toText(surgeryName.value) : null,
      uses_pain_medication: usesMedication.value,
    }
    for (const q of questions.value) {
      const answer = extra[q.name]
      if (answer !== null && answer !== undefined && answer !== '') answers[q.name] = answer
    }
    if (await act(() => rehabApi.save(answers), 'rehab.saved', true)) router.replace({ name: 'home' })
  }

  return { loading, busy, error, approved, subcategory, painLevel, hadSurgery, surgeryName, usesMedication, extra, questions, canSave, save }
}
