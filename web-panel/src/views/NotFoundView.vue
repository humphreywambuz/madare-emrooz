<script setup lang="ts">
import EmptyState from '@/components/EmptyState.vue'
</script>

<template>
  <div class="grid min-h-screen place-items-center bg-base-200 p-6">
    <div class="card card-border w-full max-w-md border-base-300 bg-base-100 shadow-level-2">
      <EmptyState icon="search" tone="warning" :title="$t('notFound.title')">
        <RouterLink to="/" class="btn btn-primary">{{ $t('notFound.back') }}</RouterLink>
      </EmptyState>
    </div>
  </div>
</template>
