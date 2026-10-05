import { createI18n } from 'vue-i18n'

import fa from './fa'

// Persian only for now; add a language by adding its messages here.
export const i18n = createI18n({ legacy: false, locale: 'fa', fallbackLocale: 'fa', messages: { fa } })
