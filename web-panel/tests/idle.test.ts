import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h } from 'vue'

import { IDLE_MINUTES, useIdleSignOut } from '@/utils/useIdleSignOut'

const MINUTE = 60_000

function mountWatcher(onIdle: () => void) {
  let state!: ReturnType<typeof useIdleSignOut>
  const wrapper = mount(defineComponent({
    setup() {
      state = useIdleSignOut(onIdle)
      return () => h('div')
    },
  }))
  return { wrapper, state: () => state }
}

describe('idle sign-out', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.useFakeTimers()
  })
  afterEach(() => vi.useRealTimers())

  it('warns a minute before and signs out after the idle limit', () => {
    const onIdle = vi.fn()
    const { state } = mountWatcher(onIdle)
    vi.advanceTimersByTime((IDLE_MINUTES - 1) * MINUTE - 2_000)
    expect(state().warning.value).toBe(false)
    vi.advanceTimersByTime(3_000)
    expect(state().warning.value).toBe(true)
    expect(state().secondsLeft.value).toBeLessThanOrEqual(60)
    vi.advanceTimersByTime(MINUTE)
    expect(onIdle).toHaveBeenCalledTimes(1)
    vi.advanceTimersByTime(5 * MINUTE)
    expect(onIdle).toHaveBeenCalledTimes(1) // only once
  })

  it('any input resets the clock and hides the warning', () => {
    const onIdle = vi.fn()
    const { state } = mountWatcher(onIdle)
    vi.advanceTimersByTime((IDLE_MINUTES - 0.5) * MINUTE)
    expect(state().warning.value).toBe(true)
    dispatchEvent(new KeyboardEvent('keydown', { key: 'a' }))
    vi.advanceTimersByTime(1_000)
    expect(state().warning.value).toBe(false)
    vi.advanceTimersByTime((IDLE_MINUTES - 2) * MINUTE)
    expect(onIdle).not.toHaveBeenCalled()
  })

  it('counts activity in another tab', () => {
    const onIdle = vi.fn()
    mountWatcher(onIdle)
    vi.advanceTimersByTime((IDLE_MINUTES - 2) * MINUTE)
    localStorage.setItem('madare.lastActive', String(Date.now())) // the other tab was used just now
    vi.advanceTimersByTime(5 * MINUTE)
    expect(onIdle).not.toHaveBeenCalled()
  })

  it('stops watching when the panel closes', () => {
    const onIdle = vi.fn()
    const { wrapper } = mountWatcher(onIdle)
    wrapper.unmount()
    vi.advanceTimersByTime((IDLE_MINUTES + 1) * MINUTE)
    expect(onIdle).not.toHaveBeenCalled()
  })
})
