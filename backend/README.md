# madare-emrooz backend

Flask + PostgreSQL backend.

- [`docs/architecture.md`](docs/architecture.md): how the code is organised (modular monolith with
  clean architecture layers) and how to add a feature.
- [`docs/data-model.md`](docs/data-model.md) and [`docs/erd.svg`](docs/erd.svg): the Phase 1 (MVP)
  data model and entity-relationship diagram.
- [`docs/proposal-review.md`](docs/proposal-review.md): what the product proposal asks for, how the
  backend maps onto it, and the open questions.

## Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # adjust DATABASE_URL; for real SMS set KAVENEGAR_API_KEY and SMS_BACKEND=kavenegar

createdb madare_emrooz
flask db upgrade       # create the schema
flask create-admin 09121234567 --first-name Ali --last-name Ahmadi   # first admin
```

The admin signs in with an SMS code and creates the doctors and midwives in the staff panel
(`POST /api/v1/admin/staff`). Mothers then choose their midwife in the app.

## Tests

The tests run against a real PostgreSQL database (`TEST_DATABASE_URL`):

```bash
createdb madare_emrooz_test
pytest
```

## Changing the schema

Edit the models in `app/modules/<module>/infrastructure/models.py`, then:

```bash
flask db migrate -m "describe the change"
flask db upgrade
python scripts/generate_erd.py   # refresh docs/erd.svg
```
