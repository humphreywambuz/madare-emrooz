import { createRouter, createWebHistory, type RouteLocationRaw } from 'vue-router'

import type { Role } from '@/api/types'
import { useAuth } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    roles?: Role[]
    public?: boolean
  }
}

export function homeFor(role: Role | null): RouteLocationRaw {
  if (role === 'midwife') return { name: 'alerts' }
  if (role === 'doctor') return { name: 'patients' }
  if (role === 'admin') return { name: 'unassigned' }
  return { name: 'login' }
}

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { public: true } },
    {
      path: '/',
      component: () => import('@/layouts/AppShell.vue'),
      children: [
        { path: '', name: 'home', redirect: () => homeFor(useAuth().role) },
        {
          path: 'alerts', name: 'alerts', component: () => import('@/views/AlertsView.vue'),
          meta: { roles: ['midwife'] }, props: { mode: 'midwife' },
        },
        {
          path: 'patients', name: 'patients', component: () => import('@/views/PatientsView.vue'),
          meta: { roles: ['midwife', 'doctor'] },
        },
        {
          path: 'patients/:id', name: 'patient', component: () => import('@/views/PatientView.vue'),
          meta: { roles: ['midwife', 'doctor'] }, props: true,
        },
        {
          path: 'admin/unassigned', name: 'unassigned', component: () => import('@/views/AlertsView.vue'),
          meta: { roles: ['admin'] }, props: { mode: 'admin' },
        },
        {
          path: 'admin/staff', name: 'staff', component: () => import('@/views/StaffView.vue'),
          meta: { roles: ['admin'] },
        },
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
  if (to.meta.public) {
    return to.name === 'login' && auth.isSignedIn ? homeFor(auth.role) : true
  }
  if (!auth.isSignedIn) return { name: 'login', query: { next: to.fullPath } }
  const allowed = to.matched.every((r) => !r.meta.roles || r.meta.roles.includes(auth.role!))
  return allowed ? true : homeFor(auth.role)
})
