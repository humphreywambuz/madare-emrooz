# Phase 1 (MVP) data model

This is the database schema for Phase 1 of the maternal & child health platform. It is based on
`دیتامدل فاز 1 .docx` in this folder. The code lives in `backend/app/modules/` (Flask-SQLAlchemy,
PostgreSQL), and the schema is created by the Alembic migration in `backend/migrations/`.

## Mapping from the specification

| # | Section of the spec | Table(s) | Module (`app/modules/…`) |
|---|---|---|---|
| 1 | User auth & role | `users`, `otp_codes`, `user_sessions` | `identity` |
| 2 | Base demographic profile | `profiles` | `profiles` |
| 3 | Medical & midwifery history | `medical_histories` | `profiles` |
| 4 | Pregnancy path (+ partner QR code) | `pregnancies`, `partner_links` | `pregnancy` |
| 5 | Daily monitoring & symptoms | `daily_logs` (+ `alerts`) | `monitoring` |
| 6 | Medical documents | `medical_documents`, `document_files` | `documents` |
| 7 | Medical staff panel | `staff_profiles`, `care_assignments`, `alerts`, `risk_tag_assignments`, `staff_notes`, `care_approvals` | `care_team` |
| 8 | Audit log | `audit_logs` | `audit` |
| 9 | Fitness & daily sport path (option B) | `fitness_profiles` (+ `profiles`) | `fitness` |
| 10 | Rehabilitation health profile (option C) | `rehab_profiles` | `rehabilitation` |
| 11 | Rehabilitation access control | `rehab_profiles.specialist_visit_*` + `care_approvals` | `rehabilitation` (`domain/policies.py`) |

Each module keeps its ORM models in `infrastructure/models.py` (classes end in `Model`, e.g.
`PregnancyModel`) and its enums and business rules in `domain/`. See
[architecture.md](architecture.md).

## Entity-relationship diagram

![Phase 1 entity-relationship diagram](erd.svg)

The diagram is generated from the models. After changing a model, regenerate it from the `backend`
directory:

```bash
python scripts/generate_erd.py
```

## Tables

### 1. `users`, `otp_codes`, `user_sessions`
- `users.mobile` is unique and stored as an Iranian mobile in international form: `+98` followed by
  10 digits starting with 9 (`+989121234567`). A CHECK constraint on `users.mobile` and
  `otp_codes.mobile` enforces this, so a number in local form (`0912…`) or from another country can't
  be saved even if the app has a bug. The pattern is defined once, in
  `identity/domain/mobile.py` (`IRANIAN_MOBILE_PATTERN`).
- `users.role` is one of `user`, `doctor`, `midwife` or `admin`. Access level follows from the role.
- `otp_codes` is keyed by mobile number, because the user may not exist before their first login.
  It stores only a **hash** of the code, together with its expiry, the number of attempts, when
  it was used, and the IP address that requested it (`request_ip`, used to limit how many codes
  one network can request).
- `user_sessions` holds one row per logged-in device (session management), with a hashed refresh
  token and `revoked_at` for logout.

### 2. `profiles` (one per user)
- Name, national code (10 digits with a valid check digit, unique), height, initial weight, her
  blood type and her spouse's (`father_blood_type`, shown as `spouse_blood_type` in the API),
  reproductive status (`trying_to_conceive` / `pregnant` / `postpartum`) and join goal
  (`pregnancy` / `fitness` / `rehabilitation`).
- The app's home screen follows from `join_goal` and `reproductive_status`: pregnant → pregnancy
  dashboard; trying to conceive → a simple page until later phases; postpartum → the fitness and
  postpartum rehabilitation paths. Ending a pregnancy as delivered sets her status to postpartum.
- **Age is stored as `birth_date`.** A stored age would go out of date; `profiles.domain.rules.age_on` calculates it.
- The father's blood type is kept for Rh incompatibility checks. See
  `profiles.domain.rules.rh_incompatibility_risk`.

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
  (`pregnancy.domain.entities.calculate_due_date`). It is stored so a clinician can correct it, for example from
  an ultrasound.
- **The gestational week is not stored** because it changes every day.
  The `Pregnancy` domain entity calculates it from the due date (`gestational_week()`).
- `partner_links`: the QR code her spouse scans to see the week and due date, without signing in.
  Only the link's id is stored; the token in the code is that id plus an HMAC keyed with
  `SECRET_KEY`. One active link per mother (partial unique index); turning it off or making a new
  one sets `revoked_at`. The link also stops working when the pregnancy ends.

### 5. `daily_logs`
- Each entry records who entered it (`recorded_by_id`): the mother (only spotting or bleeding, during
  a pregnancy) or her midwife (blood pressure, glucose, weight, symptoms).
- A bleeding report also creates an `alerts` row in the same transaction (see section 7).
- `is_red_alert` is a PostgreSQL **generated column**, currently `true` whenever bleeding is
  reported, so it always matches the data. A partial index makes alert lookups fast. More
  alert rules (e.g. BP ≥ 140/90) can be added by changing the expression in a migration.
- Vital signs have range CHECK constraints to catch typing mistakes.

### 6. `medical_documents`
- Only the mother's midwife uploads. The file itself (JPEG, PNG or PDF, at most 10 MB, recognised
  from its first bytes) is stored in PostgreSQL in `document_files`, kept apart from
  `medical_documents` so listing documents doesn't read the files. The row stores the original file
  name, type, size and `storage_key` (`db:<id>`).
- `document_type` is one of blood, urine, thyroid, ultrasound, screening, imaging (radiology/MRI)
  or other. The row also records when the test was done (`performed_at`), fundal height and fetal
  heart rate.

### 7. Staff panel: `staff_profiles`, `care_assignments`, `alerts`, `risk_tag_assignments`, `staff_notes`, `care_approvals`
- `staff_profiles`: name and bio of a doctor, midwife or admin (the account itself is in `users`).
  Admins create staff; `is_listed` midwives appear in the app for mothers to choose from.
- `care_assignments`: the midwife each mother chose. Changing midwife ends the old row
  (`ended_at`), so the history is kept; a partial unique index allows one active assignment per
  mother and `care_role`. The `doctor` role is there for Phase 2, when mothers choose their
  gynecologist and doctors see only their own patients.
- `alerts`: red alerts (Phase 1: bleeding). An alert goes to the mother's current midwife, or to
  the admins' "unassigned mothers" list while she has none, until someone marks it as seen.
- **Summary card**: tags that follow from her record (RhoGAM, miscarriages, diabetes, blood
  pressure, thyroid, infections) are worked out when the card is shown. Staff can add others; each
  added tag is a `risk_tag_assignments` row, unique per patient, recording who added it.
- **Staff notes**: free-text notes and interventions by a doctor or midwife.
- **Approval checkmark**: `care_approvals` rows with a `scope`. Revoking one sets `revoked_at`
  instead of deleting it, so the history is kept. A partial unique index allows only one active
  approval per patient and scope. Only doctors approve (checked by the
  care team service).

### 8. `audit_logs`
- Append-only, with a `BIGINT` identity key. It records the actor, the patient, the event type
  (`profile_created`, `record_viewed`, `access_denied`, …), the resource, the IP address and a
  JSONB `details` field.
- `actor_id` and `patient_id` intentionally have **no foreign keys**. Audit rows have to outlive
  the records they describe and must never block a delete. `actor_id` is nullable so failed,
  anonymous access attempts can be logged.

### 9. `fitness_profiles`
- The quick sign-up reuses `users.mobile` and `profiles` (name, birth date, height, weight). This
  table adds the fitness goal (`weight_loss`, `muscle_gain`, `general_fitness`, `other`) and her
  explanation of it (`goal_note`).
- `specialist_visit_completed` / `specialist_visit_at`: the fitness dashboard opens after a
  specialist visit, which staff record.

### 10. `rehab_profiles` (one per user)
- Common fields: sub-category, pain level (1–10, enforced by a CHECK), related surgery in the last
  5 years with its name (the name is required when the answer is yes, enforced by a CHECK) and
  pain-medication use.
- The fields specific to each sub-category are nullable columns grouped in the model: injury
  correction, postpartum recovery, performance/yoga and orthopedic referral. For an orthopedic
  referral, the imaging file (radiology/MRI) is a normal `medical_documents` row, uploaded by her
  midwife, that `imaging_document_id` points to.
- Only the questions of the chosen sub-category may be answered; the others must stay empty
  (checked in `rehabilitation/domain/entities.py`).

### 11. Rehabilitation access control
- `rehab_profiles.specialist_visit_completed` / `specialist_visit_at` record the visit.
- `rehabilitation.domain.policies.is_advanced_locked` stays **true** until the visit has happened **and** there is
  an active `care_approvals` row with scope `rehabilitation_plan`. Because it is calculated rather
  than stored, the lock cannot disagree with the approval history.

## Conventions
- Primary keys are UUIDs (`gen_random_uuid()`), except `audit_logs`, which uses a `BIGINT`
  identity for fast inserts.
- Every table has `created_at`, and mutable tables also have `updated_at` (`timestamptz`).
- Enums are stored as `VARCHAR` with a named CHECK constraint (`ck_<table>_<column>_valid`)
  instead of native PostgreSQL `ENUM` types, so adding a value is a simple migration. The values
  are defined in each module's `domain/enums.py`.
- All constraints follow a naming convention (`app/extensions.py`), so Alembic migrations stay
  predictable.
- Patient-owned data uses `ON DELETE CASCADE` to its patient. References to staff members
  (`recorded_by_id`, `approved_by_id`, …) use the default `RESTRICT`, so staff accounts should be
  deactivated (`is_active = false`) rather than deleted.
- `tests/test_data_rules.py` checks the data rules and delete behaviour listed in the Phase 1 data
  dictionary against PostgreSQL:
  - deleting a mother removes all her data but keeps `audit_logs`;
  - staff with records can't be deleted;
  - deleting a pregnancy or document clears the links to it;
  - only `+98` mobiles are stored.

## Redis
Phase 1 does not need Redis to store any data. If load grows, it is a good fit for OTP send rate
limits and brute-force counters, and for caching revoked session IDs. PostgreSQL
remains the source of truth for everything in this document.

## Out of scope for Phase 1
AI features, service booking, wallet and advanced triage, as stated in the spec.
