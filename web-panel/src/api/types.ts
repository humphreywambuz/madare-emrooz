// Shapes of the backend's JSON (backend/app/modules/*/api and application views).
export type Role = 'user' | 'midwife' | 'doctor' | 'admin'
export type Uuid = string
export type IsoDate = string // 2026-10-01
export type IsoDateTime = string // 2026-10-01T09:30:00+03:30

export interface Tokens {
  token_type: 'Bearer'
  access_token: string
  expires_in: number
  refresh_token: string
  refresh_token_expires_at: IsoDateTime
  user: { id: Uuid; role: Role }
  is_new_user: boolean
}

export interface StaffMember {
  user_id: Uuid
  role: Role
  mobile: string
  first_name: string | null
  last_name: string | null
  bio: string | null
  is_listed: boolean
  is_active: boolean
}

export interface PatientRow {
  id: Uuid
  mobile: string
  first_name: string | null
  last_name: string | null
  join_goal: string | null
  reproductive_status: string | null
  midwife_id: Uuid | null
  open_alerts: number
  last_alert_at: IsoDateTime | null
}

export interface Page<T> {
  items: T[]
  page: number
  per_page: number
  total: number
}

export interface Alert {
  id: Uuid
  kind: string
  created_at: IsoDateTime
  seen_at: IsoDateTime | null
  patient_id: Uuid
  patient_first_name: string | null
  patient_last_name: string | null
  patient_mobile: string
}

export interface RiskTag {
  tag: string
  source: 'record' | 'staff'
  note: string | null
  added_by_id: Uuid | null
}

export interface PatientHeader {
  id: Uuid
  mobile: string
  first_name: string | null
  last_name: string | null
  age: number | null
  join_goal: string | null
  reproductive_status: string | null
  gestational_week: number | null
  estimated_due_date: IsoDate | null
  midwife: { id: Uuid; first_name: string; last_name: string; bio: string | null } | null
}

export interface Summary {
  patient: PatientHeader
  risk_tags: RiskTag[]
}

export interface Pregnancy {
  id: Uuid
  lmp_date: IsoDate
  avg_cycle_length_days: number
  conception_type: string
  estimated_due_date: IsoDate
  gestational_week: number
  care_provider_type: string | null
  care_provider_name: string | null
  status: string
  due_date_source: 'lmp' | 'clinician'
  due_date_corrected_at: IsoDateTime | null
}

export interface DailyLog {
  id: Uuid
  patient_id: Uuid
  recorded_by_id: Uuid
  recorded_at: IsoDateTime
  pregnancy_id: Uuid | null
  has_spotting_or_bleeding: boolean | null
  systolic_bp: number | null
  diastolic_bp: number | null
  blood_glucose_mg_dl: number | null
  weight_kg: number | null
  has_acid_reflux: boolean | null
  has_blurred_vision: boolean | null
  has_headache: boolean | null
  has_palpitations: boolean | null
  has_heartburn: boolean | null
  has_reduced_fetal_movement: boolean | null
  other_complaints: string | null
  is_red_alert: boolean
}

export interface MedicalDocument {
  id: Uuid
  patient_id: Uuid
  uploaded_by_id: Uuid
  document_type: string
  original_filename: string
  content_type: string
  file_size_bytes: number
  created_at: IsoDateTime
  pregnancy_id: Uuid | null
  performed_at: IsoDateTime | null
  fundal_height_cm: number | null
  fetal_heart_rate_bpm: number | null
  notes: string | null
}

export interface Note {
  id: Uuid
  body: string
  created_at: IsoDateTime
  author_id: Uuid
  author_name: string | null
  author_role: Role
}

export interface Approval {
  id: Uuid
  scope: string
  approved_by_id: Uuid
  approved_at: IsoDateTime
  revoked_at: IsoDateTime | null
  revoked_by_id: Uuid | null
  is_active: boolean
}

export interface FitnessProfile {
  goal: string
  goal_note: string | null
  specialist_visit_completed: boolean
  specialist_visit_at: IsoDateTime | null
  dashboard_unlocked: boolean
}

export type RehabProfile = Record<string, unknown> & {
  subcategory: string
  pain_level: number
  had_related_surgery: boolean
  related_surgery_name: string | null
  uses_pain_medication: boolean
  imaging_document_id: Uuid | null
  specialist_visit_completed: boolean
  specialist_visit_at: IsoDateTime | null
  is_advanced_locked: boolean
}

export type Profile = Record<string, unknown> & {
  first_name: string
  last_name: string
  national_code: string | null
  birth_date: IsoDate | null
  age: number | null
  height_cm: number | null
  initial_weight_kg: number | null
  mother_blood_type: string | null
  spouse_blood_type: string | null
  join_goal: string
  reproductive_status: string | null
}

export interface PatientRecord {
  patient: PatientHeader
  risk_tags: RiskTag[]
  profile: Profile | null
  medical_history: Record<string, unknown> | null
  pregnancy: Pregnancy | null
  daily_logs: DailyLog[]
  documents: MedicalDocument[]
  fitness_profile: FitnessProfile | null
  rehab_profile: RehabProfile | null
  notes: Note[]
  approvals: Approval[]
}
