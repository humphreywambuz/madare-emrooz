import { createRouter, createWebHistory } from 'vue-router'

import { useAuth } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    public?: boolean
    /** Shown in the header of inner pages; the key of a page title in the translations. */
    title?: string
  }
}

export const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { public: true } },
    { path: '/welcome', name: 'welcome', component: () => import('@/views/ProfileFormView.vue') },
    {
      path: '/',
      component: () => import('@/layouts/AppShell.vue'),
      children: [
        { path: '', name: 'home', component: () => import('@/views/HomeView.vue') },
        { path: 'midwife', name: 'midwife', component: () => import('@/views/MidwifeView.vue') },
        { path: 'documents', name: 'documents', component: () => import('@/views/DocumentsView.vue') },
        { path: 'me', name: 'me', component: () => import('@/views/MeView.vue') },
      ],
    },
    {
      path: '/',
      component: () => import('@/layouts/PageShell.vue'),
      children: [
        { path: 'profile', name: 'profile', component: () => import('@/views/ProfileFormView.vue'), meta: { title: 'pages.profile' } },
        { path: 'pregnancy', name: 'pregnancy', component: () => import('@/views/PregnancyFormView.vue'), meta: { title: 'pages.pregnancy' } },
        { path: 'history', name: 'history', component: () => import('@/views/HistoryView.vue'), meta: { title: 'pages.history' } },
        { path: 'partner', name: 'partner', component: () => import('@/views/PartnerView.vue'), meta: { title: 'pages.partner' } },
        { path: 'fitness', name: 'fitness', component: () => import('@/views/FitnessView.vue'), meta: { title: 'pages.fitness' } },
        { path: 'rehab', name: 'rehab', component: () => import('@/views/RehabView.vue'), meta: { title: 'pages.rehab' } },
      ],
    },
    { path: '/:rest(.*)*', name: 'not-found', component: () => import('@/views/NotFoundView.vue'), meta: { public: true } },
  ],
})

let restored = false

router.beforeEach(async (to) => {
  const auth = useAuth()
  if (!restored) {
    restored = true
    await auth.restore()
  }
  if (to.meta.public) return to.name === 'login' && auth.isSignedIn ? { name: 'home' } : true
  if (!auth.isSignedIn) return { name: 'login' }
  // A new mother chooses her goal and fills in her profile before anything else.
  if (!auth.hasProfile) return to.name === 'welcome' ? true : { name: 'welcome' }
  return to.name === 'welcome' ? { name: 'home' } : true
})
