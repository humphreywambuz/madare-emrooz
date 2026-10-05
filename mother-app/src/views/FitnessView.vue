<script setup lang="ts">
// Her fitness goal and, in her own words, what she wants from it.
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { fitness as fitnessApi } from '@/api/endpoints'
import ChoiceList from '@/components/ChoiceList.vue'
import { toText } from '@/utils/forms'
import { useAction } from '@/utils/useAction'
import { useFormat } from '@/utils/useFormat'

const { t } = useI18n()
const router = useRouter()
const { errorText } = useFormat()
const { busy, error, act } = useAction()

const loading = ref(true)
const goal = ref<string | null>(null)
const note = ref('')
const goals = computed(() =>
  ['weight_loss', 'muscle_gain', 'general_fitness', 'other'].map((value) => ({ value, label: t(`fitness.goals.${value}`) })),
)

onMounted(async () => {
  await act(async () => {
    const saved = await fitnessApi.get()
    goal.value = saved?.goal ?? null
    note.value = saved?.goal_note ?? ''
  })
  loading.value = false
})

async function save() {
  if (await act(() => fitnessApi.save(goal.value!, toText(note.value)), 'fitness.saved', true)) router.replace({ name: 'home' })
}
</script>

<template>
  <div>
  <div v-if="loading" class="skeleton h-64 w-full rounded-box" />
  <form v-else class="flex flex-col gap-6" @submit.prevent="save">
    <p class="leading-relaxed text-base-content/70">{{ $t('fitness.formHelp') }}</p>
    <ChoiceList v-model="goal" name="fitness-goal" :options="goals" />
    <fieldset class="fieldset">
      <legend class="fieldset-legend">{{ $t('fitness.note') }}</legend>
      <textarea v-model="note" class="textarea w-full" rows="3" maxlength="2000" :placeholder="$t('fitness.notePlaceholder')" />
    </fieldset>
    <div v-if="error" role="alert" class="alert alert-error alert-soft text-sm">{{ errorText(error) }}</div>
    <button class="btn btn-primary btn-lg btn-block" :disabled="busy || !goal">
      <span v-if="busy" class="loading loading-spinner loading-sm" />{{ $t('app.save') }}
    </button>
  </form>
  </div>
</template>
