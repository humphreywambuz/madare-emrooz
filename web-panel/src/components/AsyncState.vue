<script setup lang="ts">
// Shows a spinner while loading, the error with a retry button, or the content.
import { useFormat } from '@/utils/useFormat'

defineProps<{ loading: boolean; error: unknown }>()
defineEmits<{ retry: [] }>()
const { errorText } = useFormat()
</script>

<template>
  <div v-if="loading" class="flex justify-center py-16" role="status">
    <span class="loading loading-spinner loading-lg text-primary" />
    <span class="sr-only">{{ $t('app.loading') }}</span>
  </div>
  <div v-else-if="error" role="alert" class="alert alert-error alert-soft">
    <span>{{ errorText(error) }}</span>
    <button class="btn btn-sm" @click="$emit('retry')">{{ $t('app.retry') }}</button>
  </div>
  <slot v-else />
</template>
