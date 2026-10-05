<script setup lang="ts">
// Her rehabilitation path: the questionnaire, the specialist visit and the doctor's approval.
import { onMounted } from 'vue'

import { rehab as rehabApi } from '@/api/endpoints'
import AppIcon from '@/components/AppIcon.vue'
import AsyncState from '@/components/AsyncState.vue'
import SurfaceCard from '@/components/SurfaceCard.vue'
import { useAsync } from '@/utils/useAsync'
import { useFormat } from '@/utils/useFormat'

const { num } = useFormat()
const { data, loading, error, run } = useAsync(async () => ({ profile: await rehabApi.get() }))
onMounted(run)
</script>

<template>
  <SurfaceCard>
    <div class="card-body gap-3 p-5">
      <div class="flex items-center gap-3">
        <span class="grid size-11 place-items-center rounded-xl bg-secondary/20 text-secondary-content"><AppIcon name="activity" class="size-5" /></span>
        <h2 class="text-lg font-bold">{{ $t('pages.rehab') }}</h2>
      </div>
      <AsyncState :loading="loading" :error="error" @retry="run">
        <template v-if="!data?.profile">
          <p class="text-sm leading-relaxed text-base-content/60">{{ $t('rehab.intro') }}</p>
          <RouterLink to="/rehab" class="btn btn-primary mt-2 self-start">{{ $t('rehab.start') }}</RouterLink>
        </template>
        <template v-else>
          <p class="font-semibold">{{ $t(`rehab.subcategories.${data.profile.subcategory}`) }}</p>
          <p class="text-sm text-base-content/60">{{ $t('rehab.painNow', { n: num(data.profile.pain_level) }) }}</p>
          <ul class="steps steps-vertical text-sm">
            <li class="step step-primary">{{ $t('rehab.stepAnswers') }}</li>
            <li class="step" :class="{ 'step-primary': data.profile.specialist_visit_completed }">{{ $t('paths.stepVisit') }}</li>
            <li class="step" :class="{ 'step-primary': !data.profile.is_advanced_locked }">{{ $t('rehab.stepApproved') }}</li>
          </ul>
          <p class="text-sm leading-relaxed text-base-content/60">
            {{ $t(data.profile.is_advanced_locked ? 'rehab.locked' : 'rehab.unlocked') }}
          </p>
          <RouterLink to="/rehab" class="btn btn-sm btn-outline self-start">{{ $t('rehab.edit') }}</RouterLink>
        </template>
      </AsyncState>
    </div>
  </SurfaceCard>
</template>
