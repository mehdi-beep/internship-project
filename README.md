# BIMS — Bon d'Intervention Management System

Digital replacement for the company's paper-based intervention workflow. See [`project_specifications.md`](project_specifications.md) for the full SRS, [`TASKS.md`](TASKS.md) for the phased task breakdown, [`DATABASE_SCHEMA.md`](DATABASE_SCHEMA.md) for the data model, and [`API_SPEC.md`](API_SPEC.md) for the endpoint contracts.

**Status:** Phases 1–9 complete (Init, Database, Auth, Reference Data, Planning, Interventions, Business Logic, Approvals, Dashboards & Reporting). Phase 10 (Testing, Cleanup, Docs) is in progress — see [`TASKS.md`](TASKS.md) for the exact remaining items.

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
`tech01` / `Password123!`). This path is for local development and evaluation only —
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
alembic upgrade head          # applies full schema (14 tables, Phase 1 + Phase 2)
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

## Running on Railway

The backend deploys from `backend/Dockerfile`, which now ships working defaults so it
boots with **zero** Railway dashboard configuration — it points at the same pre-seeded
`backend/dev.db` used by the local [Quick Start](#quick-start-clone-and-run-immediately)
above. This section covers what to set, how to deploy, and how to verify it worked.

### Required environment variables

| Variable | Default (baked into the Dockerfile) | Should you change it? |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./dev.db` (resolves to `/app/dev.db`, since the container's working directory is `/app`) | Only if you want PostgreSQL instead — point it at a Railway-provisioned Postgres plugin's connection string (`postgresql+psycopg://...`) |
| `SECRET_KEY` | `dev-secret-key-not-for-production` | **Yes, before sharing the URL with anyone.** This repo is public — the default is visible to anyone who reads it, so anyone could forge valid login tokens against a deployment still using it. Set a real random value as a Railway service variable. |
| `CORS_ORIGINS` | `*` (allow any origin) | Yes, once your frontend has a real URL — set it to that exact origin (e.g. `https://your-frontend.up.railway.app`), since browsers reject `*` for credentialed requests (this API sends cookies/auth headers) |
| `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`, `UPLOAD_FOLDER`, `MAX_UPLOAD_SIZE`, `APP_NAME`, `DEBUG` | Same defaults as local dev (see `.env.example`) | Optional |

Set any of these as **Railway service variables** (Railway's dashboard → your service →
Variables) — they override the Dockerfile's `ENV` defaults automatically, no code or
image change needed.

### Deployment steps

1. In Railway, create a new service from this GitHub repo.
2. Set the service's **root directory** to `backend/` (Railway needs this since
   `Dockerfile` lives there, not at the repo root) — Railway will then auto-detect and
   build from `backend/Dockerfile`.
3. Set the service's exposed port to `8000` (matches the Dockerfile's `EXPOSE 8000` /
   the `uvicorn --port 8000` command).
4. Deploy. With no variables set at all, it will boot successfully using the SQLite
   defaults above.
5. Before sharing the deployment URL with anyone, set a real `SECRET_KEY` (see table
   above) and, once you know your frontend's deployed URL, a matching `CORS_ORIGINS`.

### SQLite on Railway — what works and what to know

Railway's container filesystem is **ephemeral by default**: local disk (including
`dev.db`) resets to whatever was committed in the image on every new deploy/restart.
Practically, this means:

- **Works as-is, no extra setup**: the pre-seeded demo data (technicians, clients,
  interventions, etc. — same dataset as local dev) is always there after every deploy,
  since it's baked into the image from the committed `backend/dev.db`. This is enough
  for demos, evaluation, and read-heavy exploration.
- **Does not persist across redeploys**: any *new* data written while the app is
  running (new users, new interventions, uploaded attachments) is lost the next time
  the service redeploys or restarts — the file reverts to its committed contents.
- **To make writes persistent**, attach a Railway **Volume** to the service and mount
  it at `/app` (Railway dashboard → your service → Volumes → Add Volume → mount path
  `/app`). Once mounted, `/app/dev.db` lives on the volume instead of the ephemeral
  container disk, so it survives redeploys like a normal database would. This is the
  smallest change that gets you real persistence without switching off SQLite; for a
  production deployment with concurrent users, PostgreSQL (via `DATABASE_URL`) remains
  the better fit.

### Verifying a successful deployment

1. Hit `https://<your-service>.up.railway.app/api/health` — expect:
   ```json
   {"success":true,"status":"ok","database_connected":true}
   ```
2. Confirm the seeded data is actually reachable (not just that the process is alive)
   by logging in:
   ```bash
   curl -X POST https://<your-service>.up.railway.app/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"tech01","password":"Password123!"}'
   ```
   A successful response includes an `access_token` — confirming both the app booted
   and the pre-seeded database is being read correctly.

## Running Tests

The backend has a permanent pytest suite (121 tests) covering authentication, business logic (duration/point calculation, status transitions), planning, interventions, approvals, reference-data CRUD, dashboards, reports, and technician performance:

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
10. Testing & Cleanup *(in progress)*

Business rules — for example ["cities are never typed manually"](project_specifications.md), ["interventions are never deleted"](project_specifications.md), or the point/duration formulas — are enforced **only** in `backend/app/services/`. The frontend displays data and calls the API; it never recalculates anything the backend already computed.

Git branching follows `main` (protected) ← `develop` ← `feature/*`, with PRs reviewed before merging into `develop`, per SRS Chapter 120–123.
