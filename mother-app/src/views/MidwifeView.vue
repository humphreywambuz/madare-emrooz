<script setup lang="ts">
// Her midwife: the one she chose, and the list she can choose from.
import { onMounted } from 'vue'

import { midwives as midwivesApi } from '@/api/endpoints'
import AsyncState from '@/components/AsyncState.vue'
import EmptyState from '@/components/EmptyState.vue'
import SurfaceCard from '@/components/SurfaceCard.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { useAction } from '@/utils/useAction'
import { useAsync } from '@/utils/useAsync'
import { useFormat } from '@/utils/useFormat'

const { fullName } = useFormat()
const { busy, act } = useAction()
const { data, loading, error, run } = useAsync(async () => {
  const [list, mine] = await Promise.all([midwivesApi.list(), midwivesApi.mine()])
  return { midwives: list.items, mine: mine.midwife }
})
onMounted(run)

async function choose(id: string) {
  if (await act(() => midwivesApi.choose(id), 'midwife.chosen')) await run()
}
</script>

<template>
  <div class="flex flex-col gap-4 p-4 pt-6">
    <header class="animate-rise px-1 motion-reduce:animate-none">
      <h1 class="font-display text-2xl">{{ $t('nav.midwife') }}</h1>
      <p class="mt-1 text-sm leading-relaxed text-base-content/60">{{ $t('midwife.help') }}</p>
    </header>

    <AsyncState :loading="loading" :error="error" @retry="run">
      <template v-if="data">
        <section v-if="data.mine" class="rounded-3xl bg-primary/10 p-5">
          <p class="text-xs font-semibold text-primary">{{ $t('midwife.current') }}</p>
          <div class="mt-3 flex items-center gap-4">
            <UserAvatar :name="fullName(data.mine.first_name, data.mine.last_name)" size="lg" />
            <div class="min-w-0">
              <h2 class="text-lg font-bold">{{ fullName(data.mine.first_name, data.mine.last_name) }}</h2>
              <p v-if="data.mine.bio" class="mt-0.5 text-sm leading-relaxed text-base-content/70">{{ data.mine.bio }}</p>
            </div>
          </div>
        </section>

        <SurfaceCard v-if="!data.midwives.length">
          <EmptyState icon="stethoscope" :title="$t('nav.midwife')" :text="$t('midwife.empty')" />
        </SurfaceCard>
        <SurfaceCard v-else as="ul" class="list">
          <li class="p-4 pb-2 text-sm font-semibold">{{ $t(data.mine ? 'midwife.change' : 'midwife.choose') }}</li>
          <li v-for="m in data.midwives" :key="m.id" class="list-row items-center">
            <UserAvatar :name="fullName(m.first_name, m.last_name)" />
            <div class="list-col-grow min-w-0">
              <div class="font-semibold">{{ fullName(m.first_name, m.last_name) }}</div>
              <div v-if="m.bio" class="text-sm leading-relaxed text-base-content/60">{{ m.bio }}</div>
            </div>
            <span v-if="data.mine?.id === m.id" class="badge badge-success badge-soft">{{ $t('midwife.yours') }}</span>
            <button v-else class="btn btn-sm btn-soft btn-primary" :disabled="busy" @click="choose(m.id)">{{ $t('midwife.pick') }}</button>
          </li>
        </SurfaceCard>
      </template>
    </AsyncState>
  </div>
</template>
