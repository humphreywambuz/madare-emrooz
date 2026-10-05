// The mother's goal and profile: the first thing a new mother fills in, and editable later.
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { profile as profileApi } from '@/api/endpoints'
import type { JoinGoal, ReproductiveStatus } from '@/api/types'
import { useAuth } from '@/stores/auth'

import { asciiDigits } from './format'
import { toNumber, toText } from './forms'
import { useAction } from './useAction'

export const BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

export function useProfileForm() {
  const auth = useAuth()
  const router = useRouter()
  const { busy, error, act } = useAction()
  const saved = auth.profile

  const goal = ref<JoinGoal | null>(saved?.join_goal ?? null)
  const firstName = ref(saved?.first_name ?? '')
  const lastName = ref(saved?.last_name ?? '')
  const birthDate = ref(saved?.birth_date ?? '')
  const height = ref(saved?.height_cm?.toString() ?? '')
  const weight = ref(saved?.initial_weight_kg?.toString() ?? '')
  const nationalCode = ref(saved?.national_code ?? '')
  const motherBlood = ref(saved?.mother_blood_type ?? '')
  const spouseBlood = ref(saved?.spouse_blood_type ?? '')
  const status = ref<ReproductiveStatus | null>(saved?.reproductive_status ?? null)

  const isPregnancyPath = computed(() => goal.value === 'pregnancy')
  const canSave = computed(() =>
    Boolean(goal.value && firstName.value.trim() && lastName.value.trim() && (!isPregnancyPath.value || status.value)),
  )

  async function save() {
    const ok = await act(async () => {
      auth.setProfile(await profileApi.save({
        join_goal: goal.value!,
        first_name: firstName.value.trim(),
        last_name: lastName.value.trim(),
        birth_date: birthDate.value || null,
        height_cm: toNumber(height.value),
        initial_weight_kg: toNumber(weight.value),
        // The pregnancy path asks more; the other paths keep what was saved before.
        national_code: isPregnancyPath.value ? toText(asciiDigits(nationalCode.value)) : saved?.national_code ?? null,
        mother_blood_type: isPregnancyPath.value ? motherBlood.value || null : saved?.mother_blood_type ?? null,
        spouse_blood_type: isPregnancyPath.value ? spouseBlood.value || null : saved?.spouse_blood_type ?? null,
        reproductive_status: isPregnancyPath.value ? status.value : saved?.reproductive_status ?? null,
      }))
    }, saved ? 'profile.saved' : undefined, true)
    if (ok) router.replace({ name: 'home' })
  }

  return {
    isNew: !saved, busy, error, canSave, isPregnancyPath, save,
    goal, firstName, lastName, birthDate, height, weight, nationalCode, motherBlood, spouseBlood, status,
  }
}
