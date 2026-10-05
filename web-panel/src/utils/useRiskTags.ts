// Adding and removing a mother's risk flags from her record.
import { computed, type MaybeRefOrGetter, ref, toValue } from 'vue'

import { patients } from '@/api/endpoints'
import type { RiskTag } from '@/api/types'

import { useAction } from './useAction'

const ALL_TAGS = [
  'needs_rhogam', 'thyroid', 'miscarriage_history', 'diabetes', 'hypertension', 'anemia', 'infectious_disease', 'other',
]

export function useRiskTags(patientId: MaybeRefOrGetter<string>, tags: MaybeRefOrGetter<RiskTag[]>, onChanged: () => void) {
  const { busy, error, act } = useAction()
  const available = computed(() => ALL_TAGS.filter((tag) => !toValue(tags).some((t) => t.tag === tag)))

  const adding = ref(false)
  const newTag = ref('')
  const newNote = ref('')

  function openAdd() {
    newTag.value = available.value[0] ?? ''
    newNote.value = ''
    error.value = null
    adding.value = true
  }

  async function add() {
    if (await act(() => patients.addTag(toValue(patientId), newTag.value, newNote.value || null), 'app.saved', true)) {
      adding.value = false
      onChanged()
    }
  }

  async function remove(tag: string) {
    if (await act(() => patients.removeTag(toValue(patientId), tag), 'app.saved')) onChanged()
  }

  return { busy, error, available, adding, newTag, newNote, openAdd, add, remove }
}
