# Madare Emrooz · staff web panel

The web panel for the care team: midwives, doctors and admins. Mothers use the mobile app.
Vue 3 + TypeScript, Vite, Tailwind CSS 4 with daisyUI 5, Vue Router, Pinia and vue-i18n.
Persian (right to left, Persian digits, Jalali dates) is the default; English is one click away.

## What each role sees

| Role | Pages |
|---|---|
| Midwife | **Red alerts** from her mothers (mark as seen) · **Patients** (her mothers, search, paging) · each mother's record |
| Doctor | **Patients** (every mother in Phase 1) · each mother's record |
| Admin | **Unassigned mothers**: red alerts from mothers with no midwife yet · **Staff**: create, edit, list for mothers, deactivate |

A mother's record has a summary card (week, due date, midwife, red flags) and tabs:

- **Profile & history:** read-only, as she entered it in the app.
- **Pregnancy:** correct the due date, e.g. after an ultrasound.
- **Daily log:** her bleeding reports; the midwife records vitals and symptoms.
- **Documents:** the midwife uploads (JPEG/PNG/PDF up to 10 MB) and removes them; everyone can view them.
- **Fitness & rehab:** record specialist visits, link imaging (midwife), approve or revoke the plan (doctor).
- **Notes**.

What a role can't do isn't shown, and the backend enforces it anyway (403).

## Run it

Needs Node 20+ and the backend running (see `../backend/README.md`).

```bash
cd web-panel
npm install
cp .env.example .env      # VITE_BACKEND_URL: where the Flask backend runs (default http://localhost:5000)
npm run dev               # http://localhost:5173
```

The dev server proxies `/api` to the backend, so there is no CORS to configure. With
`SMS_BACKEND=console` on the backend, the sign-in code is printed in the backend's log.

## Build

```bash
npm run build             # type-checks, then writes dist/
```

`dist/` is static files. Serve them and the backend from the **same domain**, with `/api/` (and `/p/`,
the partner QR page) going to Flask and every other path falling back to `index.html` (the panel
uses HTML5 history routes such as `/patients/<id>`).

## Docker

`Dockerfile` builds the panel and serves it with nginx (`nginx.conf.template`). nginx also forwards
`/api/` and `/p/` to `BACKEND_URL` (default `http://backend:5000`), allows 12 MB uploads, sets
security headers, caches `/assets/` for a year and answers its own API errors (413, 502–504) in the
backend's JSON format. The root `docker-compose.yml` runs it on port 8080.

## Checks

```bash
npm test                  # Vitest: Jalali calendar, formatting, the API client's token renewal
npm run typecheck
```

## Code map

```text
src/
├── api/            client.ts (fetch, bearer token, one renewal on 401, ApiError) · endpoints.ts · types.ts
├── stores/         auth.ts (session: access token in memory, refresh token in localStorage) · toast.ts
├── i18n/           fa.ts, en.ts (same keys; fa is typed against en) · setLocale() switches dir and lang
├── utils/          jalali.ts (Gregorian ↔ Jalali) · format.ts (digits, dates, mobiles) · useFormat, useAsync, useAction
├── router/         routes with the roles allowed on each page
├── layouts/        AppShell.vue (side menu by role, alert count, language and theme switches)
├── views/          Login, Alerts (midwife and admin), Patients, Patient, Staff
└── components/     DateInput (Jalali day/month/year in Persian), ModalDialog, AsyncState, PaginationBar, patient/*
```

To add a text: put the key in `src/i18n/en.ts` and the same key in `fa.ts`; TypeScript reports a
missing translation.
