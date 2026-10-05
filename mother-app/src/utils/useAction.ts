// Run an API call from a button: busy flag, success toast, error toast or inline error.
import { ref, shallowRef } from 'vue'
import { useI18n } from 'vue-i18n'

import { useToasts } from '@/stores/toast'

import { useFormat } from './useFormat'

export function useAction() {
  const busy = ref(false)
  const error = shallowRef<unknown>(null)
  const toasts = useToasts()
  const { t } = useI18n()
  const { errorText } = useFormat()

  /** Returns true on success. With `inline`, the error stays in `error` (for forms) instead of a toast. */
  async function act(call: () => Promise<unknown>, success?: string, inline = false): Promise<boolean> {
    busy.value = true
    error.value = null
    try {
      await call()
      if (success) toasts.show(t(success))
      return true
    } catch (e) {
      if (inline) error.value = e
      else toasts.show(errorText(e), 'error')
      return false
    } finally {
      busy.value = false
    }
  }

  return { busy, error, act }
}
