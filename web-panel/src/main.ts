import '@fontsource-variable/vazirmatn'
import './style.css'

import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import { i18n, setLocale } from './i18n'
import { router } from './router'
import { useAuth } from './stores/auth'
import type { Locale } from './utils/format'

const app = createApp(App)
app.use(createPinia())
app.use(i18n)
app.use(router)

setLocale(i18n.global.locale.value as Locale)
// A refresh token that stopped working (expired, or the account was deactivated) ends the session.
useAuth().onSignedOut(() => router.push({ name: 'login' }))

app.mount('#app')
