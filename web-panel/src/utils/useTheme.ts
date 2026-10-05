// Light / dark theme: follows the system until the user picks one, then remembers the choice.
import { computed, ref } from 'vue'

import { load, store } from './storage'

const KEY = 'madare.theme'
const chosen = ref<string | null>(load(KEY))
if (chosen.value) document.documentElement.dataset.theme = chosen.value

export function useTheme() {
  const isDark = computed(() =>
    (chosen.value ?? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')) === 'dark',
  )

  function toggle() {
    chosen.value = isDark.value ? 'light' : 'dark'
    document.documentElement.dataset.theme = chosen.value
    store(KEY, chosen.value)
  }

  return { isDark, toggle }
}
