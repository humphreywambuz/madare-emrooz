# Phase 1 (MVP) data model

This is the database schema for Phase 1 of the maternal & child health platform. It is based on
`دیتامدل فاز 1 .docx` in this folder. The code lives in `backend/app/models/` (Flask-SQLAlchemy,
PostgreSQL), and the schema is created by the Alembic migration in `backend/migrations/`.

## Mapping from the specification

| # | Section of the spec | Table(s) | Model |
|---|---|---|---|
| 1 | User auth & role | `users`, `otp_codes`, `user_sessions` | `User`, `OtpCode`, `UserSession` |
| 2 | Base demographic profile | `profiles` | `Profile` |
| 3 | Medical & midwifery history | `medical_histories` | `MedicalHistory` |
| 4 | Pregnancy path | `pregnancies` | `Pregnancy` |
| 5 | Daily monitoring & symptoms | `daily_logs` | `DailyLog` |
| 6 | Medical documents | `medical_documents` | `MedicalDocument` |
| 7 | Medical staff panel | `risk_tag_assignments`, `staff_notes`, `care_approvals` | `RiskTagAssignment`, `StaffNote`, `CareApproval` |
| 8 | Audit log | `audit_logs` | `AuditLog` |
| 9 | Fitness & daily sport path (option B) | `fitness_profiles` (+ `profiles`) | `FitnessProfile` |
| 10 | Rehabilitation health profile (option C) | `rehab_profiles` | `RehabProfile` |
| 11 | Rehabilitation access control | `rehab_profiles.specialist_visit_*` + `care_approvals` | `RehabProfile.is_advanced_locked` |

## Entity-relationship diagram

```mermaid
erDiagram
    users ||--o{ otp_codes : "by mobile (no FK)"
    users ||--o{ user_sessions : has
    users ||--o| profiles : has
    users ||--o| medical_histories : has
    users ||--o| fitness_profiles : has
    users ||--o| rehab_profiles : has
    users ||--o{ pregnancies : has
    users ||--o{ daily_logs : "patient / recorded_by"
    pregnancies |o--o{ daily_logs : groups
    users ||--o{ medical_documents : "patient / uploaded_by"
    pregnancies |o--o{ medical_documents : groups
    medical_documents |o--o| rehab_profiles : "orthopedic imaging"
    users ||--o{ risk_tag_assignments : "patient / added_by"
    users ||--o{ staff_notes : "patient / author"
    users ||--o{ care_approvals : "patient / approved_by"
    users ||--o{ audit_logs : "actor / patient (no FK)"

    users {
        uuid id PK
        varchar mobile UK "E.164"
        varchar role "user|doctor|midwife|admin"
        bool is_active
        timestamptz mobile_verified_at
        timestamptz last_login_at
    }
    otp_codes {
        uuid id PK
        varchar mobile
        varchar code_hash
        timestamptz expires_at
        smallint attempts
        timestamptz consumed_at
    }
    user_sessions {
        uuid id PK
        uuid user_id FK
        varchar refresh_token_hash UK
        inet ip_address
        timestamptz expires_at
        timestamptz revoked_at
    }
    profiles {
        uuid user_id PK,FK
        varchar first_name
        varchar last_name
        varchar national_code UK
        date birth_date
        numeric height_cm
        numeric initial_weight_kg
        varchar mother_blood_type
        varchar father_blood_type
        varchar reproductive_status
        varchar join_goal
    }
    medical_histories {
        uuid user_id PK,FK
        smallint previous_children_count
        smallint miscarriage_count
        bool has_diabetes
        bool has_hypertension
        text underlying_conditions "and ~20 more, see model"
    }
    pregnancies {
        uuid id PK
        uuid user_id FK
        date lmp_date
        smallint avg_cycle_length_days
        varchar conception_type
        date estimated_due_date
        varchar care_provider_type
        varchar status "one active per user"
    }
    daily_logs {
        uuid id PK
        uuid patient_id FK
        uuid pregnancy_id FK
        uuid recorded_by_id FK
        timestamptz recorded_at
        bool has_spotting_or_bleeding
        smallint systolic_bp
        smallint diastolic_bp
        smallint blood_glucose_mg_dl
        numeric weight_kg
        bool is_red_alert "generated"
    }
    medical_documents {
        uuid id PK
        uuid patient_id FK
        uuid uploaded_by_id FK
        uuid pregnancy_id FK
        varchar document_type
        varchar storage_key UK
        timestamptz performed_at
        numeric fundal_height_cm
        smallint fetal_heart_rate_bpm
    }
    risk_tag_assignments {
        uuid id PK
        uuid patient_id FK
        varchar tag "unique per patient"
        uuid added_by_id FK
    }
    staff_notes {
        uuid id PK
        uuid patient_id FK
        uuid author_id FK
        text body
    }
    care_approvals {
        uuid id PK
        uuid patient_id FK
        uuid approved_by_id FK
        varchar scope "pregnancy_plan|rehabilitation_plan"
        timestamptz approved_at
        timestamptz revoked_at
    }
    fitness_profiles {
        uuid user_id PK,FK
        varchar goal
        text goal_note
    }
    rehab_profiles {
        uuid user_id PK,FK
        varchar subcategory
        smallint pain_level "1..10"
        bool had_related_surgery
        varchar related_surgery_name
        bool uses_pain_medication
        uuid imaging_document_id FK
        bool specialist_visit_completed
    }
    audit_logs {
        bigint id PK
        uuid actor_id
        uuid patient_id
        varchar event_type
        varchar resource_type
        varchar resource_id
        inet ip_address
        jsonb details
        timestamptz created_at
    }
```

## Tables

### 1. `users`, `otp_codes`, `user_sessions`
- `users.mobile` is unique and stored in E.164 format (`+989121234567`), which a CHECK constraint
  enforces.
- `users.role` is one of `user`, `doctor`, `midwife` or `admin`. Access level follows from the role.
- `otp_codes` is keyed by mobile number, because the user may not exist before their first login.
  It stores only a **hash** of the code, together with its expiry, the number of attempts and when
  it was used.
- `user_sessions` holds one row per logged-in device (session management), with a hashed refresh
  token and `revoked_at` for logout.

### 2. `profiles` (one per user)
- Name, national code (10 digits, unique), height, initial weight, both parents' blood types,
  reproductive status (`trying_to_conceive` / `pregnant` / `postpartum`) and join goal
  (`pregnancy` / `fitness` / `rehabilitation`).
- **Age is stored as `birth_date`.** A stored age would go out of date; `Profile.age` calculates it.
- The father's blood type is kept for Rh incompatibility checks. See
  `Profile.rh_incompatibility_risk`.

### 3. `medical_histories` (one per user)
- Covers every item in the spec: children and miscarriage counts, diabetes, hypertension,
  nutrient deficiencies (with names), thyroid problems, breast cyst, PCOS, underlying conditions,
  surgery and anesthesia, medications, dental infections, HIV and hepatitis B/C, and the
  spouse's health.
- Yes/no answers are **nullable booleans**: `NULL` means "not answered", which is different
  from "no".

### 4. `pregnancies`
- A user can have several pregnancies over time, but a partial unique index allows **only one
  with `status = 'active'`**.
- `estimated_due_date` is calculated from LMP with Naegele's rule, adjusted for cycle length
  (`Pregnancy.calculate_due_date`). It is stored so a clinician can correct it, for example from
  an ultrasound.
- **The gestational week is not stored** because it changes every day.
  `Pregnancy.gestational_week()` calculates it from the due date.

### 5. `daily_logs`
- Each entry records who entered it (`recorded_by_id`): the patient (e.g. spotting or bleeding)
  or a midwife (blood pressure, glucose, weight, symptoms).
- `is_red_alert` is a PostgreSQL **generated column**, currently `true` whenever bleeding is
  reported, so it always matches the data. A partial index makes alert lookups fast. More
  alert rules (e.g. BP ≥ 140/90) can be added by changing the expression in a migration.
- Vital signs have range CHECK constraints to catch typing mistakes.

### 6. `medical_documents`
- The file is kept in file or object storage; the row stores the `storage_key`, original file name,
  MIME type and size.
- `document_type` is one of blood, urine, thyroid, ultrasound, screening, imaging (radiology/MRI)
  or other. The row also records when the test was done (`performed_at`), fundal height and fetal
  heart rate.

### 7. Staff panel: `risk_tag_assignments`, `staff_notes`, `care_approvals`
- **Summary card**: each risk tag is a row (`needs_rhogam`, `thyroid`, `miscarriage_history`, …),
  unique per patient, and records which staff member added it.
- **Staff notes**: free-text notes and interventions by a doctor or midwife.
- **Approval checkmark**: `care_approvals` rows with a `scope`. Revoking one sets `revoked_at`
  instead of deleting it, so the history is kept. A partial unique index allows only one active
  approval per patient and scope. Checking that the approver is a doctor is left to the service
  layer.

### 8. `audit_logs`
- Append-only, with a `BIGINT` identity key. It records the actor, the patient, the event type
  (`profile_created`, `record_viewed`, `access_denied`, …), the resource, the IP address and a
  JSONB `details` field.
- `actor_id` and `patient_id` intentionally have **no foreign keys**. Audit rows have to outlive
  the records they describe and must never block a delete. `actor_id` is nullable so failed,
  anonymous access attempts can be logged.

### 9. `fitness_profiles`
- The quick sign-up reuses `users.mobile` and `profiles` (name, birth date, height, weight). This
  table only adds the fitness goal (`weight_loss`, `muscle_gain`, `general_fitness`, `other`).

### 10. `rehab_profiles` (one per user)
- Common fields: sub-category, pain level (1–10, enforced by a CHECK), related surgery in the last
  5 years with its name (the name is required when the answer is yes, enforced by a CHECK) and
  pain-medication use.
- The fields specific to each sub-category are nullable columns grouped in the model: injury
  correction, postpartum recovery, performance/yoga and orthopedic referral. For an orthopedic
  referral, the imaging file (radiology/MRI) is a normal `medical_documents` row that
  `imaging_document_id` points to.

### 11. Rehabilitation access control
- `rehab_profiles.specialist_visit_completed` / `specialist_visit_at` record the visit.
- `RehabProfile.is_advanced_locked` stays **true** until the visit has happened **and** there is
  an active `care_approvals` row with scope `rehabilitation_plan`. Because it is calculated rather
  than stored, the lock cannot disagree with the approval history.

## Conventions
- Primary keys are UUIDs (`gen_random_uuid()`), except `audit_logs`, which uses a `BIGINT`
  identity for fast inserts.
- Every table has `created_at`, and mutable tables also have `updated_at` (`timestamptz`).
- Enums are stored as `VARCHAR` with a named CHECK constraint (`ck_<table>_<column>_valid`)
  instead of native PostgreSQL `ENUM` types, so adding a value is a simple migration. The values
  are defined in `app/models/enums.py`.
- All constraints follow a naming convention (`app/extensions.py`), so Alembic migrations stay
  predictable.
- Patient-owned data uses `ON DELETE CASCADE` to its patient. References to staff members
  (`recorded_by_id`, `approved_by_id`, …) use the default `RESTRICT`, so staff accounts should be
  deactivated (`is_active = false`) rather than deleted.

## Redis
Phase 1 does not need Redis to store any data. When the auth endpoints are built, it is a good fit
for OTP send rate limits and brute-force counters, and for caching revoked session IDs. PostgreSQL
remains the source of truth for everything in this document.

## Out of scope for Phase 1
AI features, service booking, wallet and advanced triage, as stated in the spec.
