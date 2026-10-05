// Formatting and labels bound to the current language, for templates.
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { ApiError } from '@/api/client'

import {
  formatDate, formatDateTime, formatMobile, formatNumber, formatTimeAgo, localDigits, type Locale,
} from './format'

export function useFormat() {
  const { t, te, locale } = useI18n()
  const current = computed(() => locale.value as Locale)

  return {
    locale: current,
    num: (v: number | string | null | undefined) => formatNumber(v, current.value),
    digits: (s: string | null | undefined) => localDigits(s, current.value),
    date: (iso: string | null | undefined) => formatDate(iso, current.value),
    dateTime: (iso: string | null | undefined) => formatDateTime(iso, current.value),
    timeAgo: (iso: string | null | undefined) => formatTimeAgo(iso, current.value),
    mobile: (m: string | null | undefined) => formatMobile(m, current.value),
    /** Label of a backend enum value, e.g. enumLabel('join_goal', 'fitness'). */
    enumLabel: (group: string, value: string | null | undefined) => {
      if (!value) return '—'
      const key = `enums.${group}.${value}`
      return te(key) ? t(key) : value
    },
    yesNo: (v: unknown) => (v === true ? t('app.yes') : v === false ? t('app.no') : t('app.notAnswered')),
    fullName: (first?: string | null, last?: string | null) => [first, last].filter(Boolean).join(' '),
    /** A user-facing message for an error from the API. */
    errorText: (error: unknown) => {
      if (error instanceof ApiError) {
        if (error.code === 'staff_account') return t('login.staffAccount')
        const key = `errors.${error.code}`
        // Persian users get our translation; English users get the server's specific message.
        if (current.value === 'fa' && te(key)) return t(key)
        return error.message || (te(key) ? t(key) : t('errors.generic'))
      }
      return t('errors.generic')
    },
  }
}
