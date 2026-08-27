# BIMS — Complete Technical Architecture

This document explains the full architecture of BIMS (Bon d'Intervention Management
System): how the application is structured, every technology it uses and why, the
folder layout, and the complete request lifecycle from a user's click to the database
and back.

---

## 1. Overall Architecture

### 1.1 High-level architecture

BIMS is a **split, two-service architecture**: a stateless REST API backend and a
fully separate static single-page-application frontend, communicating over HTTPS with
JWT bearer-token authentication and no server-side session state.

```
┌───────────────────────┐        HTTPS + JSON         ┌─────────────────────────┐
│      FRONTEND            │ ◄──────────────────────────► │        BACKEND API         │
│  React + TypeScript      │   Authorization: Bearer <JWT>  │   FastAPI (Python)          │
│  Static build (Vite)     │                                │   Uvicorn ASGI server       │
│  Hosted on Vercel         │                                │   Hosted on Railway         │
└───────────────────────┘                                └────────────┬────────────┘
                                                                          │ SQLAlchemy ORM
                                                                          ▼
                                                              ┌─────────────────────────┐
                                                              │         Database            │
                                                              │  PostgreSQL (production)    │
                                                              │  or SQLite (dev/demo)       │
                                                              └─────────────────────────┘
```

The two halves are fully decoupled: the frontend has no knowledge of the backend
beyond one configured base URL (`VITE_API_URL`), and the backend has no knowledge of
the frontend beyond which origins are allowed to call it (CORS). This is what allows
them to be built, tested, deployed, and scaled independently — and is why they're
hosted on two different platforms in production.

### 1.2 Backend

A layered FastAPI application with a strict, one-directional dependency chain:

```
API layer (app/api/*.py)              — HTTP routing + role authorization only
        │
        ▼
Service layer (app/services/*.py)      — 100% of business logic and calculations
        │
        ▼
Repository layer (app/repositories/*.py) — all database query construction
        │
        ▼
Model layer (app/models/*.py)           — SQLAlchemy ORM entities (15 tables)
```

No route handler in the API layer contains business logic — every handler resolves
authorization via a dependency (`Depends(require_roles(...))`), calls exactly one
service function, and wraps the result in a uniform response envelope
(`{success, message, data}`). This separation was maintained without exception
throughout the project.

### 1.3 Frontend

A single-page React application with one global piece of client state (authentication)
and everything else managed as server-cache state:

```
App.tsx (routing + global providers: MUI Theme, TanStack Query Client, Auth Context)
   │
   ├── ProtectedRoute (role-gated route wrapper, redirects to /login or /403)
   │      └── AppLayout (responsive shell: desktop sidebar / tablet icon-rail / mobile drawer)
   │             └── ~30 Page components, one per route
   │                    ├── Reusable components (DataTable, GenericCalendar, charts, etc.)
   │                    └── Service layer (typed functions calling the backend)
   │                           └── queryHelpers.ts (unwraps the {success, message, data} envelope)
   │                                  └── apiClient (axios instance — attaches the JWT,
   │                                        globally handles any 401 response)
   └── AuthContext (session state: current user, login/logout, token storage)
```

There is no Redux/Zustand or other global client-state store — TanStack Query owns
the entire server-data lifecycle (fetching, caching, refetching, invalidation after a
mutation), which is why no separate state-management library was needed beyond the
authentication context.

### 1.4 Database

15 tables, centered on one core entity (`interventions`), with two genuine
many-to-many relationships (via explicit join tables), one self-referential foreign
key (a warranty intervention referencing an earlier intervention), and strict
soft-delete conventions — no row in the audit-sensitive tables (`interventions`,
`approval_history`, `audit_log`) is ever deleted; the application code never issues a
`DELETE` against them. One post-launch table, `point_rules` (Task 2), is a genuine
exception to that pattern — it has no foreign key pointing into it from anywhere else,
so it supports real hard deletes safely (an Administrator permanently removing a point
rule cannot orphan or corrupt any intervention, since `points_earned` stores a plain
computed integer, not a reference back to the rule). See `DATABASE_SCHEMA.md` for the
full column-by-column breakdown; the full entity list and relationships are also
covered in Section 8 of this document at a summary level.

### 1.5 Authentication

Stateless JWT-based authentication with no server-side session store:

```
Login (username + password)
   │
   ▼
Backend verifies the password (bcrypt) against the stored hash
   │
   ▼
Backend issues a signed JWT: { sub: user_id, role, exp }
   │
   ▼
Frontend stores the token and attaches "Authorization: Bearer <token>"
to every subsequent request (axios request interceptor)
   │
   ▼
Backend verifies the signature + expiry on every protected request,
re-fetches the User row (so a deactivated account is locked out
immediately even with a still-valid token), then checks the caller's
role against that endpoint's allowed-roles list
```

Authorization is enforced identically everywhere through one reusable FastAPI
dependency, `require_roles(*allowed_roles)` (`app/middleware/auth.py`) — never
duplicated as bespoke per-endpoint logic. The frontend has a matching, structurally
identical guard (`ProtectedRoute.tsx`), but the frontend guard is a usability
convenience only; the backend dependency is the actual security boundary.

### 1.6 API

A conventional REST design under one `/api` prefix. Every response uses the same
envelope shape (`{success, message, data}`); every paginated list endpoint uses the
same page shape (`{items, total, page, page_size, pages}`). One deliberate
API-design decision worth highlighting: eight of the ten specified report types are
structurally identical ("a list of interventions matching a filter set," differing
only in which filter the frontend pre-applies), so they're implemented as one
generically filterable endpoint rather than eight near-duplicate ones.

### 1.7 Deployment

```
Developer pushes to GitHub (main branch)
        │
        ├────────────────────────────┬────────────────────────────┐
        ▼                              ▼
┌─────────────────────┐      ┌─────────────────────┐
│   Railway (backend)    │      │    Vercel (frontend)   │
│  Builds from             │      │  Auto-detects Vite      │
│  backend/Dockerfile      │      │  framework, builds        │
│  Root dir: backend/      │      │  a static output           │
│  Ships a pre-seeded       │      │  Root dir: frontend/       │
│  demo database inside      │      │  SPA rewrite rule via       │
│  the image                  │      │  vercel.json                 │
└──────────┬───────────┘      └──────────┬────────────┘
           │                                │
           ▼                                ▼
  https://<backend>.up.railway.app   https://<frontend>.vercel.app
           ▲                                │
           └────────── CORS-allowed ────────┘
              cross-origin API calls (Bearer JWT, no cookies)
```

Locally, an equivalent three-container Docker Compose stack (PostgreSQL + backend with
hot reload + frontend dev server with hot reload) reproduces the same topology for
development. A separate, even simpler local path (`run_dev_sqlite.py`) runs the
backend directly against a pre-seeded SQLite file with zero external services at all.

### 1.8 File uploads

Attachments (the photographed/scanned signed paper BI, and any other supporting
files) are uploaded as `multipart/form-data` to a dedicated endpoint, validated
server-side for content type (JPG/JPEG/PNG/PDF only) and a maximum size (configurable,
10 MB by default), and stored on the backend's local filesystem under a
year/month/BI-number-partitioned path. Because downloading an attachment requires the
same Bearer-token authentication as every other endpoint (and a plain `<img src>` tag
cannot send a custom header), the frontend fetches attachment images as an
authenticated blob request and converts the result into a local object URL for
display — this pattern is centralized in one shared hook
(`useAuthenticatedPreview.ts`) rather than reimplemented per component.

### 1.9 Reports

The reporting module (`services/report_service.py`, `services/export_service.py`)
builds a filtered dataset from the same underlying intervention/approval/planning
tables the rest of the application already writes to — there is no separate reporting
database or ETL step. Two independent renderers (reportlab for PDF, openpyxl for
Excel) both consume that same filtered row data, so a report's content is guaranteed
identical regardless of which export format is chosen.

### 1.10 Planning

The planning module (`services/planning_service.py`) is the scheduling layer sitting
"before" an intervention exists as a submitted record — a Chef des Techniciens creates
a planning entry (assigning a technician, date, time, client, site, priority), which
the technician sees on their own calendar and is notified of. An urgent-priority
planning entry additionally participates in a separate, manually-orderable "urgent
queue" surfaced on the Chef's dashboard.

### 1.11 Notifications

A single service (`services/notification_service.py`) owns every notification-
triggering event in the system — new/urgent assignment, planning modified/cancelled,
submission received, technical approval granted, rejection (at either level), and
full approval — each writing one row to the `notifications` table, optionally linked
back to either the originating intervention or planning entry (two independent
nullable foreign keys, not a single polymorphic reference). The frontend's
notification-click routing (`utils/notificationRouting.ts`) inspects a notification's
content to deep-link the user to the correct page, including auto-opening the correct
edit modal when the target is a planning entry.

### 1.11b Outbound notification channels (Task 4, post-launch)

`notification_service` remains the single owner of every notification and the
`notifications` table remains the single source of truth — Task 4 did not add a
second notification system. What it added is `services/delivery_service.py`, a
best-effort fan-out that mirrors an in-app notification to **email (SMTP)**
and/or **WhatsApp (Meta Cloud API)**.

Both channels are disabled by default and configured purely through environment
variables (`config.py`; no credential is hardcoded). Two invariants make the
feature safe to leave switched off, half-configured, or pointed at a broken
provider:

1. The in-app notification is written and committed *before* any external send
   is attempted.
2. Every external send is wrapped so that unreachable hosts, bad credentials,
   timeouts, missing optional dependencies (`httpx`) and provider errors are
   logged and swallowed — an assignment never fails because email or WhatsApp
   is down.

Assignment notifications also gained the client/site/date/priority context the
technician needs, shared verbatim between the in-app copy and the external
copies. See `NOTIFICATIONS.md` for the full configuration guide and the
per-event recipient matrix.

### 1.11c Deactivation vs permanent deletion (Task 5, post-launch)

Administrative entities support two distinct operations, deliberately kept
separate in both the API and the UI:

- **Deactivate/archive** — the pre-existing soft-delete (`active = false` or
  `status = 'archived'`). The row and every relationship survive; it is simply
  hidden from active views and reversible.
- **Permanent deletion** — a real `DELETE`, allowed *only* when nothing
  references the record.

`services/deletion_service.py` is the single place that knows the dependency
graph. Before any hard delete it counts every inbound foreign key and, if any
exist, raises a 409 naming each blocker and its count. This is not a
convenience check — it is what upholds the schema's `ON DELETE RESTRICT`
contract (Ch.49) and Rule 9 (interventions/approval_history/audit_log are
never deleted). Cascading was rejected outright: cascading a client delete
would silently destroy its interventions and their approval history.

Consequently, any record with genuine operational history is undeletable by
design, and the error message tells the Administrator to deactivate instead.
The frontend mirrors this with a distinct red `PermanentDeleteDialog` that
runs the same check up-front, lists the blockers, and — when deletion *is*
possible — requires typing the record's name to arm the button, so it can
never be confused with the amber deactivate flow beside it.

### 1.12 Configurable point rules (Task 2, post-launch)

The Ch.28 point-award windows were originally a hardcoded four-branch `if/elif` chain
inside `business_logic_service.calculate_points()`. They now live in a new
`point_rules` table, managed by the Administrator through a dedicated **Point
Management** admin screen (`point_rule_service.py` / `api/point_rules.py`) supporting
create/edit/deactivate/reactivate/delete with no artificial cap on how many rules can
exist. `calculate_points()` still runs exactly once, at submission time
(`intervention_service.submit_intervention`), and the result is still stored as a
plain integer in `interventions.points_earned` — every dashboard, KPI, and report
reads that already-computed column directly and never calls `calculate_points()`
again, which is what guarantees editing or deleting a rule can never retroactively
change a past intervention's already-awarded points. Interval containment and
overlap-conflict validation (including windows that cross midnight, e.g.
`22:00`–`00:00`) are centralized in `point_rule_service.contains()` /
`_intervals_overlap()`, the same functions `calculate_points()` calls, so the scoring
logic and the admin-facing validation logic can never drift apart into two competing
implementations.

### 1.13 Display role & live global calendar (Task 3, post-launch)

A fourth role, `display`, was added for a dedicated, strictly read-only hallway-screen
account with exactly one reachable capability anywhere in the API: a new endpoint,
`GET /planning/display` (also reachable by Chef/Admin, harmlessly, since they already
see this same data through other means), which returns global planning entries with
technician/client/site names already resolved server-side — the display role needs no
separate `/clients` or `/users` lookup, unlike every other calendar page in the app.
Every pre-existing role-restricted router was left untouched; `display` was
deliberately never added to any of them.

The frontend renders this as a dedicated, layout-free, full-screen page
(`DisplayCalendarPage.tsx`, routed outside `AppLayout` entirely) reusing the existing
`GenericCalendar` component unmodified. Live updates use **controlled polling** —
TanStack Query's `refetchInterval`, the same mechanism already proven by the
notification-badge poll (`useNotificationPolling.ts`) — at a 20-second interval, since
this codebase has no WebSocket or Server-Sent-Events infrastructure anywhere and
polling was judged the least invasive mechanism that satisfies "no manual refresh
required" for one screen.

---

## 2. Folder Structure

### Backend (`backend/`)

```
backend/
├── app/
│   ├── api/            FastAPI routers — HTTP routing and role authorization only,
│   │                    zero business logic. One file per feature area (auth, users,
│   │                    clients, sites, contracts, projects, travaux, planning,
│   │                    interventions, attachments, approvals, dashboard,
│   │                    technician_performance, reports, notifications, health,
│   │                    point_rules).
│   ├── authentication/  Password hashing (bcrypt) and JWT creation/verification —
│   │                    pure, dependency-free cryptographic functions.
│   ├── database/        Engine/session setup (session.py) and the synthetic-data
│   │                    seed generator (seed.py).
│   ├── middleware/      The role-based-access-control dependency (auth.py) — the
│   │                    single mechanism every protected endpoint uses.
│   ├── models/          SQLAlchemy ORM entities — one file per table, 15 total.
│   ├── repositories/    The database query layer — one file per entity, hand-written
│   │                    SQLAlchemy `select(...)` queries, no query logic duplicated
│   │                    into services.
│   ├── schemas/         Pydantic request/response models — the API's data contracts.
│   ├── services/        100% of business logic — calculations, the status state
│   │                    machine, validation, notification triggering. This is the
│   │                    single most important directory in the backend.
│   ├── utils/           Small stateless helpers (BI-number formatting, pagination).
│   ├── static/          (reserved, not actively used by any current feature)
│   └── uploads/         Attachment storage, partitioned by year/month/BI-number.
│                        Gitignored — this is runtime data, not source code.
├── alembic/             Database migration scripts — one file per schema change,
│                        forming a linear, reversible chain from the initial baseline
│                        to the current schema.
├── tests/               The full pytest suite (211 tests), one file per feature area,
│                        each test running against a freshly created and freshly
│                        seeded database (no shared fixtures, no mocks).
├── main.py              The FastAPI application entry point — constructs the app,
│                        registers every router, sets up CORS and the global error
│                        handler, and (via a lifespan hook) ensures the schema exists
│                        and demo data is seeded on startup if the database is empty.
├── config.py            Typed application configuration (the `Settings` class),
│                        loaded from environment variables.
├── run_dev_sqlite.py     A zero-external-dependency local launcher — points the app
│                        at a pre-seeded SQLite file and starts it with no Docker, no
│                        Postgres, no manual seed step required.
├── requirements.txt      Production Python dependencies.
├── requirements-dev.txt  Additional dependencies needed only for running tests.
├── Dockerfile            The container image definition used for the Railway deploy.
└── dev.db                The committed, pre-seeded SQLite demo database (see the
                        separate synthetic-database document for full detail).
```

### Frontend (`frontend/src/`)

```
frontend/src/
├── api/            The shared axios instance (client.ts — JWT attachment, 401
│                    handling) and generic response-unwrapping helper functions
│                    (queryHelpers.ts) that every service module is built on.
├── components/      Reusable UI building blocks used across multiple pages — data
│                    tables, calendars, charts, form selects, dialogs, etc. Nothing
│                    in this directory is page-specific; if a component is only ever
│                    used by one page, it typically lives inline in that page instead.
├── context/         React Context providers — currently just AuthContext, the one
│                    piece of global client-side state in the whole application.
├── hooks/           Custom React hooks — currently just the authenticated-attachment-
│                    preview hook shared by every image-displaying component.
├── layouts/         The application shell (AppLayout.tsx) — the responsive sidebar/
│                    top-bar/content-area wrapper every protected page renders inside,
│                    with one deliberate exception: DisplayCalendarPage.tsx (Task 3)
│                    is routed outside AppLayout entirely, since a hallway-kiosk screen
│                    should occupy the full viewport with no sidebar/top-bar chrome.
├── pages/            One component per route — the actual screens a user navigates
│                    between. Includes two sub-directories: `admin/` (seven
│                    reference-data/configuration management screens — the original
│                    six plus PointRulesPage.tsx, Task 2 — all admin_supervisor-only)
│                    and `dashboards/` (the per-role dashboard content components).
│                    DisplayCalendarPage.tsx (Task 3) lives at the top level, not
│                    under admin/, since its role (`display`) is not admin_supervisor.
├── routes/           The role-gated route-protection wrapper (ProtectedRoute.tsx).
├── services/         One file per backend feature area — typed functions that call
│                    the matching API endpoints and return typed results. This is the
│                    layer every page actually imports from; no page calls the raw
│                    API client directly.
├── styles/           The MUI theme definition and the shared chart color palette.
├── types/            TypeScript interfaces mirroring the backend's Pydantic schemas —
│                    the frontend's model of every entity the backend returns.
├── utils/            Small stateless helper functions (notification-click routing,
│                    status/priority/planning color-coding, role-to-dashboard-path
│                    mapping) that don't belong to any single component or page.
├── App.tsx            The route table and top-level provider tree.
└── main.tsx           The actual entry point — mounts the React tree, registers the
                     Day.js ISO-week plugin globally (so frontend week-boundary
                     calculations match the backend's own Monday-start convention).
```

### Repository root

```
├── project_specifications.md   The full written specification (154 chapters) —
│                                the single source of truth every design decision in
│                                this project traces back to.
├── DATABASE_SCHEMA.md            The complete relational schema, derived directly
│                                from the specification's data-model chapters.
├── API_SPEC.md                    The complete endpoint inventory and role-
│                                authorization matrix, derived from the specification's
│                                API chapters.
├── TASKS.md                       The ten-phase implementation plan the project was
│                                actually built against, in order.
├── README.md                      Setup, running, testing, and deployment
│                                instructions for both local and hosted environments.
├── docker-compose.yml              The local three-container development stack
│                                (PostgreSQL + backend + frontend).
├── backend/                        (see above)
└── frontend/                       (see above)
```

---

## 3. Technologies

### Backend

| Technology | Version | Purpose | Where used | Why chosen |
|---|---|---|---|---|
| **Python** | 3.12 (Docker image), 3.10+ supported | The backend implementation language | The entire `backend/` directory | Mature ecosystem for exactly this combination of a typed REST API, ORM, and data-validation-heavy application (FastAPI + SQLAlchemy + Pydantic) |
| **FastAPI** | ≥0.115.0 | The web framework — routing, request/response validation, dependency injection, automatic interactive API docs | Every file under `app/api/` | Generates its documentation automatically from the same type-annotated function signatures used to define endpoints, eliminating documentation drift; its dependency-injection system is what makes `require_roles(...)` a single, reusable, composable authorization mechanism instead of duplicated per-endpoint checks |
| **Uvicorn** | ≥0.30.6 | The ASGI server that actually runs the FastAPI application | `main.py` is what it serves; invoked directly in `Dockerfile`'s `CMD` and in `run_dev_sqlite.py` | The standard, high-performance ASGI server for FastAPI applications |
| **SQLAlchemy** | ≥2.0.35 (2.0-style declarative mapping) | The Object-Relational Mapper — maps Python classes to database tables | Every file under `app/models/` and `app/repositories/` | Supports both PostgreSQL and SQLite through the same codebase with only one connection-argument difference (handled by a single conditional in `app/database/session.py`), which underpins the project's whole dual-database strategy (Postgres for production, SQLite for zero-setup local/demo use) |
| **Alembic** | ≥1.13.2 | Database migration tooling | `backend/alembic/` | The standard companion to SQLAlchemy; every schema change in this project's history is a small, reversible, chronologically ordered migration file |
| **Pydantic** (via **pydantic-settings**) | ≥2.10 / ≥2.5.2 | Request/response schema validation, and typed application configuration | Every file under `app/schemas/`; `config.py`'s `Settings` class | FastAPI's native validation layer, so adopting it was effectively free; gives configuration errors precise, structured messages rather than an unclear runtime crash |
| **python-jose** | ≥3.3.0 | JWT creation and verification | `app/authentication/jwt.py` | A focused, standards-compliant JWT library; used for exactly two functions (`create_access_token`, `decode_access_token`), nothing more |
| **bcrypt** | ≥4.1.0 | Password hashing | `app/authentication/password.py` | Used directly (not through a higher-level wrapper) after a real compatibility break was found in the more commonly used wrapper library's own self-test code under a newer bcrypt release |
| **PostgreSQL** | 16 (Docker Compose image) | The production-grade relational database | The Docker Compose local stack; the intended real-production target | Explicitly the specification's intended production database; the natural choice given this application's referential-integrity and concurrent-write requirements |
| **SQLite** | (Python standard library, no separate install) | The zero-setup secondary database option | Local development (`run_dev_sqlite.py`), the automated test suite, and the current production deployment's demo database (`backend/dev.db`) | Requires no external service at all, which is what makes the project immediately clonable-and-runnable with no setup, and what makes the deployed demo boot with zero platform-side database provisioning |
| **python-multipart** | ≥0.0.9 | Parses `multipart/form-data` request bodies | The attachment-upload endpoint | Required by FastAPI/Starlette for handling file uploads |
| **python-dotenv** | ≥1.0.1 | Loads `.env` files into the process environment | Used transitively by `pydantic-settings`'s `env_file` support | Standard local-development convenience for supplying configuration without exporting shell variables manually |
| **Faker** | ≥28.4.1 | Generates realistic synthetic data (names, companies, addresses, phone numbers) | `app/database/seed.py`, exclusively | Produces demographically plausible, non-repetitive fake data far faster and more realistically than hand-written fixtures — essential given the scale of the synthetic dataset (hundreds of interventions, dozens of clients) needed to make the dashboards and reports meaningfully demonstrable |
| **reportlab** | ≥5.0.0 | PDF generation | `app/services/export_service.py`'s `render_pdf()` | A mature, widely used Python PDF-generation library, giving fine-grained control over the styled table layout used for every exported report |
| **openpyxl** | ≥3.1.5 | Excel (.xlsx) generation | `app/services/export_service.py`'s `render_excel()` | The standard library for writing `.xlsx` files from Python without requiring Excel itself to be installed |
| **pytest** | (declared in `requirements-dev.txt`) | The backend test framework | `backend/tests/` | The de facto standard Python test runner; its fixture system fits this project's per-test fresh-database pattern naturally |

*Note on the task's example list:* **Plotly** and **Pandas** were listed as example
technologies in the original request, but neither is actually present anywhere in this
project's dependencies or source code (confirmed via a direct search of
`requirements.txt` and the full backend source). The actual charting library is
**Recharts** on the frontend (see below); the actual data-generation and export
libraries are **Faker**, **reportlab**, and **openpyxl** as listed above. This is
called out explicitly rather than silently included, since claiming an unused
technology at a defense would be a real, checkable inaccuracy.

### Frontend

| Technology | Version | Purpose | Where used | Why chosen |
|---|---|---|---|---|
| **React** | ^19.2.8 | The UI framework — component-based, declarative UI | The entire `frontend/src/` directory | Ecosystem maturity for a data-heavy, role-differentiated multi-page application |
| **TypeScript** | ~6.0.2 | Static typing for the entire frontend codebase (no plain `.js` files) | Every file under `frontend/src/` | With 14+ distinct data shapes flowing between backend and frontend, static typing catches an entire category of integration bugs (a renamed/restructured backend field) at compile time rather than at runtime in front of a user |
| **Vite** | ^8.2.0 | The build tool and development server | `vite.config.ts`; `npm run dev` and `npm run build` | Near-instantaneous dev-server startup and hot-module-reload compared to older bundlers, directly relevant to iteration speed across this many distinct pages |
| **Material UI (MUI)** | ^9.2.0 (`@mui/material`, `@mui/icons-material`) | The component/design system | Essentially every visual element in the application | Provided a complete, accessible, professionally styled component set (tables, dialogs, forms, navigation) out of the box, letting implementation effort focus on data flows and business logic rather than building a design system from scratch |
| **Emotion** | ^11.14.0/^11.14.1 (`@emotion/react`, `@emotion/styled`) | CSS-in-JS styling engine | MUI's own internal styling dependency | Not chosen directly — it's MUI's required styling engine, included transitively |
| **React Router** | ^7.18.2 (`react-router-dom`) | Client-side routing | `App.tsx`, `ProtectedRoute.tsx` | The ecosystem-standard SPA router, integrating cleanly with a role-based route-protection wrapper component |
| **TanStack Query** | ^5.101.4 (`@tanstack/react-query`) | Server-state management — fetching, caching, background refetching, cache invalidation after mutations | Every page and most components, via `useQuery`/`useMutation` | Replaces manual `useEffect`+`useState` data-fetching entirely; this is why no separate global state-management library (Redux, etc.) was needed at all — the only global client state in the app is authentication |
| **Axios** | ^1.19.0 | The HTTP client | `api/client.ts`, and every `services/*.ts` file built on top of it | Its interceptor system implements two cross-cutting concerns cleanly and centrally: automatically attaching the JWT to every outgoing request, and globally handling any 401 response |
| **React Hook Form** | ^7.84.0 | Form state management and validation | Every page with a create/edit form (interventions, planning, all six admin reference-data pages) | Minimizes re-renders on every keystroke via uncontrolled inputs; its `Controller`/`useWatch` primitives implement the intervention form's conditional-field logic (client → site cascading, intervention-type-dependent fields) |
| **FullCalendar** | ^6.1.21 (`@fullcalendar/react`, `daygrid`, `timegrid`, `interaction`) | Calendar rendering | `components/GenericCalendar.tsx`, wrapped by `PlanningCalendar.tsx` and used directly by the interventions list's calendar view and both approval queues | Production-grade month/week/day calendar views with built-in event-click and visible-range-change hooks, used directly to drive the application's own data-fetching for whatever date range is currently visible |
| **Recharts** | ^3.10.1 | Chart rendering — every bar and line chart on every dashboard | `components/SimpleBarChart.tsx`, `SimpleLineChart.tsx`, and everything built on them | A React-native charting library with a declarative component API, fitting the same component-composition model as the rest of the frontend, rather than requiring imperative canvas manipulation (this is the project's actual charting library — see the Plotly/Pandas note above) |
| **Day.js** | ^1.11.21 (with the `isoWeek` plugin) | Date/time handling | Throughout the frontend wherever a date is formatted or manipulated; the `isoWeek` plugin is registered globally in `main.tsx` | The `isoWeek` plugin specifically makes the frontend's week-boundary calculation (Monday-start) match the backend's own week convention — a deliberate, small but consequential decision, since a mismatch would cause Week-mode dashboard charts to silently disagree between what the user selected and what data the backend actually returned |
| **dnd-kit** | ^6.3.1/^10.0.0/^3.2.2 (`core`, `sortable`, `utilities`) | Drag-and-drop | `components/UrgentQueueList.tsx`, exclusively | Built natively for React's current rendering model (no legacy HTML5 drag-and-drop workarounds); its pointer-sensor activation-distance configuration prevents accidental drags from interfering with normal clicks on the same list items |
| **react-zoom-pan-pinch** | ^4.0.4 | Image pan/zoom | `components/InterventionReviewViewer.tsx`, exclusively — the attached paper-BI photo viewer | A focused, single-purpose library for exactly this interaction, rather than pulling in a larger general-purpose image-gallery library for one well-defined need |
| **oxlint** | ^1.75.0 | Linting | `npm run lint`, `.oxlintrc.json` | A fast Rust-based linter, configured with React-specific rules (`rules-of-hooks`, etc.) |

### Deployment / infrastructure

| Technology | Purpose | Why chosen |
|---|---|---|
| **Docker / Docker Compose** | Local full-stack development environment (Postgres + backend + frontend with live reload); the deployment artifact format for the backend | A standalone `Dockerfile` (independent of the Compose file) is what the production hosting platform actually builds from |
| **Git** | Version control | Standard practice; this project's history is organized as a sequence of focused, independently describable rounds of change |
| **GitHub** | Remote repository hosting, and the source both deployment platforms build from | Both Railway and Vercel are configured to deploy automatically from pushes to the repository's `main` branch |
| **Railway** | Backend hosting | A managed container-hosting platform that deploys directly from a Dockerfile with minimal configuration — directly relevant to the deployment work of making the container boot correctly with safe, sensible defaults and zero required platform-side configuration for a first deploy |
| **Vercel** | Frontend hosting | Purpose-built for static frontend builds with automatic framework detection (recognizing the Vite build output with no manual build-command configuration needed); separating frontend and backend hosting onto their purpose-built platforms is a more standard, more scalable split-deployment pattern than hosting both together |

---

## 4. Complete Request Flow

### 4.1 Generic flow, every request

```
┌────────┐     ┌───────────┐     ┌─────────┐     ┌──────────────┐     ┌──────────┐
│  User    │ ──► │  Frontend    │ ──► │   API     │ ──► │ Business Logic │ ──► │ Database   │
│ (browser)│     │ (React page) │     │ (FastAPI  │     │  (services/*)   │     │(SQLAlchemy)│
└────────┘     └───────────┘     │  router)  │     └──────────────┘     └──────────┘
                                       └─────────┘
                       ▲                                                          │
                       │                                                          │
                       └──────────────────────  response  ◄──────────────────────┘
```

1. **User** interacts with a page (clicks a button, submits a form, navigates to a
   route).
2. **Frontend** — the page component calls a function from its matching
   `services/*.ts` file; that function calls `queryHelpers.ts`'s generic wrapper
   (`fetchOne`, `postOne`, etc.), which delegates to the shared `apiClient` (axios).
   The axios request interceptor attaches `Authorization: Bearer <token>`
   automatically.
3. **API** — FastAPI routes the request to the matching handler in `app/api/*.py`.
   Before the handler body runs, its `Depends(require_roles(...))` dependency chain
   executes: decode and verify the JWT, re-fetch the `User` row (rejecting a
   deactivated account immediately), and check the user's role against the endpoint's
   allowed-roles list — a 401 or 403 is returned here if either check fails, before any
   business logic ever runs.
4. **Business Logic** — the handler calls exactly one function in the matching
   `app/services/*.py` file. This is where every calculation, validation, and
   state-transition check happens (duration/points/lunch-break math, the status
   state-machine, warranty-reference validation, notification triggering).
5. **Database** — the service calls into `app/repositories/*.py`, which builds and
   executes the actual SQLAlchemy query against the `app/models/*.py` ORM entities.
6. **Response path (reverse):** the repository returns ORM objects → the service may
   transform/aggregate them → the API handler validates the result against a Pydantic
   response schema and wraps it in the `{success, message, data}` envelope → the
   frontend's `queryHelpers.ts` unwraps that envelope → the calling page re-renders
   with the new data (via TanStack Query's cache).

### 4.2 A concrete, worked example — submitting an intervention for approval

```
User clicks "Submit" on InterventionFormPage
        │
        ▼
frontend: interventionService.ts → submitIntervention(id)
        │  POST /api/interventions/{id}/submit   (Bearer JWT attached automatically)
        ▼
backend: api/interventions.py → submit_intervention()
        │  require_roles("technician") — 403 if not a technician
        ▼
services/intervention_service.py → submit_intervention()
        │
        ├──► services/status_transition_service.py
        │       ensure_transition_allowed(current, PENDING_TECHNICAL_APPROVAL)
        │       — 409 if the move isn't legal from the intervention's current status
        │
        ├──► services/business_logic_service.py
        │       calculate_points(submission_time)
        │       — computes the point award from the local submission hour
        │
        ├──► repositories/intervention_repository.py → update()
        │       writes the new status + submission_date + points_earned
        │
        └──► services/notification_service.py
                notify_chefs_of_submission(bi_number, intervention_id)
                — writes one notification row per active Chef des Techniciens
        │
        ▼
Response: {success: true, message: "...", data: <updated intervention>}
        │
        ▼
frontend: TanStack Query cache updates → InterventionDetailsPage re-renders
          showing the new "Pending Technical Approval" status
```

This single request touches four of the layers described in Section 1.2 (API →
service → two other services it calls into → repository), which is the normal shape
of almost every meaningful write operation in this application — a service function
rarely does everything itself; it composes smaller, focused service functions
(duration/points calculation, transition validation, notification dispatch) rather
than inlining all of that logic in one place.
