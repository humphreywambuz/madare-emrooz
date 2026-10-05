<script setup lang="ts">
import EmptyState from '@/components/EmptyState.vue'
import SurfaceCard from '@/components/SurfaceCard.vue'
</script>

<template>
  <div class="mx-auto grid min-h-screen w-full max-w-md place-items-center p-6">
    <SurfaceCard class="w-full">
      <EmptyState icon="search" tone="warning" :title="$t('notFound.title')">
        <RouterLink to="/" class="btn btn-primary">{{ $t('notFound.back') }}</RouterLink>
      </EmptyState>
    </SurfaceCard>
  </div>
</template>
