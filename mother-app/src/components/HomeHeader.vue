<script setup lang="ts">
// The greeting at the top of the home screens: her name, her avatar and a line about where she is.
import UserAvatar from '@/components/UserAvatar.vue'
import { useAuth } from '@/stores/auth'
import { useFormat } from '@/utils/useFormat'

defineProps<{ text: string }>()
const auth = useAuth()
const { fullName } = useFormat()
</script>

<template>
  <header class="animate-rise flex items-start justify-between gap-4 px-5 pt-6 pb-2 motion-reduce:animate-none">
    <div class="min-w-0">
      <p class="text-sm text-base-content/60">{{ $t('home.hello', { name: auth.profile?.first_name }) }}</p>
      <h1 class="mt-1 font-display text-2xl leading-tight text-balance">{{ text }}</h1>
    </div>
    <RouterLink to="/me" :aria-label="$t('nav.me')">
      <UserAvatar :name="fullName(auth.profile?.first_name, auth.profile?.last_name)" />
    </RouterLink>
  </header>
</template>
