# BIMS — Bon d'Intervention Management System

Digital replacement for the company's paper-based intervention workflow.

**Status:** Phases 1–10 complete (Init, Database, Auth, Reference Data, Planning, Interventions, Business Logic, Approvals, Dashboards & Reporting, Testing & Cleanup), plus eight post-launch tasks: configurable search/filters (Task 1), Administrator-configurable point rules (Task 2), a read-only hallway-display role with a live-updating global calendar (Task 3), assigned-intervention notifications with optional email/WhatsApp channels (Task 4), deactivation and permanent deletion for reference-data entities (Task 5), permanent deletion for Users with full history preservation (Task 6), a CEO role with exclusive Admin-management power (Task 7), and login by username-or-email plus self-service password reset (Task 8). See "Post-Launch Tasks" below for what each one actually changed.

> Several reference documents (the original SRS, phased task breakdown, full data model, API contracts, notification setup, and Postgres-migration notes) live in a local-only `additions/` folder that is intentionally not part of this repository on GitHub — see "Project Documentation" below for what's still available and where.

## Tech Stack

- **Frontend:** React + TypeScript + Vite + Material UI + React Router + TanStack Query + Axios + React Hook Form + FullCalendar + Day.js
- **Backend:** Python 3 + FastAPI + SQLAlchemy + Alembic + Pydantic + JWT
- **Database:** PostgreSQL (production-like setup) — SQLite is also supported for local development/evaluation, via a pre-seeded `backend/dev.db` (see "Quick Start" below). The data-access layer is written entirely against SQLAlchemy's database-agnostic query API; the codebase has exactly one place that branches on which dialect is in use (`backend/app/database/session.py`, a connection-argument difference) plus one dashboard KPI calculation using a SQLite-specific date function with its PostgreSQL equivalent already documented inline — migrating a real deployment to PostgreSQL is a configuration change, not a rewrite.

## Folder Structure

```
internship-project/
├── docker-compose.yml          # Postgres (required) + backend/frontend (convenience)
├── CLEANUP_LOG.md              # (in additions/, gitignored) history of the repo reorganization
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routers — HTTP only, no business logic
│   │   ├── models/         # SQLAlchemy ORM models (16 tables)
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # business logic (the only place calculations happen)
│   │   ├── repositories/   # database query layer
│   │   ├── authentication/ # password hashing, JWT
│   │   ├── middleware/     # auth dependency, role guards
│   │   ├── database/       # engine/session setup, seed script
│   │   ├── utils/
│   │   ├── uploads/        # uploaded attachments (gitignored)
│   │   └── static/
│   ├── alembic/versions/    # migrations (8, single linear chain)
│   ├── tests/               # pytest suite (259 tests, see "Running Tests" below)
│   ├── main.py
│   ├── config.py
│   ├── dev.db               # pre-seeded SQLite database (see "Quick Start")
│   ├── run_dev_sqlite.py    # zero-setup launcher for the SQLite quick-start path
│   └── requirements.txt
└── frontend/
    └── src/
        ├── components/ pages/ layouts/ hooks/
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
hallway-calendar role — see [Task 3](#task-3--display-role--live-global-calendar)).
This path is for local development and evaluation only —
see "Running the Backend" and "Running the Database" further down for the
PostgreSQL-backed setup those sections describe.

## Environment Variables

**Backend** (`backend/.env`, copy from `backend/.env.example`):

| Variable | Description |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg://user:pass@host:5432/dbname` |
| `SECRET_KEY` | JWT signing secret — change in production; the code falls back to an insecure development default if unset, so a real deployment must set this explicitly |
| `JWT_ALGORITHM` | default `HS256` |
| `JWT_EXPIRE_MINUTES` | token lifetime |
| `UPLOAD_FOLDER` | attachment storage path |
| `MAX_UPLOAD_SIZE` | bytes, default 10 MB |
| `APP_NAME` | display name |
| `DEBUG` | `true`/`false` |
| `CORS_ORIGINS` | comma-separated allowed origins |
| `FRONTEND_BASE_URL` | used to build links inside email/WhatsApp notifications (Task 4); defaults to `http://localhost:5173` |
| `EMAIL_ENABLED`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | optional email notification channel (Task 4) — disabled by default, see below |
| `WHATSAPP_ENABLED`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_TEMPLATE_NAME` | optional WhatsApp notification channel (Task 4) — disabled by default, see below |

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
alembic upgrade head          # applies the full schema (16 tables, 8-migration chain)
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

This populates the database with realistic synthetic data simulating several months of company activity: 10 technicians, 2 Chef des Techniciens, 2 Administration Supervisors, 1 read-only Display account (Task 3), 1 CEO account (Task 7), 20+ clients, 50+ client sites, 25+ contracts, 15+ projects, 125 travaux catalog entries, 500+ interventions across every lifecycle status (including warranty interventions referencing real prior BI numbers), 200+ planning records, 300+ notifications, 3 default point rules (Task 2 — see below), and full approval/audit history.

The script is idempotent — re-running it against an already-seeded database is a no-op (it checks whether the `roles` table is empty first).

**Seeded login credentials** (all accounts): password `Password123!`
- Technicians: `tech01` … `tech10`
- Chef des Techniciens: `chef01`, `chef02`
- Administration Supervisors: `admin01`, `admin02`
- Display (read-only hallway calendar, Task 3): `display01`
- CEO (Task 7 — the one account above Admin): `ceo01`

Every seeded account can also log in with its email instead of its username (Task 8) — e.g. `ceo01@bims.local` works wherever `ceo01` does.

> The committed `backend/dev.db` file additionally contains 58 real company travaux (technical-operation codes/names, added directly through the Travaux admin screen rather than the seed script) on top of the 125 synthetic ones above, for a live total of 183. Running `python -m app.database.seed` against a *fresh* empty database reproduces only the 125 synthetic entries — the 58 real ones are specific to the already-seeded `dev.db` file shipped in this repo, not something the seed script itself generates.

## Running Everything via Docker Compose

```bash
docker compose up -d
```

Starts Postgres, backend (with hot reload), and frontend (with hot reload) together.

## Running Tests

The backend has a permanent pytest suite (259 tests) covering authentication (including login by username or email, and self-service password reset — Task 8), business logic (duration/point calculation, status transitions), planning, interventions, approvals, reference-data CRUD, dashboards, reports, technician performance, configurable point rules (Task 2), the read-only display role (Task 3), assignment notifications (Task 4), deactivation/permanent deletion (Task 5 and Task 6), and the CEO role's exclusive Admin-management power (Task 7):

```bash
cd backend
pytest tests/
```

Each test spins up a fresh SQLite database via fixtures in `tests/conftest.py` and seeds it with the same `app.database.seed` logic used for real development data, so every test runs against realistic, fully isolated data rather than mocks. This makes the full run slow (fresh module reload + full reseed per test, on the order of 20 minutes for the whole suite) but each test fully independent of the others. There is currently no frontend test suite beyond TypeScript's own type-checking (`npx tsc --noEmit`) and linting (`npm run lint`).

## Development Workflow

The project was built incrementally, one phase at a time:

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

Business rules — for example "cities are never typed manually," "interventions are never deleted, only status-transitioned," or the point/duration formulas — are enforced **only** in `backend/app/services/`. The frontend displays data and calls the API; it never recalculates anything the backend already computed.

## Post-Launch Tasks

Six follow-on tasks were implemented after the original 10-phase plan above, each scoped and delivered independently.

### Task 1 — Search and Relevant Filters

Every list page's search bar now has entity-appropriate filters (not one generic set): Client Sites gained a City filter, Contracts/Projects gained start-date ranges, Travaux gained a Category filter, and Interventions gained Technician (Chef/Admin only — a technician's own list already has exactly one technician in it), City, Type, Contract, and Project filters — all combinable with search, pagination, and existing role restrictions. No new tables; a handful of existing list endpoints gained new optional query parameters.

### Task 2 — Administrator Point Rules

The point-award windows (originally `17:00–19:00 → +5`, etc.) were previously hardcoded in `business_logic_service.calculate_points()`. They're now stored in a `point_rules` table (`start_time`, `end_time`, `points`, `active`) managed through a **Point Management** section in the Administrator UI (create/edit/deactivate/delete, no cap on how many rules can exist, midnight-crossing windows and overlap-conflict validation both handled explicitly). `calculate_points()` reads the active rules from the database instead of an `if/elif` chain; every dashboard/KPI/report continues to read the already-stored `interventions.points_earned` column exactly as before, so **editing or deleting a rule never changes any intervention's already-awarded points** — only future submissions are affected.

- Migration: `backend/alembic/versions/5b327e8d21a6_add_point_rules_table.py`
- New endpoints: `GET/POST/PUT/PATCH/DELETE /api/point-rules` (Administrator-only)

### Task 3 — Display Role & Live Global Calendar

A 4th role, `display`, was added for a dedicated, strictly read-only hallway-screen account (seeded as `display01`) that can log in and see one thing: a full-screen, auto-refreshing global planning calendar (`/display-calendar`, no sidebar/top bar). It has no access to any other endpoint anywhere in the API — every existing role-restricted router was left untouched; the only new surface is one purpose-built endpoint, `GET /api/planning/display`, reachable by `display`/`chef_technicien`/`admin_supervisor`, that returns planning entries with technician/client/site names already resolved server-side (no separate `/clients` or `/users` lookup needed) and defaults to showing every planning entry in the system (no date window) unless one is explicitly requested.

Live updates use **controlled polling** (TanStack Query's `refetchInterval`, the same mechanism already used for the notification badge) at a 20-second interval, including while the browser tab is backgrounded — this codebase has no WebSocket or Server-Sent-Events infrastructure anywhere, and polling was the least-invasive mechanism that satisfied "no manual refresh required" without introducing new infrastructure for one screen.

The calendar is sized to a hard viewport ceiling (`100dvh`, immune to page-level growth) rather than relying on ordinary page scrolling, so it fits any screen without manual zoom adjustment. Clicking a day with more entries than fit, or an individual planning entry, opens a centered popup (MUI `Dialog`, always viewport-centered regardless of where the trigger was) with a scrollable list or full read-only detail respectively — the calendar remains visible behind it.

- Migration: `backend/alembic/versions/2c9527c79999_add_display_role.py` (extends the PostgreSQL `role_name` enum; a no-op on SQLite, which has no native enum type)
- Existing Technician/Chef/Admin calendars (`PlanningPage.tsx`, the technician calendar) were not touched

### Task 4 — Assigned Intervention Notifications

When an Administrator or Chef des Techniciens assigns a planned intervention, **only the assigned technician** is notified — never all technicians. This covers both urgent and normal assignments, plus reassignment (the newly-assigned technician gets a full assignment notification; the previous one is told it's no longer theirs).

Notifications carry the client, site/city, planned date and time, and priority, and clicking one deep-links the technician into that specific assignment.

This extends the **existing** notification system (the `notifications` table and `notification_service`) rather than adding a second one. On top of the in-app notification, a `delivery_service` fans the same content out to two **optional** channels:

- **Email (SMTP)** — including Gmail (requires a Google App Password)
- **WhatsApp** — via the Meta WhatsApp Cloud API (requires a Meta Business account and an approved message template)

Both are **disabled by default and configured entirely through environment variables** (see "Environment Variables" above) — no credentials are hardcoded anywhere in the codebase. The application is fully functional with neither configured, and an unreachable or misconfigured provider never fails the assignment that triggered the notification (covered by tests that point the app at a dead host and assert the assignment still succeeds).

### Task 5 — Deactivation and Permanent Deletion (Reference Data)

Administrative entities support two clearly distinct operations:

- **Deactivate / Archive** (existing behaviour, kept): the record stays in the database, is hidden from active views, and every historical relationship is preserved. Reversible.
- **Delete permanently** (new): the row is genuinely removed from the database. Irreversible.

For **Client Sites, Contracts, Projects, and Travaux**, permanent deletion always succeeds, even when other records reference the entity being deleted — a shared `deletion_service` **detaches** the reference (clears the foreign key to `NULL`) rather than blocking the delete or cascading it away. An intervention that referenced a now-deleted client, for example, keeps its own BI number, dates, duration, points, and full approval/audit history intact; it simply no longer shows a client. The one exception at this stage was **Clients**, whose own child records (sites/contracts/projects) are detached the same way when the client itself is deleted, so deleting a client never silently deletes anything that belonged to it.

The `/deletion-check` endpoint on each entity reports what will be detached (as an informational impact, not a blocker) before the Administrator confirms, and the UI shows an amber warning listing exactly what will lose its link — explicitly stating that those records are not deleted.

Supported on **Client Sites, Contracts, Projects, and Travaux** at this stage — see Task 6 immediately below for Users, which needed a different mechanism.

### Task 6 — Permanent User Deletion with History Preservation

Users were initially the one entity kept hard-blocked from permanent deletion, since a user is the *actor* in the audit trail (who approved something, who performed an intervention), not just a piece of reference data being pointed at. That block has since been removed: **any user can now be permanently deleted, including one with a full history of approvals, interventions, and uploads** — with no loss of that history.

The mechanism is different from Task 5's plain detach, because a deleted user has no other record of their own name once their row is gone (unlike a client, whose name still exists on other surviving rows). So deleting a user **freezes their full name as a plain-text label** onto every row that referenced them — `interventions.deleted_user_label`, `approval_history.deleted_user_label`, `audit_log.deleted_user_label`, `attachments.deleted_user_label`, and two separate labels on `planning` (one for the assigned technician, one for the creator) — immediately before the live foreign key is cleared. Old approvals, interventions, and audit entries keep showing who did them (e.g. "Approved by Jean Dupont") even though that account no longer exists to log in. The one exception is `intervention_technicians` (colleague-technician participation), a pure join row with no content of its own beyond the link, which is deleted outright rather than frozen — the same treatment already used for `intervention_tasks` when a Travail is permanently deleted.

- Migration: `backend/alembic/versions/583080ba69d4_freeze_deleted_user_names.py`

### Permission model across Tasks 5 and 6

All of the above — deactivation, permanent deletion, and the pre-flight `/deletion-check` — is **Administrator-only**, enforced in the backend (`require_roles("admin_supervisor")`) as well as the UI, for every entity. The UI keeps the two operations unmistakable: deactivate is an amber circle-slash icon with a plain confirmation; permanent deletion is a red trash icon opening a distinct red dialog that lists what will be affected and requires **typing the record's name** to arm the delete button.

### Task 7 — CEO Role

A 5th role, `ceo`, sits above Administration Supervisor: **exactly one CEO account can ever exist** (enforced in `user_service._ensure_single_ceo`, checked at creation, not just assumed from the seed script). Everywhere a route required `admin_supervisor`, it now accepts `ceo` too, so the CEO can do everything an Administrator can. The CEO's one exclusive power is the reverse of that: **only the CEO can create, edit, deactivate, or permanently delete an Administrator or the CEO account itself** — a regular Administrator gets 403 attempting any of those against another Admin or the CEO (`user_service._ensure_can_manage_role`). The CEO account is also immune to both deactivation and permanent deletion, unconditionally, including by itself.

- Migration: `backend/alembic/versions/4bc2260af366_add_ceo_role.py`
- Seeded account: `ceo01` (see "Seeded login credentials" above)

### Task 8 — Login by Username or Email, and Self-Service Password Reset

`POST /auth/login` now accepts either a username or an email address in the same field — `auth_service.authenticate()` tries a username lookup first, falling back to email only if that fails, so nobody's existing login habit changes.

Alongside that, any authenticated user can now reset their own password without an Administrator: `GET /auth/password-reset/availability`, `POST /auth/password-reset/request`, and `POST /auth/password-reset/confirm` (all in `backend/app/services/password_reset_service.py` and `backend/app/api/auth.py`) implement a two-step, code-based flow that always acts on the caller's own account, never a target user id. Requesting a reset emails a 6-digit code (bcrypt-hashed at rest, never stored raw, 10-minute expiry, single-use) to the user's on-file address via the existing Task 4 `delivery_service` — no second email system. If email isn't configured, the request fails loudly with a 409 rather than pretending to succeed, since a silent failure here would leave someone locked out with no explanation.

- Migration: `backend/alembic/versions/a2159ec5c6ae_add_password_reset_codes.py`

## Project Documentation

The original SRS (`project_specifications.md`), phased task breakdown (`TASKS.md`), full data model (`DATABASE_SCHEMA.md`), API endpoint contracts (`API_SPEC.md`), notification setup guide (`NOTIFICATIONS.md`), and Postgres-migration notes (`FUTURE_DATABASE_INTEGRATION.md`) all still exist, but live in a local-only `additions/` folder (see `CLEANUP_LOG.md` inside it for the full reasoning) that is deliberately excluded from this GitHub repository. If you're working from a clone that doesn't have that folder, these documents aren't available — ask whoever manages the project for them directly.

Git branching follows `main` (protected) ← `develop` ← `feature/*`, with PRs reviewed before merging into `develop`.
