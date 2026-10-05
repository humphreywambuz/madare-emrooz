<script setup lang="ts">
// After the birth: the two paths open to her, fitness and postpartum rehabilitation.
import FitnessPanel from '@/components/FitnessPanel.vue'
import HomeHeader from '@/components/HomeHeader.vue'
import RehabPanel from '@/components/RehabPanel.vue'
</script>

<template>
  <HomeHeader :text="$t('home.postpartumText')" />
  <div class="flex flex-col gap-4 p-4">
    <RehabPanel />
    <FitnessPanel />
  </div>
</template>
