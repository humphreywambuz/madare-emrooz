# Madare Emrooz: mothers' web app

The mother-facing web app: sign in with an SMS code, choose a goal, and follow the pregnancy, fitness
or rehabilitation path. It is built for phones, in Persian, and uses the same backend API as the
mobile app. Staff accounts cannot sign in here; they use the [care team panel](../web-panel/README.md).

## Screens

| Screen | Route | What she does |
|---|---|---|
| Sign in | `/login` | Mobile number, then the 6-digit SMS code. A new number creates her account. |
| Welcome | `/welcome` | A new mother chooses her goal and fills in her profile. |
| Home | `/` | The home screen the backend chose for her (`profile.home`), see below. |
| My midwife | `/midwife` | Her midwife, and the list to choose from. |
| Documents | `/documents` | Test results and scans her midwife uploaded. |
| Me | `/me` | Her profile summary, dark mode, sign out. |
| Profile | `/profile` | Change her goal, details or status. |
| Pregnancy details | `/pregnancy` | Record a pregnancy, correct its details, or record its end. |
| Medical history | `/history` | Every question is optional; unanswered is saved as empty, not "no". |
| Partner code | `/partner` | The QR code her spouse scans to see the week and due date. |
| Fitness / Rehabilitation | `/fitness`, `/rehab` | Her fitness goal; the rehabilitation questionnaire. |

Home screens (`src/views/home/`):

- **Pregnancy:** her own pregnancy wheel, the due date, the daily bleeding question, the latest vitals
  her midwife recorded, and links to the pages above. Answering "yes" to bleeding raises a red alert
  for her midwife (or for the admins while she has none) and shows the emergency number 115.
- **Trying to conceive:** a simple page until that phase's features exist.
- **Postpartum:** the two paths open to her, rehabilitation and fitness.
- **Fitness / Rehabilitation:** her answers and the steps still ahead (specialist visit, approval).

## Run it

Requires Node 20+ and the backend running.

```bash
npm install
cp .env.example .env              # VITE_BACKEND_URL=http://localhost:5000
npm run dev -- --port 5174        # proxies /api and /p/ to the backend
```

With `docker compose up -d --build` from the repository root it is served at <http://localhost:8081>.

`npm run build` type-checks and builds into `dist/`. There are no unit tests yet.

## Code map

| Path | What is there |
|---|---|
| `src/api/` | `client.ts` (fetch wrapper, token renewal), `endpoints.ts` (one function per endpoint), `types.ts` |
| `src/stores/auth.ts` | The session and her profile |
| `src/router/` | Routes; a mother without a profile is sent to `/welcome` |
| `src/layouts/` | `AppShell` (bottom navigation) and `PageShell` (back button and title) |
| `src/views/` | One file per screen |
| `src/utils/use*.ts` | The logic of each form and screen |
| `src/i18n/fa.ts` | Every text. Add a language by adding its messages in `src/i18n/index.ts`. |

`client.ts`, the Jalali and formatting utilities, the theme (`src/style.css`) and a few components
(`GestationWheel`, `DateInput`, `ModalDialog`, …) are copies of the panel's. Change both when you
change one.
