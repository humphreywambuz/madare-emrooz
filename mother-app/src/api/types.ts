// Shapes of the backend's JSON for the mother's own endpoints.
export type Role = 'user' | 'midwife' | 'doctor' | 'admin'
export type Uuid = string
export type IsoDate = string // 2026-10-01
export type IsoDateTime = string // 2026-10-01T09:30:00+03:30

export type JoinGoal = 'pregnancy' | 'fitness' | 'rehabilitation'
export type ReproductiveStatus = 'trying_to_conceive' | 'pregnant' | 'postpartum'
export type HomePath = 'pregnancy' | 'trying_to_conceive' | 'postpartum' | 'fitness' | 'rehabilitation'

export interface Tokens {
  token_type: 'Bearer'
  access_token: string
  expires_in: number
  refresh_token: string
  refresh_token_expires_at: IsoDateTime
  user: { id: Uuid; role: Role }
  is_new_user: boolean
}

export interface ProfileInput {
  first_name: string
  last_name: string
  join_goal: JoinGoal
  national_code: string | null
  birth_date: IsoDate | null
  height_cm: number | null
  initial_weight_kg: number | null
  mother_blood_type: string | null
  spouse_blood_type: string | null
  reproductive_status: ReproductiveStatus | null
}

export interface Profile extends ProfileInput {
  user_id: Uuid
  age: number | null
  rh_incompatibility_risk: boolean
  home: HomePath
}

export type MedicalHistory = Record<string, boolean | number | string | null>

export interface PregnancyInput {
  lmp_date: IsoDate
  conception_type: 'natural' | 'assisted'
  avg_cycle_length_days: number
  care_provider_type: string | null
  care_provider_name: string | null
}

export interface Pregnancy extends PregnancyInput {
  id: Uuid
  estimated_due_date: IsoDate
  gestational_week: number
  status: 'active' | 'delivered' | 'ended'
  due_date_source: 'lmp' | 'clinician'
  due_date_corrected_at: IsoDateTime | null
}

export interface DailyLog {
  id: Uuid
  recorded_by_id: Uuid
  recorded_at: IsoDateTime
  has_spotting_or_bleeding: boolean | null
  systolic_bp: number | null
  diastolic_bp: number | null
  blood_glucose_mg_dl: number | null
  weight_kg: number | null
  is_red_alert: boolean
}

export interface Midwife {
  id: Uuid
  first_name: string
  last_name: string
  bio: string | null
}

export interface PartnerLink {
  url: string
  token: string
  created_at: IsoDateTime
}

export interface FitnessProfile {
  goal: string
  goal_note: string | null
  specialist_visit_completed: boolean
  specialist_visit_at: IsoDateTime | null
  dashboard_unlocked: boolean
}

export type RehabAnswers = Record<string, string | number | boolean | null | undefined>

export interface RehabProfile extends Record<string, unknown> {
  subcategory: string
  pain_level: number
  specialist_visit_completed: boolean
  is_advanced_locked: boolean
}

export interface MedicalDocument {
  id: Uuid
  document_type: string
  original_filename: string
  content_type: string
  file_size_bytes: number
  created_at: IsoDateTime
  performed_at: IsoDateTime | null
  notes: string | null
}
