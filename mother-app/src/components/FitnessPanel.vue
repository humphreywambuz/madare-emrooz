<script setup lang="ts">
// Her fitness path: the goal she set, and whether the specialist visit has opened her dashboard.
import { onMounted } from 'vue'

import { fitness as fitnessApi } from '@/api/endpoints'
import AppIcon from '@/components/AppIcon.vue'
import AsyncState from '@/components/AsyncState.vue'
import SurfaceCard from '@/components/SurfaceCard.vue'
import { useAsync } from '@/utils/useAsync'

const { data, loading, error, run } = useAsync(async () => ({ profile: await fitnessApi.get() }))
onMounted(run)
</script>

<template>
  <SurfaceCard>
    <div class="card-body gap-3 p-5">
      <div class="flex items-center gap-3">
        <span class="grid size-11 place-items-center rounded-xl bg-info/10 text-info"><AppIcon name="dumbbell" class="size-5" /></span>
        <h2 class="text-lg font-bold">{{ $t('pages.fitness') }}</h2>
      </div>
      <AsyncState :loading="loading" :error="error" @retry="run">
        <template v-if="!data?.profile">
          <p class="text-sm leading-relaxed text-base-content/60">{{ $t('fitness.intro') }}</p>
          <RouterLink to="/fitness" class="btn btn-primary mt-2 self-start">{{ $t('fitness.start') }}</RouterLink>
        </template>
        <template v-else>
          <p class="font-semibold">{{ $t(`fitness.goals.${data.profile.goal}`) }}</p>
          <p v-if="data.profile.goal_note" class="text-sm leading-relaxed text-base-content/60">{{ data.profile.goal_note }}</p>
          <ul class="steps steps-vertical text-sm">
            <li class="step step-primary">{{ $t('fitness.stepGoal') }}</li>
            <li class="step" :class="{ 'step-primary': data.profile.specialist_visit_completed }">{{ $t('paths.stepVisit') }}</li>
            <li class="step" :class="{ 'step-primary': data.profile.dashboard_unlocked }">{{ $t('fitness.stepDashboard') }}</li>
          </ul>
          <p class="text-sm leading-relaxed text-base-content/60">
            {{ $t(data.profile.dashboard_unlocked ? 'fitness.unlocked' : 'paths.visitNeeded') }}
          </p>
          <RouterLink to="/fitness" class="btn btn-sm btn-outline self-start">{{ $t('fitness.edit') }}</RouterLink>
        </template>
      </AsyncState>
    </div>
  </SurfaceCard>
</template>
