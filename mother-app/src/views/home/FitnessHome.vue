<script setup lang="ts">
import FitnessPanel from '@/components/FitnessPanel.vue'
import HomeHeader from '@/components/HomeHeader.vue'
</script>

<template>
  <HomeHeader :text="$t('home.fitnessText')" />
  <div class="p-4"><FitnessPanel /></div>
</template>
