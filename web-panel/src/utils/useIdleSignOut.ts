// Signs staff out after a stretch without activity, so a mother's record isn't left open on a
// shared computer. Activity in any tab of the panel counts; a warning comes a minute before.
import { onBeforeUnmount, onMounted, ref } from 'vue'

import { load, store } from './storage'

export const IDLE_MINUTES = 15
const IDLE_MS = IDLE_MINUTES * 60_000
const WARNING_MS = 60_000
const LAST_ACTIVE_KEY = 'madare.lastActive'
const ACTIVITY = ['pointerdown', 'pointermove', 'keydown', 'wheel', 'scroll', 'touchstart'] as const

export function useIdleSignOut(onIdle: () => void) {
  const warning = ref(false)
  const secondsLeft = ref(0)
  let lastActive = Date.now()
  let lastShared = 0
  let timer: ReturnType<typeof setInterval> | undefined

  /** Called on any input; shared with the other tabs at most every few seconds. */
  function markActive() {
    lastActive = Date.now()
    if (lastActive - lastShared > 5_000) {
      store(LAST_ACTIVE_KEY, String(lastActive))
      lastShared = lastActive
    }
  }

  function check() {
    const idle = Date.now() - Math.max(lastActive, Number(load(LAST_ACTIVE_KEY)) || 0)
    if (idle >= IDLE_MS) {
      stop()
      warning.value = false
      onIdle()
      return
    }
    warning.value = idle >= IDLE_MS - WARNING_MS
    secondsLeft.value = Math.ceil((IDLE_MS - idle) / 1000)
  }

  function stop() {
    clearInterval(timer)
    ACTIVITY.forEach((name) => removeEventListener(name, markActive, true))
  }

  onMounted(() => {
    markActive()
    ACTIVITY.forEach((name) => addEventListener(name, markActive, { capture: true, passive: true }))
    // Every second, so the countdown is live; also catches up after the computer sleeps.
    timer = setInterval(check, 1000)
  })
  onBeforeUnmount(stop)

  return { warning, secondsLeft, markActive }
}
