// Load data with loading/error state and a reload function.
import { ref, shallowRef } from 'vue'

export function useAsync<T>(load: () => Promise<T>) {
  const data = shallowRef<T | null>(null)
  const loading = ref(false)
  const error = shallowRef<unknown>(null)

  async function run() {
    loading.value = data.value === null
    error.value = null
    try {
      data.value = await load()
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, run }
}
