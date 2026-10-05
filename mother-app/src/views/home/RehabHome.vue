<script setup lang="ts">
import HomeHeader from '@/components/HomeHeader.vue'
import RehabPanel from '@/components/RehabPanel.vue'
</script>

<template>
  <HomeHeader :text="$t('home.rehabText')" />
  <div class="p-4"><RehabPanel /></div>
</template>
