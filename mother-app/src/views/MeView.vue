<script setup lang="ts">
// Her account: who she is, and the settings of the app.
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import AppIcon from '@/components/AppIcon.vue'
import LinkRow from '@/components/LinkRow.vue'
import SurfaceCard from '@/components/SurfaceCard.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { useAuth } from '@/stores/auth'
import { useFormat } from '@/utils/useFormat'
import { useTheme } from '@/utils/useTheme'

const auth = useAuth()
const router = useRouter()
const { fullName, mobile, num } = useFormat()
const { isDark, toggle } = useTheme()
const profile = computed(() => auth.profile!)

const facts = computed(() => [
  { label: 'me.age', value: num(profile.value.age) },
  { label: 'me.height', value: num(profile.value.height_cm) },
  { label: 'me.blood', value: profile.value.mother_blood_type ?? '—' },
])

async function signOut() {
  await auth.signOut()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="flex flex-col gap-4 p-4 pt-6">
    <header class="animate-rise flex items-center gap-4 motion-reduce:animate-none">
      <UserAvatar :name="fullName(profile.first_name, profile.last_name)" size="lg" />
      <div class="min-w-0">
        <h1 class="font-display text-2xl leading-tight">{{ fullName(profile.first_name, profile.last_name) }}</h1>
        <p class="ltr text-start text-sm text-base-content/60">{{ mobile(auth.mobile) }}</p>
      </div>
    </header>

    <dl class="grid grid-cols-3 gap-3">
      <SurfaceCard v-for="f in facts" :key="f.label" as="div" class="p-4 text-center">
        <dd class="font-display text-2xl leading-none tabular-nums"><bdi class="ltr">{{ f.value }}</bdi></dd>
        <dt class="mt-1 text-xs text-base-content/60">{{ $t(f.label) }}</dt>
      </SurfaceCard>
    </dl>

    <SurfaceCard as="ul" class="list">
      <LinkRow to="/profile" icon="pencil" :title="$t('pages.profile')" :detail="$t(`goal.${profile.join_goal}.label`)" />
      <LinkRow to="/history" icon="heart" :title="$t('pages.history')" :detail="$t('home.historyDetail')" />
      <li class="list-row items-center">
        <span class="grid size-11 place-items-center rounded-xl bg-primary/10 text-primary">
          <AppIcon :name="isDark ? 'moon' : 'sun'" class="size-5" />
        </span>
        <div class="font-semibold">{{ $t('me.dark') }}</div>
        <input type="checkbox" class="toggle toggle-primary" :checked="isDark" :aria-label="$t('me.dark')" @change="toggle" />
      </li>
    </SurfaceCard>

    <button class="btn btn-outline btn-block" @click="signOut"><AppIcon name="logout" class="size-4" />{{ $t('me.signOut') }}</button>
  </div>
</template>
