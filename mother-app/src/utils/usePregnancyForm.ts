// Recording a pregnancy, correcting its details later, and marking its end.
import { onMounted, ref, shallowRef } from 'vue'
import { useRouter } from 'vue-router'

import { pregnancy as pregnancyApi, profile as profileApi } from '@/api/endpoints'
import type { Pregnancy } from '@/api/types'
import { useAuth } from '@/stores/auth'

import { toText } from './forms'
import { useAction } from './useAction'

export function usePregnancyForm() {
  const auth = useAuth()
  const router = useRouter()
  const { busy, error, act } = useAction()

  const loading = ref(true)
  const current = shallowRef<Pregnancy | null>(null)
  const lmpDate = ref('')
  const cycleLength = ref(28)
  const conceptionType = ref<'natural' | 'assisted'>('natural')
  const providerType = ref('')
  const providerName = ref('')
  const ending = ref(false)

  onMounted(async () => {
    await act(async () => {
      current.value = await pregnancyApi.current()
      const p = current.value
      if (p) {
        lmpDate.value = p.lmp_date
        cycleLength.value = p.avg_cycle_length_days
        conceptionType.value = p.conception_type
        providerType.value = p.care_provider_type ?? ''
        providerName.value = p.care_provider_name ?? ''
      }
    })
    loading.value = false
  })

  async function save() {
    const values = {
      lmp_date: lmpDate.value,
      conception_type: conceptionType.value,
      avg_cycle_length_days: cycleLength.value,
      care_provider_type: providerType.value || null,
      care_provider_name: toText(providerName.value),
    }
    const call = () => (current.value ? pregnancyApi.correct(values) : pregnancyApi.start(values))
    if (await act(call, 'pregnancy.saved', true)) router.replace({ name: 'home' })
  }

  async function end(status: 'delivered' | 'ended') {
    const ok = await act(async () => {
      await pregnancyApi.end(status)
      // Ending as "delivered" changes her status, and with it her home screen.
      const profile = await profileApi.get()
      if (profile) auth.setProfile(profile)
    }, 'pregnancy.ended')
    if (ok) router.replace({ name: 'home' })
  }

  return { loading, busy, error, current, lmpDate, cycleLength, conceptionType, providerType, providerName, ending, save, end }
}
