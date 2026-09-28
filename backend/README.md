# madare-emrooz backend

Flask + PostgreSQL backend. The Phase 1 (MVP) data model is documented in
[`docs/data-model.md`](docs/data-model.md).

## Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # adjust DATABASE_URL

createdb madare_emrooz
flask db upgrade       # create the schema
```

## Tests

The tests run against a real PostgreSQL database (`TEST_DATABASE_URL`):

```bash
createdb madare_emrooz_test
pytest
```

## Changing the schema

Edit the models in `app/models/`, then:

```bash
flask db migrate -m "describe the change"
flask db upgrade
```
