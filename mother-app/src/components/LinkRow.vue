<script setup lang="ts">
// A row that opens another page: an icon on a tinted tile, a title and a line of detail.
import AppIcon from '@/components/AppIcon.vue'
import type { IconName } from '@/components/icons'

defineProps<{ to: string; icon: IconName; title: string; detail?: string }>()
</script>

<template>
  <li>
    <RouterLink :to="to" class="list-row items-center transition-colors hover:bg-base-200 active:bg-base-200">
      <span class="grid size-11 place-items-center rounded-xl bg-primary/10 text-primary">
        <AppIcon :name="icon" class="size-5" />
      </span>
      <div class="min-w-0">
        <div class="font-semibold">{{ title }}</div>
        <div v-if="detail" class="text-sm leading-relaxed text-base-content/60">{{ detail }}</div>
      </div>
      <AppIcon name="chevron" class="size-4 text-base-content/40 rtl:rotate-180" />
    </RouterLink>
  </li>
</template>
