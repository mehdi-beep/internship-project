# Future Integration With the Company's Real Database

This document explains, without implementing anything, how BIMS could later be
connected to the company's real production database instead of the current synthetic
one. **This is a planning document only — no code has been changed.**

---

## 1. Why this is realistic to do later, not now

The specification itself states this as an explicit architectural requirement:
*"The application is currently developed as a web application using a synthetic
database. The architecture must allow easy migration to the company's real database
in the future."* The application was built with this in mind from the start — the
entire data-access layer is written against SQLAlchemy's database-agnostic query API,
and the one and only place in the whole codebase with a database-specific branch is a
single conditional in `backend/app/database/session.py` choosing between a SQLite-safe
and a PostgreSQL-safe connection argument. This is a strong starting position for a
future migration.

## 2. Which files would need to change

| File / area | What would change |
|---|---|
| **`DATABASE_URL` environment variable** (Railway service variable, or local `.env`) | Repointed to the company's real PostgreSQL connection string. This is a configuration change, not a code change — see `backend/.env.example` for the exact format. |
| **`backend/alembic/versions/*.py`** | No *new* migration files are strictly required to point at a different database — the existing migration chain already targets PostgreSQL as its primary dialect. What *would* likely be needed is one new, small migration (or a one-off data-import script, not a schema migration) specifically for **importing the company's existing historical data**, if backfilling old paper records is desired — see Section 5. |
| **`backend/app/database/seed.py`** | Would simply stop being run against the real database. It's a *demo-data generator*, not part of the application's runtime — it's invoked manually (`python -m app.database.seed`) or automatically only as an empty-database safety net (`main.py`'s startup hook). Against an already-populated real database, its own idempotency guard (checking whether the `roles` table is empty) means it would immediately no-op and do nothing, by design — so no code change is even needed to "disable" it, it disables itself automatically. |
| **Reference/master data currently seeded as fake data** (clients, client sites, contracts, projects, the travaux catalog) | These would need to be populated from the company's real records instead of Faker-generated ones — either through a one-off import script, or manually through the existing Admin Supervisor CRUD screens (Users/Clients/Client Sites/Contracts/Projects/Travaux pages), which already fully support creating real records through the normal UI with no code change required. |
| **`CORS_ORIGINS`** (backend) and **`VITE_API_URL`** (frontend) | If the production URLs change (e.g. a company-owned domain instead of the current Railway/Vercel demo URLs), these two environment variables would need updating — again configuration, not code. |

## 3. Which files would remain unchanged

This is the more important half of the answer, and it's a large list precisely
because of the architectural discipline described in `ARCHITECTURE.md`:

- **Every file under `backend/app/models/`** — the schema is already the company's
  intended production schema (derived directly from the specification, not invented
  for demo purposes); a real migration doesn't redesign these, it just runs the
  existing migration chain against a real, empty PostgreSQL instance.
- **Every file under `backend/app/services/`, `backend/app/repositories/`,
  `backend/app/api/`** — all business logic, all query logic, all HTTP routing is
  written against the ORM abstraction, with zero SQLite-specific or demo-data-specific
  logic anywhere except the one connection-argument conditional already mentioned, and
  one dashboard KPI calculation using a SQLite-specific date-difference function
  (flagged explicitly in `ARCHITECTURE.md` and already has its PostgreSQL equivalent
  documented in an inline code comment, ready to swap in at that point).
- **The entire `frontend/` directory** — see Section 4 below; the frontend has no
  awareness of what's "real" versus "synthetic" data at all.
- **`backend/app/authentication/`, `backend/app/middleware/`** — authentication and
  role-based authorization work identically regardless of which database backs them;
  a real user table with real company employees authenticates through exactly the
  same JWT/bcrypt flow as the current demo accounts do.
- **`backend/main.py`, `backend/config.py`** — no change needed; `config.py`'s
  `database_url` field is already a plain required string with no assumption baked in
  about what it points to.

## 4. Would the frontend need modifications?

**No.** The frontend has zero knowledge of where its data comes from — every request
goes through the same typed service functions, hitting the same API endpoints, which
return the same response shapes regardless of whether the row underneath came from
`Faker` or from a real company record. As long as the backend's API contract
(`API_SPEC.md`) stays the same, the frontend requires no code changes whatsoever for
a database migration. The only frontend-facing change would be operational, not
code-level: `VITE_API_URL` might need to point at a new backend URL if the deployment
target itself changes (see Section 2).

## 5. Would the API need modifications?

**Likely not, for the migration itself** — the API's job is to expose the same
14-table schema regardless of which physical database instance backs it. Two
realistic *exceptions* worth naming honestly, though:

- If the company's real internal data model has fields BIMS doesn't currently track
  (e.g. an internal employee ID distinct from a username, a cost-center code on a
  client), those would need new columns (a real schema *extension*, via a new Alembic
  migration) and corresponding new Pydantic schema fields — this is a genuine, if
  likely small, API change, not just a data migration.
- If the company wants BIMS to *read* certain reference data (clients, contracts) live
  from another internal system rather than owning that data itself, that's a much
  bigger architectural change (see "ERP integration" in Section 7) and is explicitly
  out of scope for a simple database migration — worth calling out as a separate,
  larger future initiative rather than conflating the two.

## 6. How to migrate from the synthetic database (recommended strategy)

1. **Provision a real PostgreSQL instance** for the company (already the intended
   production target — no new technology choice needed).
2. **Run the existing Alembic migration chain against it**: `alembic upgrade head`.
   This creates the full, empty, correctly structured schema — the exact same schema
   currently backing the demo, just with zero rows in it.
3. **Do not run `seed.py` against it.** Its idempotency guard would prevent any
   accidental double-seeding regardless, but the deliberate choice here is simply not
   to invoke it at all against a database meant to hold real data.
4. **Populate reference/master data first**, in dependency order (this mirrors exactly
   the order `seed.py` itself follows, for the same reason — later data depends on
   earlier data existing): Users (real employees, correctly assigned to one of the
   three roles) → Clients → Client Sites → Contracts / Projects → the Travaux catalog.
   This can be done through the existing Admin Supervisor UI screens one record at a
   time, or via a one-off bulk-import script (see Section 8) if the company already
   has this data in a spreadsheet or another system.
5. **Decide on historical intervention data separately, as its own decision** — do
   past paper BIs get backfilled into the system, or does BIMS simply start recording
   new interventions going forward from a clean slate? This is a business decision,
   not a technical one, and the two options have very different migration effort
   (a clean start needs no `interventions`-table import at all; a full historical
   backfill needs a real data-mapping and import effort, described next).
6. **Point `DATABASE_URL` at the new PostgreSQL instance** (a Railway service
   variable, or the equivalent on whatever hosting the company ultimately uses) and
   redeploy.
7. **Verify** using the same health-check and login-smoke-test pattern already
   documented in the README's "Running on Railway" section — hit `/api/health`,
   confirm `database_connected: true`, and log in as one real seeded user to confirm
   the connection is genuinely live, not just configured.

## 7. How to map the existing schema to the company's schema

The realistic starting point is that the company's existing paper-based process
almost certainly has *some* existing digital trace to work from (an Excel client
list, a spreadsheet of contracts, etc.) rather than nothing at all. The mapping
exercise, table by table:

- **`clients`** ← the company's existing client/customer list. Map whatever unique
  identifier the company already uses (a client code, a legal name) to `client_name`.
- **`client_sites`** ← the company's existing site/location list per client, if one
  exists; if the company has only ever tracked "which city" informally, this is the
  one table that would need the most manual reconstruction, since BIMS's `city` field
  is always derived from a real `client_sites` row (Rule 4) rather than being a
  free-standing value.
- **`contracts`** / **`projects`** ← the company's existing contract/project records,
  if formally tracked; `start_date`/`end_date`/`status` map directly to whatever date
  range and active/inactive concept the company already uses.
- **`travaux`** ← the company's existing catalog of standard technical operations, if
  one is formally documented; if it currently exists only informally (as handwritten
  notes on paper BIs), this table would need to be built from scratch by having the
  Chef des Techniciens and technicians agree on a standardized operation list —
  arguably a valuable exercise in its own right, since standardizing this vocabulary
  is part of what makes the reporting/KPI features meaningful.
- **`users`** ← the company's employee list, mapped to the three BIMS roles
  (technician / chef_technicien / admin_supervisor). This is likely the most
  organizationally sensitive step — deciding who gets which role is a business
  decision, not a data-mapping one.
- **`interventions`, `approval_history`, `audit_log`** — only relevant if a historical
  backfill is chosen (Section 6, step 5). If the company has scanned copies of past
  paper BIs, each one would map to one `interventions` row plus one `attachments` row
  (the scanned image itself) plus, if the historical approval decision is known, one
  or more `approval_history` rows. This is realistically the most labor-intensive part
  of a full historical migration, since it requires manually re-entering data that
  currently exists only as a physical or scanned document — exactly the kind of task
  a future OCR pipeline (see `future_ai_validation/`) could eventually help
  accelerate, though that's a distinct, larger future initiative and not a
  precondition for this migration.

## 8. Recommended migration strategy (summary)

**Phased, not "big bang":**

1. **Phase 1 — Infrastructure**: provision real PostgreSQL, run migrations, verify an
   empty-but-correctly-structured database, deploy the unchanged application against
   it.
2. **Phase 2 — Reference data**: import real clients/sites/contracts/projects/travaux
   and real user accounts. The application is now fully usable for new work, with
   zero historical intervention data.
3. **Phase 3 (optional, decided separately) — Historical backfill**: if desired,
   import past intervention records as their own project, potentially spread over
   time rather than done all at once, since it's inherently a manual data-entry-heavy
   effort regardless of tooling.

Phasing this way means the company can start using BIMS for real, current work as
soon as Phase 2 is done, without the entire migration being blocked on the much
harder problem of historical backfill.

## 9. Recommended production architecture

The application's current split-deployment architecture (a stateless backend API on
one platform, a static frontend on another, backed by a managed PostgreSQL instance)
is already a reasonable real-production architecture as-is — the main things worth
reconsidering specifically *for* a real company deployment, not because the current
architecture is wrong, but because production stakes are different from a demo:

- **A properly managed, backed-up PostgreSQL instance** rather than the demo's
  SQLite-in-a-container approach — this is already the intended target and requires
  no architectural change, only actually provisioning it (see Section 6).
- **File storage for attachments** — the current local-filesystem upload storage is
  adequate for a demo but is a real production risk on a platform with an ephemeral
  filesystem (as Railway's is by default); a company deployment should either attach
  persistent storage or move attachments to dedicated object storage (already listed
  as a named future improvement).
- **A real, rotated `SECRET_KEY`** — not the development default currently baked into
  the Docker image (already flagged prominently in the README as something to change
  before any deployment is shared beyond a demo).
- **Narrowed CORS** — `CORS_ORIGINS` set to the company's actual frontend domain
  rather than the current wildcard demo default.

## 10. Risks and best practices

- **Do not point the real deployment's `DATABASE_URL` at `dev.db` or any synthetic
  database, ever, once real data exists.** The two must never be conflated — the
  synthetic dataset's entire value is that it's freely disposable and regeneratable;
  a real company's data is not.
- **Take a real backup before running migrations against a populated database**,
  standard practice for any schema change, and doubly important the first time this
  specific migration chain is ever run against something other than an empty or
  synthetic database.
- **Import reference data before ever exposing the real deployment to end users** —
  running with an empty `clients`/`travaux` table against real users would make the
  application unusable for its actual purpose (Rule 3: clients must be selected from
  the database, never typed), so this ordering isn't just a suggestion, it's a hard
  functional dependency.
- **Treat the historical-backfill decision (Section 6, step 5) as its own project**,
  not a blocker on going live — the biggest realistic risk of this whole migration is
  scope creep, where "let's also import 5 years of paper archives" turns a
  straightforward infrastructure migration into an open-ended data-entry project.
  Phasing (Section 8) is the direct mitigation for this.
- **Verify role assignment carefully during the user-import step** — a technician
  accidentally imported as `admin_supervisor` (or vice versa) is a real, checkable
  permissions mistake with immediate consequences, precisely because the role system
  in this application is genuinely enforced (see `ARCHITECTURE.md` Section 1.5), not
  cosmetic.
- **Re-run the automated test suite against the new PostgreSQL instance before
  declaring the migration complete** — the suite currently runs against SQLite in
  every environment it's been executed in so far; a real migration to PostgreSQL is
  exactly the kind of change worth confirming the suite still passes against, given
  the one known SQLite-specific calculation flagged in Section 2.
