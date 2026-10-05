<script setup lang="ts">
import { computed } from 'vue'

import { useFormat } from '@/utils/useFormat'

const props = defineProps<{ page: number; perPage: number; total: number }>()
defineEmits<{ go: [page: number] }>()
const { num } = useFormat()
const pages = computed(() => Math.max(1, Math.ceil(props.total / props.perPage)))
</script>

<template>
  <div class="flex flex-wrap items-center justify-between gap-4 text-sm">
    <span class="text-base-content/60">{{ $t('app.total', { n: num(total) }) }}</span>
    <div class="join rounded-full">
      <button class="btn btn-sm join-item" :disabled="page <= 1" @click="$emit('go', page - 1)">{{ $t('app.previous') }}</button>
      <span class="btn btn-sm join-item pointer-events-none">{{ $t('app.pageOf', { page: num(page), pages: num(pages) }) }}</span>
      <button class="btn btn-sm join-item" :disabled="page >= pages" @click="$emit('go', page + 1)">{{ $t('app.next') }}</button>
    </div>
  </div>
</template>
