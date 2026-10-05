// The number of open red alerts for the signed-in midwife or admin, kept fresh for the menu.
import { onMounted, onUnmounted, ref } from 'vue'

import { alerts } from '@/api/endpoints'
import { useAuth } from '@/stores/auth'

const REFRESH_MS = 60_000

export function useOpenAlerts() {
  const auth = useAuth()
  const count = ref(0)
  let timer: ReturnType<typeof setInterval> | undefined

  async function refresh() {
    if (auth.role !== 'midwife' && auth.role !== 'admin') return
    try {
      const result = auth.role === 'midwife' ? await alerts.mine() : await alerts.unassigned()
      count.value = result.items.length
    } catch {
      /* the page itself shows errors */
    }
  }

  onMounted(() => {
    refresh()
    timer = setInterval(refresh, REFRESH_MS)
    window.addEventListener('alerts-changed', refresh)
  })
  onUnmounted(() => {
    clearInterval(timer)
    window.removeEventListener('alerts-changed', refresh)
  })

  return { count }
}
