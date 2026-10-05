<script setup lang="ts">
// A daisyUI modal on a native <dialog>: Esc and the backdrop close it, focus stays inside.
import { ref, watch } from 'vue'

import AppIcon from '@/components/AppIcon.vue'

const open = defineModel<boolean>('open', { required: true })
defineProps<{ title: string; wide?: boolean }>()

const dialog = ref<HTMLDialogElement>()

watch(open, (value) => {
  if (value) dialog.value?.showModal()
  else dialog.value?.close()
})
</script>

<template>
  <dialog ref="dialog" class="modal modal-bottom sm:modal-middle" @close="open = false">
    <div class="modal-box rounded-t-3xl sm:rounded-3xl" :class="wide ? 'sm:max-w-2xl' : ''">
      <form method="dialog">
        <button class="btn btn-sm btn-circle btn-ghost absolute end-3 top-3" :aria-label="$t('app.close')">
          <AppIcon name="x" class="size-4" />
        </button>
      </form>
      <h3 class="mb-4 pe-10 text-xl font-bold">{{ title }}</h3>
      <slot />
    </div>
    <form method="dialog" class="modal-backdrop"><button>close</button></form>
  </dialog>
</template>
