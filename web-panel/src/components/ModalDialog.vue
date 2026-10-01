<script setup lang="ts">
// A daisyUI modal on a native <dialog>: Esc and the backdrop close it, focus stays inside.
import { ref, watch } from 'vue'

const open = defineModel<boolean>('open', { required: true })
defineProps<{ title: string; wide?: boolean }>()

const dialog = ref<HTMLDialogElement>()

watch(open, (value) => {
  if (value) dialog.value?.showModal()
  else dialog.value?.close()
})
</script>

<template>
  <dialog ref="dialog" class="modal" @close="open = false">
    <div class="modal-box" :class="wide ? 'max-w-2xl' : ''">
      <h3 class="mb-4 text-lg font-bold">{{ title }}</h3>
      <slot />
    </div>
    <form method="dialog" class="modal-backdrop"><button>close</button></form>
  </dialog>
</template>
