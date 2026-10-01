// One function per backend endpoint the panel uses (see backend/docs/architecture.md, "Phase 1 API").
import { api, apiBlob } from './client'
import type {
  Alert, DailyLog, MedicalDocument, Page, PatientRecord, PatientRow, Pregnancy,
  Role, StaffMember, Summary, Tokens, Uuid,
} from './types'

const patient = (id: Uuid) => `/staff/patients/${id}`

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
  staffMe: () => api<StaffMember>('/staff/me'),
}

export const patients = {
  list: (query: { q?: string; page?: number; per_page?: number }) =>
    api<Page<PatientRow>>('/staff/patients', { query }),
  summary: (id: Uuid) => api<Summary>(`${patient(id)}/summary`),
  record: (id: Uuid) => api<PatientRecord>(`${patient(id)}/record`),
  addVitals: (id: Uuid, values: Record<string, unknown>) =>
    api<DailyLog>(`${patient(id)}/daily-logs`, { method: 'POST', json: values }),
  correctDueDate: (id: Uuid, estimated_due_date: string, reason: string | null) =>
    api<Pregnancy>(`${patient(id)}/pregnancy/due-date`, { method: 'PUT', json: { estimated_due_date, reason } }),
  addNote: (id: Uuid, body: string) => api<void>(`${patient(id)}/notes`, { method: 'POST', json: { body } }),
  addTag: (id: Uuid, tag: string, note: string | null) =>
    api<void>(`${patient(id)}/risk-tags`, { method: 'POST', json: { tag, note } }),
  removeTag: (id: Uuid, tag: string) => api<void>(`${patient(id)}/risk-tags/${tag}`, { method: 'DELETE' }),
  approve: (id: Uuid, scope: string) => api<void>(`${patient(id)}/approvals`, { method: 'POST', json: { scope } }),
  revoke: (id: Uuid, scope: string) => api<void>(`${patient(id)}/approvals/${scope}`, { method: 'DELETE' }),
  fitnessVisit: (id: Uuid) => api<unknown>(`${patient(id)}/fitness-profile/specialist-visit`, { method: 'POST' }),
  rehabVisit: (id: Uuid) => api<unknown>(`${patient(id)}/rehab-profile/specialist-visit`, { method: 'POST' }),
  linkImaging: (id: Uuid, document_id: Uuid) =>
    api<unknown>(`${patient(id)}/rehab-profile/imaging`, { method: 'PUT', json: { document_id } }),
}

export const documents = {
  upload: (id: Uuid, form: FormData) =>
    api<MedicalDocument>(`${patient(id)}/documents`, { method: 'POST', form }),
  file: (id: Uuid, documentId: Uuid) => apiBlob(`${patient(id)}/documents/${documentId}/file`),
  remove: (id: Uuid, documentId: Uuid, reason: string | null) =>
    api<void>(`${patient(id)}/documents/${documentId}`, { method: 'DELETE', json: { reason } }),
}

export const alerts = {
  mine: () => api<{ items: Alert[] }>('/staff/alerts'),
  unassigned: () => api<{ items: Alert[] }>('/admin/unassigned-alerts'),
  seen: (alertId: Uuid) => api<void>(`/staff/alerts/${alertId}/seen`, { method: 'POST' }),
}

export interface NewStaff {
  mobile: string
  role: Role
  first_name: string
  last_name: string
  bio: string | null
  is_listed: boolean
}

export const staff = {
  list: () => api<{ items: StaffMember[] }>('/admin/staff'),
  create: (body: NewStaff) => api<StaffMember>('/admin/staff', { method: 'POST', json: body }),
  update: (userId: Uuid, changes: Partial<Omit<StaffMember, 'user_id' | 'role' | 'mobile'>>) =>
    api<StaffMember>(`/admin/staff/${userId}`, { method: 'PATCH', json: changes }),
}

