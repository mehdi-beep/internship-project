# The Synthetic Database — Where It Comes From and How to Work With It

This document explains the demo/synthetic database BIMS currently runs on: where it
lives, how it's built, how it's populated, and exactly how to modify or regenerate it.
**This is a pure explanation — nothing described here has been changed.**

---

## 1. Where it is stored

The synthetic database is a single file: **`backend/dev.db`**.

- It is a real, committed file in the Git repository (not gitignored) — this is
  deliberate, so that cloning the repository gives you a fully working, pre-populated
  application with zero setup.
- It is also what the production Railway deployment currently runs on: the
  `backend/Dockerfile` copies this exact file into the deployed container image and
  points `DATABASE_URL` at it by default.
- Its path is always relative to wherever the backend process's working directory is
  (`sqlite:///./dev.db`) — locally that's `backend/`, in the deployed container that's
  `/app` (the container's `WORKDIR`), which resolves to the same file either way.

## 2. Its format

SQLite — a single ordinary file containing the entire relational database (all 14
tables, every row, every index). No separate database server process is needed to
read or write it; Python's standard library (`sqlite3`) can open it directly, and
SQLAlchemy talks to it through the same ORM code path used for PostgreSQL, with only
one connection-argument difference (`app/database/session.py`).

You can inspect it directly with any SQLite tool, for example:

```bash
cd backend
python -c "
import sqlite3
conn = sqlite3.connect('dev.db')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM interventions')
print(cur.fetchone())
"
```

## 3. How it is created (the schema)

The **schema** (table/column definitions, not the data) comes from two possible
sources, and `dev.db` was built using the second:

- **Alembic migrations** (`backend/alembic/versions/`) — the "proper," versioned way
  to create the schema, normally used against PostgreSQL. Running `alembic upgrade
  head` applies every migration in order and produces an empty database with the
  correct structure.
- **`Base.metadata.create_all(engine)`** — a direct, migration-free way to create every
  table from the current SQLAlchemy model definitions in one call. This is what
  `run_dev_sqlite.py` uses, and it's also what runs automatically now on every backend
  startup (via a `lifespan` hook in `main.py`) as a safety net — but it's a no-op if
  the tables already exist, so it never touches `dev.db`'s existing structure or data
  in the normal case.

**Which files define the schema:** every file under `backend/app/models/` — one file
per table (e.g. `models/user.py` defines the `users` table, `models/intervention.py`
defines the `interventions` table). `backend/app/models/enums.py` defines every enum
type used across those tables (statuses, priorities, roles, etc.). `DATABASE_SCHEMA.md`
at the repository root is the human-readable documentation of this same schema.

## 4. How it is populated (the seed data)

**File: `backend/app/database/seed.py`** — this is the one file that controls
everything about the synthetic data. Run directly with:

```bash
cd backend
python -m app.database.seed
```

It generates, in this order (each stage depends on the previous one's output, so
order matters):

| Stage | Function | Quantity |
|---|---|---|
| Point rules (Task 2) | `seed_point_rules()` | 3 default rules, reproducing the original Ch.28 hardcoded windows exactly |
| Display role & account (Task 3) | `seed_display_role_and_account()` | 1 role row (`display`) + 1 user (`display01`) |
| Roles | `seed_roles()` | 4 (technician, chef_technicien, admin_supervisor, display) |
| Users | `seed_users()` | 15 (10 technicians `tech01`–`tech10`, 2 chefs `chef01`–`chef02`, 2 admins `admin01`–`admin02`, 1 display `display01`) |
| Clients & Sites | `seed_clients_and_sites()` | 22 clients, ~44–88 sites (2–4 per client) |
| Contracts & Projects | `seed_contracts_and_projects()` | 28 contracts, 18 projects |
| Travaux catalog | `seed_travaux()` | 125 (25 base operations × 5 variant suffixes) |
| Interventions | `seed_interventions()` | 650, spanning ~8 months, across all 9 lifecycle statuses |
| Planning | `seed_planning()` | 220 |
| Notifications | `seed_notifications()` | 320 |

The first two stages (point rules, display role/account) are called unconditionally at
the very top of `run()`, **before** the roles-count idempotency check the rest of the
function uses — each has its own independent, per-row idempotency check instead. This
is deliberate: both `point_rules` and the `display` role postdate the original schema,
so a database seeded before Tasks 2/3 existed (the committed `dev.db` is exactly this
case) would otherwise never gain either one on a normal restart. See
`business_logic_service.calculate_points()`'s module docs and
`seed_display_role_and_account()`'s own docstring for the full backfill rationale.

Every seeded technician/chef/admin/display account shares the same demo password: **`Password123!`**.

## 5. How the synthetic data is generated

Two techniques worth understanding, since they're both directly relevant if you want
to modify the generator:

- **Determinism.** Right after the imports, `seed.py` sets `Faker.seed(42)` and
  `random.seed(42)`. This means running the generator twice, on two different
  machines, produces the *exact same* dataset, byte for byet — same names, same
  emails, same random choices, every time. This is why the exact same demo data backs
  local development, the automated test suite, and the deployed production
  environment: they're not three different datasets that happen to look similar,
  they're the literal same generation run.
- **Referential-integrity-aware randomness.** The generator doesn't just pick random
  foreign keys — it actively avoids creating broken relationships. For example: a
  warranty-type intervention always references a real, already-created *prior*
  intervention from earlier in the same generation run (never a random or future ID);
  a contract-type intervention only ever picks a contract that genuinely belongs to
  the same client it's being created for (falling back to a plain "standard"
  intervention type if that client happens to have no contracts, rather than creating
  a mismatched link); and a generated notification's recipient is deliberately chosen
  so that recipient can actually view the intervention being referenced (a technician
  recipient is always that intervention's own technician, never someone else's).

## 6. How to modify it

You can edit `backend/app/database/seed.py` directly and re-run it — but read Section
7 first, since the seed script **will not overwrite an already-populated database**;
you need a fresh/empty database for a modified generator to actually take effect.

### To add more technicians, chefs, or admins

Edit the loop ranges in `seed_users()`:

```python
# Line 230 — technicians (currently range(1, 11) = 10 technicians)
for i in range(1, 11):
    ...
# Line 235 — chefs (currently range(1, 3) = 2 chefs)
for i in range(1, 3):
    ...
# Line 240 — admins (currently range(1, 3) = 2 admins)
for i in range(1, 3):
    ...
```
(The single seeded `display01` account, Task 3, is created separately by
`seed_display_role_and_account()` — not in this loop — since it must exist
independently of whether the rest of the demo dataset has ever been seeded.)
Widening any of these ranges (e.g. `range(1, 16)` for 15 technicians) is enough —
usernames are generated automatically as `tech{i:02d}`/`chef{i:02d}`/`admin{i:02d}`.

### To add more clients

Edit line 261, `for _ in range(22):` inside `seed_clients_and_sites()`. Each client
gets 2–4 randomly generated sites automatically (`random.randint(2, 4)` a few lines
below), so you don't need to separately control site count.

### To add more cities

Edit the `MOROCCAN_CITIES` list at **line 56** of `seed.py`:
```python
MOROCCAN_CITIES = [
    "Agadir", "Casablanca", "Rabat", "Marrakech", "Fes", "Tangier", "Meknes",
    "Oujda", "Kenitra", "Tetouan", "Safi", "Mohammedia", "El Jadida", "Beni Mellal",
    "Nador", "Taza", "Settat", "Khemisset", "Larache", "Guelmim",
]
```
Just add another city name string to the list. Remember (per Rule 4 of the
specification, and confirmed throughout the codebase) that cities are **never** a
standalone database field anywhere in the real application — they only ever exist as
the `city` column on a `client_sites` row. Adding a city here only affects which
city names get randomly assigned to newly generated sites; it does not create a
separate "cities" table or record.

### To add more contracts or projects

Edit line 288, `for _ in range(28):` (contracts) inside `seed_contracts_and_projects()`.
For projects, the generator draws from a fixed, hand-written list of 18 named
projects (e.g. `"Fiber Expansion Project"`, `"Datacenter Migration"`) a little further
down in the same function — to add more projects, either add more names to that list,
or change the loop that iterates over it to allow repeats.

### To add more travaux (catalog operations)

Edit the `TRAVAUX_CATALOG` list at **line 76** of `seed.py` — it's a list of
`(name, category)` pairs. Each entry is automatically combined with 5 variant
suffixes (`""`, `" — Type A"`, `" — Type B"`, `" — Standard"`, `" — Advanced"`) to
produce the final catalog, so adding one new `(name, category)` pair adds 5 new
travaux rows.

### To add more interventions

Edit line 369, `target_count = 650`, inside `seed_interventions()`. Raising this
number generates more interventions, spread across the same ~8-month date window and
the same weighted status distribution (documented in `seed.py`'s own
`INTERVENTION_STATUS_WEIGHTS` dict, a few lines above — heavily weighted toward
"Fully Approved," since the scenario being simulated is a company that's already been
using the application for months).

### To add more planning records or notifications

Same pattern: line 567 (`for _ in range(220):`) for planning, line 619
(`for _ in range(320):`) for notifications.

**Important — determinism note:** if you change any of the numbers/lists above and
then regenerate, you'll get a *different but still fully deterministic* dataset (since
`random.seed(42)` still applies) — re-running your modified generator repeatedly will
now always reproduce your new dataset consistently, but it will no longer match the
original 650/220/320 dataset described above or in any other project documentation.

## 7. How to regenerate it from scratch

The seed script has a **hard idempotency guard** — it checks whether the `roles`
table already has any rows, and if so, prints "Database already seeded... skipping"
and does nothing at all:

```python
# seed.py, inside run()
if db.query(Role).count() > 0:
    print("Database already seeded (roles table is non-empty) — skipping.")
    return
```

This means simply re-running `python -m app.database.seed` against the existing
`dev.db` **will not** apply any change you made to the generator — you must start from
a genuinely empty database first. Two ways to do that:

**Option A — delete and rebuild (simplest, but destroys the current `dev.db`):**
```bash
cd backend
rm dev.db          # deletes the current file entirely
python run_dev_sqlite.py   # recreates the schema and re-seeds, using your edited generator
```

**Option B — regenerate into a separate file (safer — keeps the original `dev.db` untouched):**
```bash
cd backend
DATABASE_URL="sqlite:///./dev_custom.db" python -c "
from app.database.session import Base, engine
import app.models  # registers every table on Base.metadata
Base.metadata.create_all(engine)
from app.database.seed import run
run()
"
```
This creates a brand-new file (`dev_custom.db`) with your modified dataset, leaving
the original `dev.db` completely untouched — useful if you want to experiment without
risking the file the whole team/deployment currently depends on.

## 8. Which files control database initialization

| File | Role |
|---|---|
| `backend/app/database/session.py` | Defines the SQLAlchemy `engine`/`SessionLocal`/`Base` — the actual connection to whichever database `DATABASE_URL` points at. |
| `backend/app/database/seed.py` | The data generator described throughout this document. |
| `backend/main.py` | Its `lifespan` startup hook (near the top of the file) calls `Base.metadata.create_all(engine)` then `seed.run()` on **every** application boot — both are safe no-ops if the schema/data already exist, so this only actually does anything the first time the app ever runs against a genuinely empty database. |
| `backend/run_dev_sqlite.py` | The local zero-setup launcher — points `DATABASE_URL` at `dev.db`, creates the schema if missing, seeds if empty, then starts the server. |
| `backend/alembic/env.py` + `backend/alembic/versions/*.py` | The migration-based path to creating the schema, normally used for a real PostgreSQL deployment via `alembic upgrade head`. |

## 9. Which files define the schema

Every file under `backend/app/models/` — see Section 3 above. The authoritative,
human-readable documentation of the same schema is `DATABASE_SCHEMA.md` at the
repository root.
