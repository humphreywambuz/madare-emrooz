// One function per backend endpoint the mother's app uses.
import { api, apiBlob, ApiError } from './client'
import type {
  DailyLog, FitnessProfile, MedicalDocument, MedicalHistory, Midwife, PartnerLink, Pregnancy, PregnancyInput,
  Profile, ProfileInput, RehabAnswers, RehabProfile, Tokens, Uuid,
} from './types'

/** The backend answers 404 for "not filled in yet"; the app treats that as null. */
async function orNull<T>(call: Promise<T>): Promise<T | null> {
  try {
    return await call
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null
    throw e
  }
}

export const auth = {
  requestCode: (mobile: string) =>
    api<{ mobile: string; expires_in: number; resend_after: number }>('/auth/otp/request', {
      method: 'POST', json: { mobile }, auth: false,
    }),
  verify: (mobile: string, code: string) =>
    api<Tokens>('/auth/otp/verify', { method: 'POST', json: { mobile, code }, auth: false }),
  refresh: (refresh_token: string) =>
    api<Tokens>('/auth/token/refresh', { method: 'POST', json: { refresh_token }, auth: false }),
  logout: (refresh_token: string) =>
    api<void>('/auth/logout', { method: 'POST', json: { refresh_token }, auth: false }),
  me: () => api<{ id: Uuid; mobile: string; role: Tokens['user']['role'] }>('/me'),
}

export const profile = {
  get: () => orNull(api<Profile>('/profile')),
  save: (values: ProfileInput) => api<Profile>('/profile', { method: 'PUT', json: values }),
  history: () => orNull(api<MedicalHistory>('/medical-history')),
  saveHistory: (values: MedicalHistory) => api<MedicalHistory>('/medical-history', { method: 'PUT', json: values }),
}

export const pregnancy = {
  current: () => orNull(api<Pregnancy>('/pregnancies/current')),
  start: (values: PregnancyInput) => api<Pregnancy>('/pregnancies', { method: 'POST', json: values }),
  correct: (changes: Partial<PregnancyInput>) => api<Pregnancy>('/pregnancies/current', { method: 'PATCH', json: changes }),
  end: (status: 'delivered' | 'ended') =>
    api<Pregnancy>('/pregnancies/current/end', { method: 'POST', json: { status } }),
}

export const logs = {
  mine: () => api<{ items: DailyLog[] }>('/daily-logs'),
  report: (has_spotting_or_bleeding: boolean) =>
    api<DailyLog>('/daily-logs', { method: 'POST', json: { has_spotting_or_bleeding } }),
}

export const midwives = {
  list: () => api<{ items: Midwife[] }>('/midwives'),
  mine: () => api<{ midwife: Midwife | null }>('/my-midwife'),
  choose: (midwife_id: Uuid) => api<{ midwife: Midwife }>('/my-midwife', { method: 'PUT', json: { midwife_id } }),
}

export const partner = {
  current: () => orNull(api<PartnerLink>('/partner-link')),
  create: () => api<PartnerLink>('/partner-link', { method: 'POST' }),
  revoke: () => api<void>('/partner-link', { method: 'DELETE' }),
}

export const fitness = {
  get: () => orNull(api<FitnessProfile>('/fitness-profile')),
  save: (goal: string, goal_note: string | null) =>
    api<FitnessProfile>('/fitness-profile', { method: 'PUT', json: { goal, goal_note } }),
}

export const rehab = {
  get: () => orNull(api<RehabProfile>('/rehab-profile')),
  save: (answers: RehabAnswers) => api<RehabProfile>('/rehab-profile', { method: 'PUT', json: answers }),
}

export const documents = {
  list: () => api<{ items: MedicalDocument[] }>('/documents'),
  file: (id: Uuid) => apiBlob(`/documents/${id}/file`),
}
