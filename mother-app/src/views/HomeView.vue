<script setup lang="ts">
// The home screen the backend chose for her path.
import { computed } from 'vue'

import { useAuth } from '@/stores/auth'

import FitnessHome from './home/FitnessHome.vue'
import PostpartumHome from './home/PostpartumHome.vue'
import PregnancyHome from './home/PregnancyHome.vue'
import RehabHome from './home/RehabHome.vue'
import TryingHome from './home/TryingHome.vue'

const HOMES = {
  pregnancy: PregnancyHome,
  trying_to_conceive: TryingHome,
  postpartum: PostpartumHome,
  fitness: FitnessHome,
  rehabilitation: RehabHome,
} as const

const auth = useAuth()
const home = computed(() => HOMES[auth.profile!.home])
</script>

<template>
  <!-- One stable root, so the screen transition animates the whole home and not a skeleton that gets swapped out. -->
  <div><component :is="home" /></div>
</template>
