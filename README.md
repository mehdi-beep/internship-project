# BIMS — Bon d'Intervention Management System

Digital replacement for the company's paper-based intervention workflow. See [`project_specifications.md`](project_specifications.md) for the full SRS, [`TASKS.md`](TASKS.md) for the phased task breakdown, [`DATABASE_SCHEMA.md`](DATABASE_SCHEMA.md) for the data model, and [`API_SPEC.md`](API_SPEC.md) for the endpoint contracts.

**Status:** Phases 1–10 complete (Init, Database, Auth, Reference Data, Planning, Interventions, Business Logic, Approvals, Dashboards & Reporting, Testing & Cleanup), plus three post-launch tasks: configurable search/filters (Task 1), Administrator-configurable point rules (Task 2), and a read-only hallway-display role with a live-updating global calendar (Task 3). See [`TASKS.md`](TASKS.md) for the full phased breakdown.

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
`tech02` / `Password123!`, or `display01` / `Password123!` for the read-only
hallway-calendar role — see [Task 3](#task-3-display-role-live-global-calendar)).
This path is for local development and evaluation only —
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

This populates the database with realistic synthetic data simulating several months of company activity: 10 technicians, 2 Chef des Techniciens, 2 Administration Supervisors, 1 read-only Display account (Task 3), 20+ clients, 50+ client sites, 25+ contracts, 15+ projects, 100+ travaux catalog entries, 500+ interventions across every lifecycle status (including warranty interventions referencing real prior BI numbers), 200+ planning records, 300+ notifications, 3 default point rules (Task 2 — see below), and full approval/audit history. See [`TASKS.md`](TASKS.md) Phase 2 for exact seeded counts.

The script is idempotent — re-running it against an already-seeded database is a no-op (it checks whether the `roles` table is empty first).

**Seeded login credentials** (all accounts): password `Password123!`
- Technicians: `tech01` … `tech10`
- Chef des Techniciens: `chef01`, `chef02`
- Administration Supervisors: `admin01`, `admin02`
- Display (read-only hallway calendar, Task 3): `display01`

## Running Everything via Docker Compose

```bash
docker compose up -d
```

Starts Postgres, backend (with hot reload), and frontend (with hot reload) together.

## Running Tests

The backend has a permanent pytest suite (211 tests) covering authentication, business logic (duration/point calculation, status transitions), planning, interventions, approvals, reference-data CRUD, dashboards, reports, technician performance, configurable point rules (Task 2), and the read-only display role (Task 3):

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

## Post-Launch Tasks

Three follow-on tasks were implemented after the original 10-phase plan above, each scoped and delivered independently:

### Task 1 — Search and Relevant Filters

Every list page's search bar now has entity-appropriate filters (not one generic set): Client Sites gained a City filter, Contracts/Projects gained start-date ranges, Travaux gained a Category filter, and Interventions gained Technician (Chef/Admin only — a technician's own list already has exactly one technician in it), City, Type, Contract, and Project filters — all combinable with search, pagination, and existing role restrictions. No new tables; a handful of existing list endpoints gained new optional query parameters.

### Task 2 — Administrator Point Rules

The Ch.28 point-award windows (`17:00–19:00 → +5`, etc.) were previously hardcoded in `business_logic_service.calculate_points()`. They're now stored in a new `point_rules` table (`start_time`, `end_time`, `points`, `active`) managed through a new **Point Management** section in the Administrator UI (create/edit/deactivate/delete, no cap on how many rules can exist, midnight-crossing windows and overlap-conflict validation both handled explicitly). `calculate_points()` reads the active rules from the database instead of an `if/elif` chain; every dashboard/KPI/report continues to read the already-stored `interventions.points_earned` column exactly as before, so **editing or deleting a rule never changes any intervention's already-awarded points** — only future submissions are affected.

- Migration: `backend/alembic/versions/5b327e8d21a6_add_point_rules_table.py`
- New endpoints: `GET/POST/PUT/PATCH/DELETE /api/point-rules` (Administrator-only)
- Seeded defaults reproduce the original spec exactly; see [`SYNTHETIC_DATABASE.md`](SYNTHETIC_DATABASE.md)

### Task 3 — Display Role & Live Global Calendar

A 4th role, `display`, was added for a dedicated, strictly read-only hallway-screen account (seeded as `display01`) that can log in and see one thing: a full-screen, auto-refreshing global planning calendar (`/display-calendar`, no sidebar/top bar). It has no access to any other endpoint anywhere in the API — every existing role-restricted router was left untouched; the only new surface is one purpose-built endpoint, `GET /api/planning/display`, reachable by `display`/`chef_technicien`/`admin_supervisor`, that returns planning entries with technician/client/site names already resolved server-side (no separate `/clients` or `/users` lookup needed).

Live updates use **controlled polling** (TanStack Query's `refetchInterval`, the same mechanism already used for the notification badge) at a 20-second interval — this codebase has no WebSocket or Server-Sent-Events infrastructure anywhere, and polling was the least-invasive mechanism that satisfied "no manual refresh required" without introducing new infrastructure for one screen.

- Migration: `backend/alembic/versions/2c9527c79999_add_display_role.py` (extends the PostgreSQL `role_name` enum; a no-op on SQLite, which has no native enum type)
- Existing Technician/Chef/Admin calendars (`PlanningPage.tsx`, the technician calendar) were not touched

### Task 4 — Assigned Intervention Notifications

When an Administrator or Chef des Techniciens assigns a planned intervention, **only the assigned technician** is notified — never all technicians. This covers both urgent and normal assignments, plus reassignment (the newly-assigned technician gets a full assignment notification; the previous one is told it's no longer theirs).

Notifications now carry the client, site/city, planned date and time, and priority, and clicking one still deep-links the technician into that specific assignment.

This extends the **existing** notification system (the `notifications` table and `notification_service`) rather than adding a second one. On top of the in-app notification, a new `delivery_service` fans the same content out to two **optional** channels:

- **Email (SMTP)** — including Gmail (requires a Google App Password)
- **WhatsApp** — via the Meta WhatsApp Cloud API (requires a Meta Business account and an approved message template)

Both are **disabled by default and configured entirely through environment variables** — no credentials are hardcoded. The application is fully functional with neither configured, and an unreachable or misconfigured provider never fails the assignment that triggered the notification (covered by tests that point the app at a dead host and assert the assignment still succeeds).

**Setup and required environment variables: [`NOTIFICATIONS.md`](NOTIFICATIONS.md).** No database changes were needed.

### Task 5 — Deactivation and Permanent Deletion

Administrative entities now support two clearly distinct operations:

- **Deactivate / Archive** (existing behaviour, kept): the record stays in the database, is hidden from active views, and every historical relationship is preserved. Reversible.
- **Delete permanently** (new): the row is genuinely removed from the database. Irreversible.

Permanent deletion is **only permitted when nothing references the record.** The data model uses `ON DELETE RESTRICT` throughout and treats `interventions`, `approval_history` and `audit_log` as never-deleted (Ch.49/Ch.50, Rule 9), so cascading was never an option — deleting a client with interventions would destroy exactly the history the system exists to preserve.

Instead, a shared `deletion_service` checks every inbound foreign key first. If anything references the record, the request is refused with `409` and a message naming each blocker and its count, e.g.:

> This client cannot be permanently deleted because it is still referenced by 33 interventions, 12 planning entries, 3 client sites, 1 contracts. Deleting it would destroy historical records. Deactivate or archive it instead.

Supported on **Users, Clients, Client Sites, Contracts, Projects and Travaux** — all **Administrator-only**, enforced in the backend (`require_roles("admin_supervisor")`) as well as the UI.

The UI keeps the two operations unmistakable: deactivate is an amber circle-slash icon with a plain confirmation; permanent deletion is a red trash icon opening a distinct red dialog that pre-checks blockers, explains why it's blocked when it is, and otherwise requires **typing the record's name** to arm the delete button. No database changes were needed.
