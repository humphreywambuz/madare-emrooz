import { createI18n } from 'vue-i18n'

import type { Locale } from '@/utils/format'
import { load, store } from '@/utils/storage'

import en from './en'
import fa from './fa'

const KEY = 'madare.locale'

const savedLocale = (): Locale => (load(KEY) === 'en' ? 'en' : 'fa')

export const i18n = createI18n({
  legacy: false,
  locale: savedLocale(),
  fallbackLocale: 'en',
  messages: { fa, en },
})

/** Switch language: Persian is right-to-left, English left-to-right. */
export function setLocale(locale: Locale) {
  i18n.global.locale.value = locale
  document.documentElement.lang = locale
  document.documentElement.dir = locale === 'fa' ? 'rtl' : 'ltr'
  document.title = `${i18n.global.t('app.panel')} · ${i18n.global.t('app.name')}`
  store(KEY, locale)
}
