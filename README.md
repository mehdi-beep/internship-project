# BIMS — Bon d'Intervention Management System

Digital replacement for the company's paper-based intervention workflow. See [`project_specifications.md`](project_specifications.md) for the full SRS, [`TASKS.md`](TASKS.md) for the phased task breakdown, [`DATABASE_SCHEMA.md`](DATABASE_SCHEMA.md) for the data model, and [`API_SPEC.md`](API_SPEC.md) for the endpoint contracts.

**Status:** Phases 1–10 complete (Init, Database, Auth, Reference Data, Planning, Interventions, Business Logic, Approvals, Dashboards & Reporting, Testing & Cleanup). See [`TASKS.md`](TASKS.md) for the full phased breakdown.

## Tech Stack

- **Frontend:** React + TypeScript + Vite + Material UI + React Router + TanStack Query + Axios + React Hook Form + FullCalendar + Day.js
- **Backend:** Python 3 + FastAPI + SQLAlchemy + Alembic + Pydantic + JWT
- **Database:** PostgreSQL (production-like setup) — SQLite is also supported for local development/evaluation, via a pre-seeded `backend/dev.db` (see "Quick Start" below)

## Folder Structure

```
internship-project/
├── project_specifications.md   # source-of-truth SRS
├── TASKS.md                    # phased task breakdown
├── DATABASE_SCHEMA.md          # full data model
├── API_SPEC.md                 # endpoint contracts
├── docker-compose.yml          # Postgres (required) + backend/frontend (convenience)
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routers — HTTP only, no business logic
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # business logic (the only place calculations happen)
│   │   ├── repositories/   # database query layer
│   │   ├── authentication/ # password hashing, JWT
│   │   ├── middleware/     # auth dependency, role guards
│   │   ├── database/       # engine/session setup
│   │   ├── utils/
│   │   ├── uploads/        # uploaded attachments (gitignored)
│   │   └── static/
│   ├── alembic/             # migrations
│   ├── tests/               # pytest suite (see "Running Tests" below)
│   ├── main.py
│   ├── config.py
│   ├── dev.db               # pre-seeded SQLite database (see "Quick Start")
│   ├── run_dev_sqlite.py    # zero-setup launcher for the SQLite quick-start path
│   └── requirements.txt
└── frontend/
    └── src/
        ├── assets/ components/ pages/ layouts/ hooks/
        ├── services/ api/ context/ routes/ utils/ types/ styles/
        └── App.tsx
```

## Quick Start (clone and run immediately)

The repository ships with a pre-seeded SQLite database (`backend/dev.db`), so a fresh
clone can be running end-to-end in two commands per side — no Docker, no PostgreSQL,
no manual seed step.

```bash
# Backend
cd backend
python -m venv venv
./venv/Scripts/activate      # Windows — use `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
python run_dev_sqlite.py
```

`run_dev_sqlite.py` points the app at `sqlite:///./dev.db`, creates any missing tables
(a no-op against the committed schema), and starts the API — it does **not** re-seed or
reset data, since `dev.db` already contains the full synthetic dataset described below.

```bash
# Frontend (separate terminal)
cd frontend
npm install
cp .env.example .env
npm run dev
```

- App: http://localhost:5173
- API: http://localhost:8000/api
- Swagger docs: http://localhost:8000/docs

Log in with any of the [seeded credentials](#seeding-the-database) below (e.g.
`tech02` / `Password123!`). This path is for local development and evaluation only —
see "Running the Backend" and "Running the Database" further down for the
PostgreSQL-backed setup those sections describe.

## Environment Variables

**Backend** (`backend/.env`, copy from `backend/.env.example`):

| Variable | Description |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg://user:pass@host:5432/dbname` |
| `SECRET_KEY` | JWT signing secret — change in production |
| `JWT_ALGORITHM` | default `HS256` |
| `JWT_EXPIRE_MINUTES` | token lifetime |
| `UPLOAD_FOLDER` | attachment storage path |
| `MAX_UPLOAD_SIZE` | bytes, default 10 MB |
| `APP_NAME` | display name |
| `DEBUG` | `true`/`false` |
| `CORS_ORIGINS` | comma-separated allowed origins |

**Frontend** (`frontend/.env`, copy from `frontend/.env.example`):

| Variable | Description |
|---|---|
| `VITE_API_URL` | backend API base URL, e.g. `http://localhost:8000/api` |

Never commit `.env` files — only the `.env.example` templates are tracked.

## Running the Database

Requires Docker, or a local PostgreSQL 16 instance.

```bash
docker compose up -d db
```

This creates database `bims_db` with user `bims_user` / password `bims_password` on port 5432 (matches `.env.example`).

## Running the Backend

```bash
cd backend
python -m venv venv
./venv/Scripts/activate      # Windows
pip install -r requirements.txt
cp .env.example .env         # adjust if needed
alembic upgrade head          # applies full schema (15 tables, Phase 1 + Phase 2)
uvicorn main:app --reload
```

- API: http://localhost:8000/api
- Swagger docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

> Note: Python 3.14 was used during development. `requirements.txt` uses lower-bound version pins (`>=`) rather than exact pins so pip resolves prebuilt wheels compatible with whichever Python 3.10+ interpreter you run — exact-pinning is worth revisiting once the team standardizes on one Python version.

## Running the Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

App: http://localhost:5173

## Seeding the Database

> If you're using the SQLite quick-start above, `backend/dev.db` is already seeded —
> skip this section. It only applies to the PostgreSQL setup below.

After `alembic upgrade head` has created the schema, run:

```bash
cd backend
python -m app.database.seed
```

This populates the database with realistic synthetic data simulating several months of company activity: 10 technicians, 2 Chef des Techniciens, 2 Administration Supervisors, 20+ clients, 50+ client sites, 25+ contracts, 15+ projects, 100+ travaux catalog entries, 500+ interventions across every lifecycle status (including warranty interventions referencing real prior BI numbers), 200+ planning records, 300+ notifications, and full approval/audit history. See [`TASKS.md`](TASKS.md) Phase 2 for exact seeded counts.

The script is idempotent — re-running it against an already-seeded database is a no-op (it checks whether the `roles` table is empty first).

**Seeded login credentials** (all accounts): password `Password123!`
- Technicians: `tech01` … `tech10`
- Chef des Techniciens: `chef01`, `chef02`
- Administration Supervisors: `admin01`, `admin02`

## Running Everything via Docker Compose

```bash
docker compose up -d
```

Starts Postgres, backend (with hot reload), and frontend (with hot reload) together.

## Running Tests

The backend has a permanent pytest suite (127 tests) covering authentication, business logic (duration/point calculation, status transitions), planning, interventions, approvals, reference-data CRUD, dashboards, reports, and technician performance:

```bash
cd backend
pytest tests/
```

Each test spins up a fresh in-memory SQLite database via fixtures in `tests/conftest.py` and seeds it with the same `app.database.seed` logic used for real development data, so every test runs against realistic, fully isolated data rather than mocks. This makes the full run relatively slow (a few minutes) but each test independent of the others.

## Development Workflow

The project is built incrementally, one phase at a time, per [`TASKS.md`](TASKS.md):

1. Project Initialization *(done)*
2. Database (schema, models, migrations, synthetic data) *(done)*
3. Authentication *(done)*
4. Reference Data CRUD (Users, Clients, Sites, Contracts, Projects, Travaux) *(done)*
5. Planning Module *(done)*
6. Intervention Module *(done)*
7. Business Logic (duration, points, warranty, status transitions) *(done)*
8. Approval Workflow *(done)*
9. Dashboards & Reporting *(done)*
10. Testing & Cleanup *(done)*

Business rules — for example ["cities are never typed manually"](project_specifications.md), ["interventions are never deleted"](project_specifications.md), or the point/duration formulas — are enforced **only** in `backend/app/services/`. The frontend displays data and calls the API; it never recalculates anything the backend already computed.

Git branching follows `main` (protected) ← `develop` ← `feature/*`, with PRs reviewed before merging into `develop`, per SRS Chapter 120–123.
