<script setup lang="ts">
// Shows a calm skeleton while loading, the error with a retry button, or the content.
import AppIcon from '@/components/AppIcon.vue'
import { useFormat } from '@/utils/useFormat'

defineProps<{ loading: boolean; error: unknown }>()
defineEmits<{ retry: [] }>()
const { errorText } = useFormat()
</script>

<template>
  <div v-if="loading" class="card card-border border-base-300 bg-base-100 shadow-level-1" role="status">
    <div class="card-body gap-4 p-5">
      <div class="skeleton h-5 w-1/3" />
      <div class="skeleton h-4 w-full" />
      <div class="skeleton h-4 w-5/6" />
      <div class="skeleton h-4 w-2/3" />
    </div>
    <span class="sr-only">{{ $t('app.loading') }}</span>
  </div>
  <div v-else-if="error" role="alert" class="alert alert-error alert-soft">
    <AppIcon name="x" class="size-5" />
    <span>{{ errorText(error) }}</span>
    <button class="btn btn-sm" @click="$emit('retry')">{{ $t('app.retry') }}</button>
  </div>
  <slot v-else />
</template>
