import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Toast {
  id: number
  kind: 'success' | 'error' | 'info'
  text: string
}

let nextId = 1

export const useToasts = defineStore('toasts', () => {
  const items = ref<Toast[]>([])

  function show(text: string, kind: Toast['kind'] = 'success', ms = 4000) {
    const id = nextId++
    items.value.push({ id, kind, text })
    setTimeout(() => dismiss(id), ms)
  }

  function dismiss(id: number) {
    items.value = items.value.filter((t) => t.id !== id)
  }

  return { items, show, dismiss }
})
