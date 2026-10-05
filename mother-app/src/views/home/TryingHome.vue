<script setup lang="ts">
import HomeHeader from '@/components/HomeHeader.vue'
import LinkRow from '@/components/LinkRow.vue'
import SurfaceCard from '@/components/SurfaceCard.vue'
</script>

<template>
  <HomeHeader :text="$t('home.tryingText')" />
  <div class="flex flex-col gap-4 p-4">
    <p class="px-1 text-sm leading-relaxed text-base-content/60">{{ $t('home.tryingMore') }}</p>
    <SurfaceCard as="ul" class="list">
      <LinkRow to="/history" icon="heart" :title="$t('pages.history')" :detail="$t('home.historyDetail')" />
      <LinkRow to="/midwife" icon="stethoscope" :title="$t('nav.midwife')" :detail="$t('home.midwifeDetail')" />
      <LinkRow to="/profile" icon="user" :title="$t('home.nowPregnant')" :detail="$t('home.nowPregnantDetail')" />
    </SurfaceCard>
  </div>
</template>
