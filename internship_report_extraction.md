# Internship Report — Information Extraction
### Project: BIMS (Bon d'Intervention Management System)
### Purpose: raw, organized material for writing a 10–15 page engineering internship report. This document is extraction and organization only — it is not the report itself.

---

# PART 1 — Internship Context

**Project title:** Bon d'Intervention Management System (BIMS), stated verbatim in the specifications document: *"The Bon d'Intervention Management System (BIMS) is a web-based application designed to replace the company's current paper-based intervention workflow."*

No company name, supervisor name, or academic institution is stated anywhere in the repository — these must be supplied when the report is written. No internship title is stated either; based on the technical scope actually delivered (full-stack web application, backend API design, database architecture, DevOps/deployment configuration), a title such as *"Full-Stack Development of a Digital Intervention Management System"* or *"Design and Implementation of a Web Platform for Technical Intervention Management"* would accurately reflect the work — to be finalized against the school's own template.

**General objective** (verbatim from the specifications): *"Create a centralized web platform capable of managing the complete lifecycle of technical interventions from planning to final approval while maintaining complete traceability."*

**Specific objectives stated in the specification** (the application "shall"):
- Replace paper-only management with digital management.
- Reduce administrative work.
- Improve intervention traceability.
- Preserve the signed paper document by attaching its image.
- Allow technicians to submit interventions digitally.
- Support two-level approval.
- Calculate technician points automatically.
- Calculate working duration automatically.
- Manage intervention planning.
- Dispatch urgent interventions.
- Produce dashboards and KPIs.
- Generate reports.
- Maintain complete intervention history.
- Prevent data loss.
- Eliminate manual calculations.
- Improve productivity.

**Long-term objectives explicitly out of first-version scope:** Mobile application, OCR, Artificial Intelligence, Predictive analytics, Automatic planning optimization, Cloud deployment, Multi-company support.

**Context of the internship:** the internship centers on building a production-grade internal tool for a company that currently manages every field/workshop technical intervention on paper. The company issues a "Bon d'Intervention" (BI) — an official intervention document — for every job a technician performs, whether at a client's premises or in the company workshop. The digitization project was scoped explicitly to preserve the existing business process rather than redesign it: *"The objective of this project is to digitize the entire workflow while preserving the existing business process used by the company."*

**Why the application was needed / the existing problem inside the company** (verbatim, specifications Ch.1): *"Currently, technicians complete a physical Bon d'Intervention after every intervention performed at a client's premises or inside the company's workshop. The document contains technical information, administrative information, work performed, signatures and various references. The current workflow is entirely manual. After completion, the paper document is physically transported to the company where different supervisors validate it before archiving it."* This process was documented as generating nine distinct categories of problems, detailed in full in Part 2 below.

**Expected benefits:** the mirror image of the nine documented problems — faster approvals (no physical transport delay), reduced document loss risk, searchable digital records, automated duration and point calculations (eliminating manual arithmetic errors), a centralized planning system replacing verbal/phone-based assignment, a real notification system, management-facing statistics/KPIs that were previously impossible to answer, elimination of duplicate paper-then-digital re-entry, and full accountability/traceability of who did what and when.

**Important framing note for the report:** the specification explicitly states the digital paper trail does **not** replace the physical signed document's legal status — the photographed/scanned paper BI remains the client-signed legal record; the digital system is the operational and administrative layer on top of it: *"The digital application must become the primary platform used by technicians and supervisors while still keeping the scanned (photographed) paper form as the legal signed document."*

---

# PART 2 — Problem Analysis

## The prior workflow (8 steps, before digitization)

1. **Intervention Assignment** — the company receives a request from a client (planned in advance, part of a maintenance contract, related to a project, or urgent). The Chef des Techniciens assigns one or more technicians verbally/manually.
2. **Technician Performs the Work** — technician travels to the client site ("Sur Site") or works in the company workshop ("Atelier").
3. **Paper Bon d'Intervention** — after the work, the technician manually fills a paper BI by hand: client, city, date, technician, work performed, intervention type, duration, comments, client signature.
4. **Client Signature** — the client verifies and signs; this signature is the legal proof of completion.
5. **Return to Company** — the technician physically carries the paper document back — same day, next day, or several days later.
6. **Technical Validation** — the Chef des Techniciens manually reviews technical quality, work performed, correct intervention type, and comments; if unacceptable, corrections are requested.
7. **Administrative Validation** — the Administration Supervisor manually checks dates, administrative information, completeness, and formal correctness.
8. **Archiving** — the paper is filed away; retrieval later requires manual searching through physical archives.

## Explicitly documented problems (9 categories, verbatim from the specification)

| # | Problem | Description |
|---|---|---|
| 1 | **Document Loss** | Paper documents may be lost, damaged, or misfiled. |
| 2 | **Slow Validation** | Approvals cannot begin until the paper physically reaches the company, delaying the whole workflow by days. |
| 3 | **Manual Calculations** | Working duration and technician points are calculated by hand, increasing the risk of errors. |
| 4 | **Difficult Searching** | Finding a specific intervention in physical archives can take minutes or even hours. |
| 5 | **No Planning Module** | No centralized system exists; assignments are communicated manually (phone/verbal). |
| 6 | **No Notification System** | Technicians learn of assignments through phone calls, with no centralized alerting. |
| 7 | **No Statistics** | Management cannot answer basic operational questions: interventions per month, top-performing technicians, highest-workload clients, average duration, urgent-intervention counts. |
| 8 | **Duplicate Information** | Information exists only on paper; any digital use requires manually re-transcribing the same data. |
| 9 | **Limited Traceability** | It is difficult to determine who modified information, who approved it, when, or why something was rejected. |

## Limitations of the manual process

The manual process fundamentally could not support any of the modern operational needs a growing service company requires: it had no mechanism for real-time visibility into technician workload, no way to prioritize urgent client requests systematically, no audit trail beyond whatever notes happened to be handwritten on the paper form, and no aggregate reporting capability at all — every KPI question required manually counting paper documents.

## Why digitization was necessary

Digitization directly targets each of the 9 documented problems while explicitly preserving the underlying business process (assignment → execution → paper signature → two-level validation → archiving) rather than reinventing it. The specification frames this precisely: the paper form's *legal* role (client signature) is preserved by photographing/attaching it, while every *operational* aspect around it — assignment, submission, calculation, validation, notification, search, and reporting — moves to a centralized, auditable digital system.

---

# PART 3 — Proposed Solution

## Overall concept

BIMS reproduces the company's existing 8-step paper workflow as a digital pipeline while eliminating its administrative overhead. The core design principle, stated explicitly in the specification: *"The digital application reproduces the existing business workflow while eliminating manual administration. The paper BI remains important because it contains the client's handwritten signature. However, instead of transporting only the paper, the technician also submits a digital version immediately."*

The new digital workflow: Client requests intervention → Chef des Techniciens schedules it → Technician receives assignment (digital notification) → Technician performs the intervention → Technician completes the digital BI form → Technician photographs/uploads the signed paper BI as an attachment → Technician submits both together → Technical approval (Chef des Techniciens) → Administrative approval (Administration Supervisor) → Intervention becomes Fully Approved → Stored permanently, immutable → Available for dashboards and reports.

## Main objectives (system-level)

- A single source of truth for every intervention's full lifecycle, from creation through both approval stages.
- Automatic, error-free calculation of working duration and technician points (removing human arithmetic entirely from these two areas).
- A real digital planning/scheduling module replacing verbal assignment, including a dedicated fast-path for urgent interventions.
- A centralized, role-aware notification system.
- Role-based dashboards providing real-time KPIs previously impossible to obtain.
- A reporting module (10 report types) with PDF/Excel export.
- Complete, permanent, immutable audit history — nothing about an intervention is ever deleted, only its status changes.

## Expected impact

Faster approval cycles (no physical document transport delay for the digital review step), elimination of calculation errors, dramatically reduced search time (a database query instead of a physical archive search), real operational visibility for both the Chef des Techniciens and the Administration Supervisor, and a durable, queryable historical record supporting both compliance and performance-management needs.

## Users involved (the three roles)

The specification is explicit that there are **only three roles** — there is no separate "Administrator" account; the Administration Supervisor performs top-level administrative duties directly:

1. **Technician** — creates, edits (while still Draft/Rejected), and submits interventions; views their own history and calendar; receives notifications relevant to their own work.
2. **Chef des Techniciens** — schedules/plans interventions and assigns technicians, dispatches urgent work, performs the first (technical) approval, views all interventions and all technicians' workload.
3. **Administration Supervisor** — performs the second (administrative) approval, manages all reference/master data (users, clients, sites, contracts, projects, travaux catalog), and has full reporting/dashboard access. Everything a "system administrator" would normally do in a smaller application is folded into this single role, by explicit design.

---

# PART 4 — My Technical Contribution

*This section should be written in the first person ("I designed...", "I implemented...") in the final report. It is organized here by technical area, drawing on the actual, specific engineering decisions made and problems solved throughout the internship — not a generic restatement of what the finished application does.*

## Architecture and design decisions

I structured the backend around a strict four-layer separation that I maintained without exception across the entire codebase: **API routers** (HTTP concerns only — request parsing, response shaping, role authorization via dependency injection), **services** (100% of business logic and calculations), **repositories** (all database query construction), and **models** (SQLAlchemy ORM definitions). This is not an incidental pattern — I actively enforced it during every feature addition and every bug fix: when I found, late in the project, that the approval-decision endpoints were bypassing a service-layer helper by calling a repository function directly, I treated that as an architectural bug and fixed it by routing both approval-decision code paths through the same single service function, rather than patching the symptom twice.

I made the deliberate architectural decision that the frontend must never recalculate anything the backend already computes — durations, points, and status transitions are always backend-authoritative, with the frontend only ever displaying a read-only preview labeled explicitly as an estimate pending backend confirmation (visible directly in the intervention form's duration preview, which is annotated in the code as client-side-only until the server value is available).

## Business logic

I implemented the core business-rule engine as a small set of pure, isolated, spec-traceable functions rather than scattering calculations across the codebase:
- The **duration calculation** (gross duration minus lunch break equals net duration), with an explicit guard rejecting a lunch break that exceeds the gross working window.
- The **point system**, a four-tier time-of-submission incentive scale (17:00–19:00 → +5, 19:00–22:00 → +2, 22:00–24:00 → +1, any other hour → a flat penalty), which I implemented with correct timezone handling — converting the submission timestamp from UTC (stored) to the company's local Africa/Casablanca time before evaluating which window applies, since a technician's "I submitted at 17:30" must mean their own local wall-clock time, not a server clock that could be running in a different zone.
- The **9-state intervention lifecycle state machine**, expressed as a single, explicit transition table that every status-changing operation in the application must pass through — no code anywhere in the application is permitted to set an intervention's status directly without going through this validator, which rejects illegal transitions with an HTTP 409.
- I identified and resolved a real ambiguity in the specification during implementation: the written spec describes 9 literal lifecycle states, but its own approval diagrams show two of those states (Submitted, Technical Approved) as always auto-advancing within the same user action to the next state. I resolved this by implementing the transition table to jump directly to the queue-visible state, while still recording the intermediate step's occurrence via a timestamp column — a decision I made explicitly to keep the system's actual observable behavior consistent with the specification's own workflow diagrams rather than its literal state list.

## Database design

I worked from a specification-driven schema across 14 tables, and I extended it three times during development as new features required it — each extension implemented as a proper, reversible Alembic migration rather than an ad-hoc schema change:
- Added a self-referential foreign key on the intervention table (`warranty_reference_id`) supporting warranty-type interventions that must reference a real, previously created BI record.
- Added a many-to-many join table for colleague/participating technicians on an intervention, explicitly designed so the lead technician (the intervention's owner) is never duplicated into that join table — a business rule I encoded directly into the schema's design rather than leaving it to application-level convention.
- Added a persisted manual-ordering column supporting a drag-and-drop urgent-intervention queue for the Chef des Techniciens' dashboard.
- Added a second nullable foreign key on the notifications table so planning-triggered notifications can deep-link back to their originating planning entry, mirroring the existing intervention-linking foreign key.

I enforced referential integrity throughout: every foreign key that must always resolve is declared `NOT NULL`; type-specific optional relationships (contract/project/warranty reference) are nullable and validated at the service layer against the selected intervention type; and I structurally prevented hard deletes on the audit-sensitive tables (interventions, approval history, audit log) by never issuing a `DELETE` against them anywhere in the application code, using status transitions and soft-delete flags (`active`, `archived`) instead.

## Backend implementation

I implemented the full REST API surface — authentication, all six reference-data CRUD modules, planning/scheduling, the intervention lifecycle, attachments, the two-level approval workflow, three role-specific dashboards plus a shared period-aware charting subsystem, a ten-report-type reporting module with PDF/Excel export, and a technician-performance analytics module.

Two specific implementation problems I identified and solved independently, beyond straightforward feature-building:

- **A genuine, undocumented reliability gap in application startup.** I discovered that the normal application boot path had no schema-creation or seed-data step at all — it only worked in every environment tested because the database file it happened to be reading already had everything pre-built into it. I added a startup safety net (a schema-creation call plus the already-idempotent seed routine, both of which I confirmed are safe no-ops against an already-initialized database) so a genuinely empty database — a fresh volume, a newly provisioned database instance — self-initializes correctly instead of crashing on the very first query. I verified this by deliberately booting the application against a brand-new, empty database file and confirming it created the full schema and seeded all demo accounts correctly, then rebooted it a second time against that same file and confirmed no duplicate data was created.

- **A CORS/authentication interaction bug specific to cross-origin deployment.** When separating the frontend (static hosting) from the backend (a separate API host), I found the backend's CORS configuration allowed credentialed requests, which is incompatible with a wildcard allowed-origin list under the CORS specification — browsers silently reject that combination. Since I confirmed the application's authentication is entirely Bearer-token-based (no cookies anywhere in the frontend), I removed the unnecessary credentialed-request allowance, which made the wildcard origin configuration valid and browser-safe again. I verified the fix with a genuine cross-origin request test (not just a same-origin check) — issuing a real CORS preflight and a real POST request from a different local origin and confirming the correct response headers came back — rather than assuming the fix was correct from code inspection alone.

## Database migrations and evolution

I authored the incremental schema-evolution migrations described above as the corresponding features were built, each scoped narrowly to exactly the columns/tables a given feature needed, keeping every migration purely additive (no destructive column drops or renames across the project's migration history) so the schema could evolve safely without ever requiring a data-loss-risking rollback.

## Frontend implementation

I built the majority of the application's page-level UI on top of a small number of deliberately reusable components rather than one-off implementations per page — a generic paginated data table used by every list view in the application (interventions, approvals, reports, all six admin reference-data pages), a generic calendar wrapper reused for both the interventions calendar view and the planning calendar (each with its own domain-specific event-coloring logic layered on top), and a shared period-mode selector driving the charting subsystem identically across all three role dashboards.

I designed and implemented the full-screen split-screen intervention review interface used throughout the approval workflow: a left panel presenting a completely denormalized, human-readable view of every stored field (resolving every foreign key — client, site, technician, contract, project, warranty reference — to its display name rather than showing a raw database ID anywhere) synchronized against a right panel presenting the attached paper-BI photograph with pan/zoom controls and multi-attachment navigation, so a reviewer can compare the digital record against the physical signed document without leaving the review screen.

I also implemented the intervention creation/edit form's multi-step conditional logic (a single intervention-type selector that reveals exactly one of three mutually exclusive dependent fields — contract, project, or warranty reference — depending on the selected type), the read-only lockout behavior that mirrors the backend's own edit-permission rules (a submitted-and-pending intervention becomes fully non-editable on the frontend, not just rejected server-side if someone tries), and the responsive application shell (a full sidebar on desktop, a collapsed icon-only rail on tablet, and a temporary slide-out drawer on mobile).

## Authentication

I implemented the authentication system end to end: password hashing using bcrypt directly (choosing the library deliberately over a higher-level wrapper after identifying a real compatibility break in that wrapper library's own self-test code under a newer bcrypt version — a decision I made and documented specifically to avoid a broken dependency rather than working around the symptom), JWT-based session tokens carrying the user's identity and role, a role-based-access-control dependency used uniformly across every protected endpoint in the API, and the frontend session layer (token storage, automatic attachment of the bearer token to every outgoing request, and a global 401-response handler that transparently logs the user out and redirects to the login page without requiring every individual page to handle that case itself).

## Dashboards

I designed and implemented three genuinely distinct, role-appropriate dashboards (not a single dashboard with role-based field-hiding) plus a shared, reusable period-aware charting subsystem: a Day/Week/Month period selector that drives every chart on a given dashboard simultaneously through one consolidated API call per dashboard, rather than one request per chart. I extended this subsystem to a fourth, cross-role technician-performance view, letting the Chef des Techniciens and Administration Supervisor drill into any individual technician's own performance metrics and activity history through the same visual language as the main dashboards.

## Notifications

I implemented the centralized notification system covering every trigger event the specification requires — new assignment, urgent assignment, planning modified, planning cancelled, submission received (routed to every active Chef des Techniciens, since the specification does not designate a single supervisor to route to), technical approval granted (routed to every active Administration Supervisor), rejection (at either approval level), and full approval — and built the frontend notification-routing logic that inspects a notification's content to deep-link the user directly to the relevant intervention or planning entry, including auto-opening the correct edit modal on the planning page when a user arrives via a planning-related notification.

## Planning

I implemented the scheduling/planning module used exclusively by the Chef des Techniciens role, including the urgent-intervention fast path (immediate notification, dashboard-level highlighting) and a persisted, drag-and-drop-reorderable urgent-intervention queue — a feature I added after the initial implementation, requiring a schema migration, a new reordering endpoint with an explicit all-or-nothing validation rule (every entry in a reorder request must already be an active urgent entry, or the entire request is rejected), and a frontend drag-and-drop component with optimistic local reordering.

## Reports

I designed the reporting module's endpoint architecture deliberately to avoid ten near-duplicate endpoints: eight of the specification's ten report types (Daily, Weekly, Monthly, Yearly, Technician, Client, Project, Contract) are all structurally "a list of interventions matching a filter set," differing only in which filter is pre-applied by the frontend — so I implemented them as one consolidated, generically filterable endpoint rather than one bespoke endpoint per report type, with the two structurally different report types (Approval history, Planning) as their own separate endpoints. I implemented PDF and Excel export for every report type with consistent, styled output (a common header-row treatment, alternating row shading) shared across both export formats.

## Deployment

I took the application from a locally-runnable-only state to a fully deployed, split-architecture production configuration:
- Diagnosed and fixed a hard startup crash on the deployment platform, tracing it to two required configuration fields with no safe defaults, and to a second, independent bug where a Postgres-specific database-connection argument would have broken any SQLite-backed deployment even after the first issue was fixed.
- Configured the backend container image to boot correctly with zero platform-side configuration by shipping a working, pre-seeded demo database inside the image itself, while documenting precisely what must be overridden (and why) before any real deployment is shared publicly.
- Configured the frontend for static hosting on a separate platform from the backend, including the single-page-application routing rule needed so a direct page load or refresh on any client-side route resolves correctly instead of returning a 404.
- Diagnosed and fixed the resulting cross-origin (CORS) misconfiguration between the two now-separately-hosted services, as described above.
- When a live login failure was reported against the deployed application, I investigated the actual production system directly (rather than reasoning from code alone), tested every seeded account systematically against the live deployment, isolated the failure to a single account via direct evidence (a timestamp inconsistency proving that one account's password had been legitimately changed at some point, rather than assuming a systemic bug), and fixed both the specific data issue and the underlying reliability gap that made a truly empty deployment target unrecoverable, verifying the fix against the live production system after redeploying — not just locally.

## Git workflow

Work was organized as a sequence of focused, independently describable rounds of change, each committed with a message explaining the "why" behind the change rather than only the "what" — the repository's commit history documents, in order: the initial full-application implementation; a first correction pass covering collaboration features, calendar consolidation, dashboard restructuring, an urgent-queue drag-and-drop feature, and a point-system rule change; a Railway deployment fix bundled together with an intervention-review completeness pass and a new Administration Supervisor navigation entry; a split-deployment configuration pass (Vercel frontend, Railway backend) with its own CORS fix; and a final production-diagnosis-and-fix round for the reported login failure. Each round of backend changes was verified against the project's full automated test suite before being committed, and deployment-affecting changes were additionally verified against the actual live, running system rather than assumed correct from local testing alone.

---

# PART 5 — Development Methodology

## Requirement gathering

The starting artifact was a complete, pre-existing written specification (`project_specifications.md`, 154 chapters) functioning as a full Software Requirements Specification (SRS) — this document served as the single source of truth for every subsequent design and implementation decision. Rather than gathering requirements through open-ended discovery, the methodology here was to read the specification exhaustively first and treat every subsequent decision as a traceable derivation from it.

## Analysis

Before any code was written, the specification's data model implications (Chapters 33–53), API surface implications (Chapters 79–87), and business-rule implications (the ten formally numbered rules in Chapter 10, plus the consolidated rule summaries in Chapters 20 and 32) were extracted and cross-checked against each other for internal consistency — this analysis phase produced the three companion documents described next.

## Specification writing

Three derivative technical documents were authored directly from the SRS before implementation began: `DATABASE_SCHEMA.md` (the full relational schema, sourced explicitly from specification Chapters 33–53), `API_SPEC.md` (the complete endpoint inventory with role-authorization mapping, sourced from Chapters 79–87), and `TASKS.md` (a ten-phase implementation plan). Writing these derivative specs before coding served as a design-validation step in its own right — deriving a concrete schema and API surface from prose requirements surfaces ambiguities that reading the prose alone does not.

## Architecture design

The layered backend architecture (API → services → repositories → models) and the corresponding frontend architecture (pages → reusable components → services → typed API client) were established at the very start of implementation (Phase 1) and deliberately never violated afterward — every subsequent phase's code additions were required to fit into this existing structure rather than introducing parallel patterns.

## Database design

The schema was designed in its near-entirety in Phase 2, directly from `DATABASE_SCHEMA.md`, and evolved only additively afterward (three small, targeted migrations across the rest of the project, as described in Part 4) — the core domain model was correct enough from the initial specification-driven design that no destructive schema change was ever required.

## Development phases

Implementation proceeded through ten sequential phases, each building strictly on the previous phase's completed foundation: (1) Project Initialization — scaffolding, tooling, and a minimal auth skeleton on both ends; (2) Database — the full 14-table schema, models, migration, and a deterministic synthetic-data generator; (3) Authentication — the complete login/session/role-authorization flow; (4) Reference Data CRUD — the six master-data modules (users, clients, sites, contracts, projects, travaux) on both ends; (5) Planning Module; (6) Intervention Module — the core creation/submission workflow; (7) Business Logic — the calculation and state-machine services, implemented as a dedicated phase specifically because two real gaps were found in the Phase 6 implementation during this pass (a missing notification trigger, and a silently-broken notification-persistence bug) and fixed at that point rather than carried forward; (8) Approval Workflow — the two-level approval process; (9) Dashboards and Reporting; (10) Testing, Cleanup, and Documentation — the full automated test suite, a UAT walkthrough against the specification's own scenarios, a responsive-design audit (which found and fixed a real mobile-sidebar defect), and final documentation.

## Testing

An automated backend test suite (pytest, 122 tests as of the project's current state) was built and maintained throughout, covering authentication, every business-logic calculation, the full status-transition state machine, planning, the intervention lifecycle, the complete two-level approval workflow (including both rejection branches), reference-data CRUD, all three dashboards, reporting/export, and the technician-performance module. Each test runs against a freshly created, freshly seeded database rather than a shared fixture or mocked data layer — a deliberate choice ensuring every test exercises the real seed-data generation logic and real database constraints rather than an idealized mock.

## Deployment

Deployment was treated as its own explicit final phase, not an afterthought: the backend was containerized and deployed to a managed platform with a working zero-configuration default, the frontend was deployed separately as a static build to a different hosting platform, and the cross-origin networking between the two was diagnosed and fixed as its own discrete piece of work, with every deployment-affecting change verified against the actual live, running deployment before being considered complete.

## Why this order was chosen

The order follows a strict dependency chain: nothing can be built before the schema exists to store it (hence Database precedes every feature phase); nothing can be protected by role without an authentication system (hence Authentication precedes every role-gated feature); reference data (clients, sites, the travaux catalog) must exist before an intervention can meaningfully reference it (hence Reference Data CRUD precedes the Intervention Module); the intervention record must exist before it can be approved (hence the Intervention Module precedes the Approval Workflow); and dashboards/reporting are, by definition, aggregations over data produced by every earlier phase, so they could only be meaningfully built last among the feature phases. Testing and deployment were placed at the end deliberately — testing validates the complete, integrated system rather than isolated units built in a vacuum, and deployment configuration is inherently the very last concern, since it depends on every other part of the application already being functionally complete.

---

# PART 6 — Technologies

## Backend

**Python 3** — the implementation language for the entire backend. Selected as the natural choice for a specification-driven REST API with a strong emphasis on data validation and business-rule correctness, given Python's mature ecosystem for exactly that combination (FastAPI, Pydantic, SQLAlchemy).

**FastAPI** — the web framework powering the entire API layer. What it is: a modern, high-performance Python web framework built specifically around type hints and automatic request/response validation. Why selected: it generates interactive API documentation automatically from the same type-annotated function signatures used to define endpoints, eliminating a whole category of documentation drift, and its native async support and dependency-injection system (used throughout the project for the `get_db` session-per-request pattern and the `require_roles` role-authorization pattern) map cleanly onto the layered architecture used here. Where used: every route handler across all 16 API router modules. Advantage for this project: the dependency-injection mechanism let role-based authorization be expressed as a single reusable, composable function (`require_roles(...)`) rather than duplicated authorization checks scattered through every handler.

**SQLAlchemy (2.0-style declarative mapping)** — the Object-Relational Mapper used for every database interaction. What it is: Python's most widely used ORM, mapping Python classes to database tables and Python method calls to SQL queries. Why selected: it supports both PostgreSQL (production) and SQLite (local development/demo) through the same codebase with no application-level branching beyond a single connection-argument difference, which was essential to this project's dual-database strategy. Where used: every model in `app/models/`, every query in `app/repositories/`. Advantage for this project: the repository layer's queries are portable between the two supported databases with zero query-level changes.

**Alembic** — the database migration tool. What it is: SQLAlchemy's official schema-migration framework, tracking an ordered chain of versioned, reversible schema changes. Why selected: it's the standard companion to SQLAlchemy and integrates directly with the same model definitions. Where used: four migrations tracking the schema's full evolution from an initial auth-only baseline through the complete domain model to the current state. Advantage: every schema change is reproducible and reversible, and the migration chain itself documents the project's schema evolution history.

**Pydantic (via pydantic-settings)** — used for two distinct purposes: request/response schema validation (every API input and output is a Pydantic model) and typed application configuration (the `Settings` class, loading from environment variables with type coercion and validation built in). Why selected: it's FastAPI's native validation layer, so adopting it was effectively free given the FastAPI choice, and it gives configuration errors (like the ones diagnosed in the deployment-fix work) precise, structured error messages rather than a runtime crash with no clear cause.

**JWT (via python-jose)** — the authentication token format. What it is: a self-contained, cryptographically signed token carrying the authenticated user's identity and role. Why selected: it's stateless — the backend never needs to look up a session store to validate a request, only to verify a signature and check an expiry — which is a good fit for a REST API with no server-side session state elsewhere in the design. Where used: issued at login, verified on every protected request via the `require_roles`/`get_current_user` dependency chain. Advantage: combined with the frontend's Bearer-token-only design (no cookies), this also simplified the cross-origin deployment configuration, since credentialed cross-origin requests (which carry real security complexity) were never needed.

**bcrypt** — the password-hashing library. What it is: a battle-tested, deliberately slow adaptive hashing algorithm designed specifically to resist brute-force password cracking. Why selected directly (rather than through a wrapper library): a compatibility break was found in the more commonly used wrapper library's own internal self-test code under a newer bcrypt release, so the raw library was used directly instead — a concrete example of a small technology decision made in response to a real, verified problem rather than by default preference.

**PostgreSQL** — the production-grade relational database target. What it is: a mature, standards-compliant open-source relational database. Why selected: the specification calls for it explicitly as the intended production database, and it's the natural choice for a system with the referential-integrity and concurrent-write requirements this application has. Where used: the primary target for the Docker Compose local-development stack and the intended target for a real production deployment.

**SQLite** — the secondary, zero-setup database option used for local development, demonstration, and the current production deployment. What it is: a serverless, single-file relational database. Why selected as a *secondary* option (not a replacement for PostgreSQL): it lets the entire application run with no external service dependency at all, which was decisive for making the project immediately clonable and runnable by anyone with no setup beyond a Python environment, and equally decisive for making the deployed demo environment boot successfully with zero platform-side database provisioning. Advantage for this project specifically: the same schema and business logic run correctly against both databases, proven by the fact that the full automated test suite runs against SQLite in every environment it's been executed in throughout the project, including in the sandboxed development environment where no external database service was available at all.

**reportlab** — PDF generation library, used for the "Export PDF" feature across all three report types.

**openpyxl** — Excel (.xlsx) generation library, used for the "Export Excel" feature across all three report types. Chosen alongside reportlab specifically because the reporting module's design (see Part 4) needed both output formats to share the same underlying filtered-data query, with only the rendering step differing.

**Faker** — synthetic-data generation library, used exclusively in the seed-data generator to produce realistic (but fictitious) names, companies, addresses, and phone numbers. Why selected: it produces demographically plausible, non-repetitive fake data far faster and more realistically than hand-written fixture data would, which was essential given the scale of the synthetic dataset (650 interventions, 22 clients, 14 users, and more) needed to make the dashboards and reports meaningfully demonstrable.

**pytest** — the backend test framework. Why selected: it's the de facto standard Python test runner, with a fixture system well suited to this project's per-test fresh-database pattern (a single `client` fixture in `conftest.py` fully rebuilds and reseeds an isolated database for every individual test).

## Frontend

**React 19** — the UI framework. What it is: a component-based JavaScript library for building user interfaces via a declarative, composable model. Why selected: its ecosystem maturity and the team's/developer's familiarity made it the natural choice for a data-heavy, role-differentiated multi-page application. Where used: the entire frontend, organized as roughly 30 page components built from a shared library of reusable components.

**TypeScript** — used for the entire frontend codebase, with no plain JavaScript files. Why selected: given the number of distinct data shapes flowing between backend and frontend (14+ typed entities, each with list and detail variants), static typing catches an entire category of integration bugs (a renamed or restructured backend field) at compile time rather than at runtime in front of a user.

**Vite** — the frontend build tool and development server. What it is: a fast, modern build tool built around native ES modules during development and Rollup-based bundling for production. Why selected over older bundlers: near-instantaneous development-server startup and hot-module-reload, which matters directly for iteration speed across a project with this many distinct pages. Where used: both the local development server and the production build (`tsc -b && vite build`) that gets deployed as a static site.

**Material UI (MUI)** — the component/design system. What it is: a comprehensive React component library implementing Google's Material Design guidelines. Why selected: it provided a complete, accessible, professionally-styled component set (tables, dialogs, forms, navigation, data display) out of the box, letting implementation effort focus on the application's actual data flows and business logic rather than on building a design system from scratch. Where used: essentially every visual element in the application, including the fully responsive application shell (desktop sidebar / tablet icon rail / mobile drawer) built on MUI's breakpoint system.

**React Router** — client-side routing. What it is: the standard routing library for React single-page applications. Why selected: it's the ecosystem standard and integrates cleanly with a role-based route-protection wrapper component, which is exactly how access control is enforced on the frontend in this project (a single `ProtectedRoute` component, parameterized by an optional allowed-roles list, wrapping every protected route).

**TanStack Query (React Query)** — server-state management. What it is: a library that manages the full lifecycle of asynchronous server data — fetching, caching, background refetching, and cache invalidation after mutations — as a distinct concern from client-side UI state. Why selected: rather than manually tracking loading/error/data state and manually re-fetching after every mutation (the traditional `useEffect` + `useState` pattern), this project's entire data layer runs through TanStack Query's query-key-based caching model, which is why no separate global state-management library (like Redux) was needed at all — the only client-side global state in the whole application is the authentication context.

**Axios** — the HTTP client. Why selected: its interceptor system was used directly to implement two cross-cutting concerns cleanly — automatically attaching the authentication bearer token to every outgoing request, and globally handling any 401 response by clearing the session and notifying the rest of the application via a custom event, without either concern needing to be repeated in every individual API call.

**React Hook Form** — form state management and validation. Why selected: it minimizes re-renders on every keystroke (relevant given the intervention form's size — nine distinct sections with interdependent conditional fields) by using uncontrolled inputs with a subscription model, and its `Controller`/`useWatch` primitives were used specifically to implement the intervention form's conditional field logic (client selection cascading into site options; intervention type selection revealing exactly one of three mutually exclusive dependent fields).

**FullCalendar** — the calendar rendering library, used for both the interventions calendar view and the planning calendar. Why selected: it provides production-grade month/week/day calendar views with built-in event-click and visible-range-change hooks out of the box, which this project relies on directly to drive its own data-fetching (refetching whatever date range the user has currently navigated to, rather than fetching the entire dataset up front).

**Recharts** — the charting library backing every dashboard chart (bar and line charts across all three role dashboards and the technician-performance view). Why selected: a React-native charting library with a declarative component API, fitting the same component-composition model as the rest of the frontend rather than requiring imperative canvas manipulation.

**Day.js** — date/time handling, including its `isoWeek` plugin, deliberately enabled globally specifically to make the frontend's week-boundary calculation match the backend's own Monday-start week convention — a small but consequential decision, since a mismatch here would have caused the Week-mode dashboard charts to silently disagree between what the user selected and what data the backend actually returned.

**dnd-kit** — drag-and-drop, used specifically and only for the Chef des Techniciens' urgent-intervention-queue reordering feature. Why selected over older drag-and-drop libraries: it's built for React's current rendering model natively (no legacy HTML5 drag-and-drop API workarounds) and its pointer-sensor activation-distance configuration was used directly to prevent accidental drags from interfering with normal clicks on the same list items.

**react-zoom-pan-pinch** — used specifically inside the intervention-review split-screen viewer, to let a reviewer pan and zoom into the photographed paper BI attachment. Why selected: it's a focused, single-purpose library for exactly this interaction pattern, rather than pulling in a larger, more general image-gallery library for a single well-defined need.

## Deployment technologies

**Docker / Docker Compose** — used for the local, full-stack development environment (Postgres + backend + frontend running together with live code reload) and as the deployment artifact format for the backend (a standalone Dockerfile, independent of the Compose file, used by the production hosting platform).

**Railway** — the backend hosting platform. Selected as a managed container-hosting platform that deploys directly from a Dockerfile with minimal configuration, which was directly relevant to the deployment-fix work described in Part 4 (making the container boot correctly with sensible, safe defaults and zero required platform-side configuration for a first deploy).

**Vercel** — the frontend hosting platform, selected specifically because it's purpose-built for static frontend builds with automatic framework detection (recognizing the Vite build output with no manual build-command configuration needed) and because separating frontend and backend hosting concerns onto their purpose-built platforms (a static host for the frontend, a container host for the backend) is a more standard, more scalable split-deployment pattern than hosting both together.

---

# PART 7 — Software Architecture

## Global architecture

```
┌─────────────────────┐        HTTPS / JSON        ┌──────────────────────┐
│   Frontend (Vercel)  │ ◄─────────────────────────► │  Backend API (Railway)│
│  React + TypeScript  │      Bearer JWT auth         │   FastAPI + Uvicorn   │
│  Static build (Vite) │                              │                        │
└─────────────────────┘                              └──────────┬───────────┘
                                                                   │
                                                                   │ SQLAlchemy
                                                                   ▼
                                                        ┌──────────────────────┐
                                                        │      Database         │
                                                        │  PostgreSQL (prod) or  │
                                                        │  SQLite (dev/demo)     │
                                                        └──────────────────────┘
```

The two halves of the application are fully decoupled: the frontend is a static build with no server-side rendering and no knowledge of the backend beyond a single configured base URL; the backend is a stateless REST API with no knowledge of the frontend at all beyond which origins are allowed to call it. This decoupling is what allowed the two to be deployed independently, onto two different hosting platforms, as described in Part 4.

## Backend architecture (layered)

```
┌─────────────────────────────────────────────────────────┐
│  API Layer (app/api/*.py)                                 │
│  HTTP routing, request parsing, role authorization only    │
│  — zero business logic                                     │
└───────────────────────────┬─────────────────────────────┘
                              │ calls
                              ▼
┌─────────────────────────────────────────────────────────┐
│  Service Layer (app/services/*.py)                         │
│  100% of business logic: calculations, state machine,       │
│  validation, notification triggering                        │
└───────────────────────────┬─────────────────────────────┘
                              │ calls
                              ▼
┌─────────────────────────────────────────────────────────┐
│  Repository Layer (app/repositories/*.py)                  │
│  All database query construction (SQLAlchemy)               │
└───────────────────────────┬─────────────────────────────┘
                              │ maps to
                              ▼
┌─────────────────────────────────────────────────────────┐
│  Model Layer (app/models/*.py)                             │
│  SQLAlchemy ORM entities, 14 tables                          │
└─────────────────────────────────────────────────────────┘
```

This is a strict, one-directional dependency chain — a rule that was actively maintained throughout the project, and one whose violation (in one specific case, described in Part 4) was treated as a real bug to be fixed rather than an acceptable shortcut.

## Frontend architecture

```
App.tsx (routing + global providers: Theme, Query Client, Auth)
   │
   ├── ProtectedRoute (role-gated route wrapper)
   │      └── AppLayout (responsive shell: sidebar / rail / drawer)
   │             └── Page components (~30, one per route)
   │                    ├── Reusable components (DataTable, GenericCalendar,
   │                    │    InterventionReviewViewer, ChartCard, etc.)
   │                    └── Service layer (typed API-calling functions)
   │                           └── queryHelpers.ts (generic fetch/post/put/patch
   │                                 wrappers, unwrapping the backend's
   │                                 {success, message, data} envelope)
   │                                  └── apiClient (axios instance, JWT
   │                                        interceptor, 401 handler)
   └── AuthContext (the only global client-side state besides server-cache state)
```

## Database architecture

The schema is organized around one central entity — the `interventions` table — with every other table either directly supporting it (attachments, tasks/travaux join, approval history, audit log, colleague-technicians join) or feeding into it as reference/master data (clients, client sites, contracts, projects, travaux catalog, users). See Part 8 for the full entity list and relationship diagram.

## API architecture

A conventional REST design under a single `/api` prefix, with a uniform response envelope (`{success, message, data}` for every endpoint) and a uniform pagination shape (`{items, total, page, page_size, pages}`) for every list endpoint. Authorization is enforced identically everywhere via a single reusable FastAPI dependency (`require_roles(*allowed_roles)`), never duplicated per-endpoint as bespoke logic. The reporting module deliberately consolidates eight structurally identical report types into one generically filterable endpoint rather than eight near-duplicate ones (see Part 4), which is the one clear example of an API-design optimization made during implementation rather than dictated directly by the specification.

## Authentication architecture

```
Login (username + password)
   │
   ▼
Backend verifies password (bcrypt) against stored hash
   │
   ▼
Backend issues a signed JWT { sub: user_id, role, exp }
   │
   ▼
Frontend stores the token (localStorage) and attaches it as
"Authorization: Bearer <token>" on every subsequent request
   │
   ▼
Backend verifies the signature + expiry on every protected request,
re-fetches the User row (so a deactivated account is locked out
immediately, even with a still-valid token), then checks the
caller's role against the endpoint's allowed-roles list
```

No server-side session store exists — the JWT itself, plus a database lookup for the current active/role state, is the entire authentication mechanism. This statelessness is also what made the cross-origin deployment configuration simpler than a cookie-based session would have required (see Part 4's CORS fix).

## Deployment architecture

```
Developer pushes to GitHub (main branch)
        │
        ├──────────────────────────────┬──────────────────────────────┐
        ▼                                ▼
┌─────────────────────┐        ┌─────────────────────┐
│   Railway (backend)   │        │    Vercel (frontend)  │
│  Builds from           │        │  Auto-detects Vite     │
│  backend/Dockerfile    │        │  framework, builds      │
│  Root dir: backend/    │        │  static output          │
│  Ships pre-seeded       │        │  Root dir: frontend/    │
│  demo database inside   │        │  SPA rewrite via         │
│  the image               │        │  vercel.json             │
└─────────┬───────────┘        └──────────┬───────────┘
          │                                  │
          ▼                                  ▼
   https://<backend>.up.railway.app   https://<frontend>.vercel.app
          ▲                                  │
          └──────────── CORS-allowed ────────┘
             cross-origin API calls (Bearer JWT, no cookies)
```

---

# PART 8 — Database

## Database design

The schema follows the specification's data model (Chapters 33–53) closely, implemented as 14 SQLAlchemy models mapped to 14 PostgreSQL/SQLite tables, evolved via 4 Alembic migrations (see Part 4). Every table carries `id` (primary key), `created_at`, and `updated_at` (except join tables, which carry only `id`), and enum-typed columns are implemented as true database enum types.

## Tables (all 14)

| Table | Purpose |
|---|---|
| `roles` | The 3 fixed roles (technician, chef_technicien, admin_supervisor) |
| `users` | All accounts across all 3 roles |
| `clients` | Company customers — selected from the database only, never typed manually |
| `client_sites` | A client's physical locations; cities are derived from this table, never typed manually |
| `contracts` | Maintenance agreements, tied to one client |
| `projects` | Long-term multi-intervention activities, tied to one client |
| `travaux` | The predefined technical-operation catalog — free-text task entry is never allowed |
| `interventions` | The central table — the digital Bon d'Intervention record itself |
| `intervention_tasks` | Many-to-many join: an intervention's selected travaux |
| `attachments` | Uploaded/photographed paper BI images and other files |
| `intervention_technicians` | Many-to-many join: colleague technicians on an intervention (the lead technician is never duplicated here) |
| `planning` | Scheduled/planned interventions, created by a Chef des Techniciens |
| `notifications` | System notifications, optionally linked to an intervention or a planning entry |
| `approval_history` | Every approval decision ever made, append-only |
| `audit_log` | The full audit trail of every significant intervention event, append-only |

## Key relationships

- `interventions` is the highest-fan-out table: 3 required foreign keys (technician, client, site), 2 mutually-exclusive optional type-specific foreign keys (contract, project), 1 self-referential optional foreign key (warranty reference, pointing back to an earlier intervention), and 5 downstream one-to-many collections (tasks, attachments, approval history, audit log, colleague technicians).
- Two genuine many-to-many relationships exist, each via its own explicit join table with a uniqueness constraint: `interventions` ↔ `travaux` (via `intervention_tasks`) and `interventions` ↔ `users`-as-colleague (via `intervention_technicians`).
- `planning` has two distinct foreign keys into `users` (the assigned technician, and the chef who created the entry), each mapped as its own explicit relationship to avoid ambiguity.
- `notifications` has two independent, mutually-optional foreign keys (to an intervention, and to a planning entry) rather than a single polymorphic reference — a deliberate simplicity-over-flexibility choice.

## Constraints

- Every required relationship is enforced with a `NOT NULL` foreign key; every intervention-type-specific relationship (contract/project/warranty) is nullable and validated by application logic to match the selected intervention type.
- `bi_number` on `interventions` and `username`/`email` on `users` carry unique constraints.
- Both many-to-many join tables carry a composite uniqueness constraint preventing the same pairing from being inserted twice.
- No foreign key into the audit-sensitive tables (`interventions`, `approval_history`, `audit_log`) allows cascading deletes — deletion of these rows is structurally prevented, not merely discouraged by convention; the application code never issues a `DELETE` against them.
- Soft-delete/archival is used everywhere a hard delete would otherwise be needed: `users`/`clients`/`travaux` use an `active` boolean flag; `contracts`/`projects` use a `status` field with an `archived` value; `interventions` are never removed in any form, only transitioned through their status lifecycle.

## Synthetic demo database

A deterministic (fixed-seed) synthetic-data generator produces a full, referentially consistent demo dataset: 14 users (10 technicians, 2 Chef des Techniciens, 2 Administration Supervisors, all sharing one demo password), 22 clients, roughly 44–88 client sites (2–4 per client), 28 contracts, 18 projects, 125 catalog entries in the travaux table, 650 interventions spanning roughly 8 months of simulated activity across every one of the 9 lifecycle statuses (weighted heavily toward Fully Approved, reflecting a company that has "been using the application for several months"), 220 planning records, and 320 notifications. Referential consistency is actively enforced during generation — for example, a warranty-type intervention always references a real, already-created prior intervention row (never a random or future ID), a contract-type intervention is only ever assigned a contract that genuinely belongs to the same client, and a generated notification's recipient is chosen specifically so that recipient can actually view the intervention the notification references, avoiding synthetic "broken link" notifications that would 403 if clicked.

Because the generator is fully deterministic (a fixed random seed), the same dataset is reproduced identically across every environment it has been run in — this is what allows the exact same demo dataset to back local development, the automated test suite, and the live deployed demo environment.

## Future migration to a real company database

The application's data-access layer is written entirely against SQLAlchemy's database-agnostic query API, with the one and only database-specific branch in the entire codebase being a single connection-argument difference between SQLite and PostgreSQL (handled by one conditional in the database session setup). The specification itself frames this explicitly as a design requirement: *"The application is currently developed as a web application using a synthetic database. The architecture must allow easy migration to the company's real database in the future."* A real migration would involve: pointing the `DATABASE_URL` configuration at the company's actual PostgreSQL instance (already the fully-supported, intended production target — SQLite is the secondary, demo-oriented option), running the existing Alembic migration chain against it to create the schema, and — separately, as a data-migration exercise outside this application's own scope — importing or re-keying the company's existing historical paper-BI records if a backfill of historical data is desired. One implementation detail worth flagging for that transition: a single dashboard KPI calculation (average administrative-approval time) currently uses a SQLite-specific date-difference function, with an explicit code comment already documenting the equivalent PostgreSQL syntax to switch to at that point.

---

# PART 9 — Functionalities

*Every implemented, user-facing feature, organized by module.*

## Authentication
**Purpose:** secure, role-differentiated access to the system. **Workflow:** a user submits a username and password; on success, they receive a session token and are redirected to a role-appropriate view of the dashboard. **Business logic:** passwords are never stored in plain text (bcrypt hashing); sessions expire after a configured duration; a deactivated account is locked out immediately regardless of any still-valid token it may be presenting. **User interaction:** a single centered login form; any authentication failure shows a generic "Invalid username or password" message (deliberately not revealing which of the two was wrong).

## Reference Data Management (Users, Clients, Client Sites, Contracts, Projects, Travaux)
**Purpose:** maintain the master/dropdown data every intervention and planning entry is built from — enforcing the specification's repeated rule that clients, sites, contracts, projects, and travaux are always selected from the database, never typed freely. **Workflow:** the Administration Supervisor searches, filters, creates, edits, and activates/deactivates (or archives, for contracts/projects) each entity through a consistent table-plus-modal-form pattern. **Business logic:** sites are always scoped to a specific client and cannot exist independently; contracts and projects likewise; user creation enforces a minimum password length and role assignment; none of these entities can ever be hard-deleted, only deactivated/archived. **User interaction:** paginated, searchable, filterable tables; a "Show inactive" toggle to reveal deactivated records; per-row action buttons.

## Intervention Creation and Submission
**Purpose:** the digital replacement for filling out the paper Bon d'Intervention. **Workflow:** a technician fills a nine-section form (general info, client/site, intervention type with its conditional dependent field, location, time/duration, team, travaux performed, technical report, attachments), saves it as a draft (repeatedly, if needed), attaches a photograph of the signed paper BI, and submits it — which locks the record and starts the approval pipeline. **Business logic:** the BI number is generated automatically and is never editable; net duration is always backend-computed; submission is blocked until at least one attachment exists and every required field is filled; a submitted record becomes fully locked to the technician until a supervisor decision is made. **User interaction:** a single form serving both creation and editing, with live client-side duration-preview feedback, cascading dropdown behavior (selecting a client filters the available sites), and a distinct, confirmation-gated "Submit" action separate from ordinary saving.

## My Interventions / Interventions List
**Purpose:** browse and track intervention history — a technician's own, or (for Chef des Techniciens and Administration Supervisor) every intervention in the system. **Workflow:** filter by status tab, client, date range, or free-text BI-number search; toggle between a paginated table view and a calendar view. **Business logic:** a technician only ever sees their own interventions (with an opt-in toggle to also include interventions they participated in as a colleague technician); supervisors see everything, unfiltered by ownership. **User interaction:** status tabs, a list/calendar view toggle, and click-through to the full intervention detail page.

## Intervention Details / Review
**Purpose:** a complete, read-only, fully denormalized view of a single intervention (used both for a technician reviewing their own submitted work, and for a supervisor reviewing a pending approval decision). **Workflow:** every stored field is displayed, every foreign key resolved to a human-readable name, the attached paper-BI photograph is shown zoomable/pannable, and — for supervisors reviewing an actionable item — Approve/Reject controls with a required rejection comment are presented alongside the digital record. **Business logic:** the review interface deliberately synchronizes the complete digital record against the physical document image side by side, so a reviewer never has to leave the screen to look something up. **User interaction:** a full-screen split-screen dialog for the active review flow; a permanent standalone page for after-the-fact history browsing.

## Planning / Scheduling
**Purpose:** replace verbal/phone-based technician assignment with a real scheduling system. **Workflow:** the Chef des Techniciens creates a planned intervention (client, site, technician, date, time, priority, notes), which the assigned technician immediately sees on their own calendar and is notified of. **Business logic:** an entry is only editable while still in its initial Planned state (not once work has started); cancellation is a soft action (status change, history preserved) with the technician notified either way. **User interaction:** a full calendar view plus a modal creation/edit form, with a distinct, visually differentiated "New Urgent Intervention" action.

## Urgent Intervention Dispatch
**Purpose:** give genuinely time-critical requests a fast path that bypasses normal planning. **Workflow:** an intervention (new or existing) is flagged urgent, immediately notifying the assigned technician and surfacing it at the top of the relevant dashboards; the Chef des Techniciens can further manually reorder the urgent queue by priority via drag-and-drop. **Business logic:** only entries that are both currently marked urgent and not cancelled may be included in a reorder; a reorder request is validated as an all-or-nothing operation. **User interaction:** a red-highlighted urgent indicator throughout the UI, and a dedicated drag-and-drop-reorderable list on the Chef des Techniciens' dashboard.

## Two-Level Approval Workflow
**Purpose:** digitally reproduce the company's existing dual-supervisor validation process. **Workflow:** a submitted intervention first queues for the Chef des Techniciens' technical approval; if approved, it automatically advances to the Administration Supervisor's administrative approval queue; if approved there too, it becomes permanently locked (Fully Approved); a rejection at either stage unlocks the record and returns it to the technician with the rejection reason, from where it can be corrected and resubmitted. **Business logic:** each level can only be performed by its designated role; every decision — approve or reject, at either level — is permanently recorded with the approver's identity, timestamp, and optional comment; a rejected-then-resubmitted record re-enters at the technical approval stage regardless of how far it had previously progressed. **User interaction:** a dedicated pending-approval queue page per level, opening the same full-screen split-screen review interface described above.

## Dashboards
**Purpose:** give each role real-time, role-appropriate operational visibility that the paper process could never provide. **Workflow:** on login, each role sees a dashboard populated with relevant KPI tiles, lists, and charts; a shared Day/Week/Month period selector drives every chart on a given dashboard simultaneously. **Business logic:** every number shown is computed server-side (never a raw data dump the frontend has to aggregate itself); the technician dashboard shows only their own data, the Chef des Techniciens dashboard shows organization-wide operational data plus the urgent queue, and the Administration Supervisor dashboard shows organization-wide approval-rate and volume KPIs. **User interaction:** stat tiles, bar/line charts, and actionable lists (e.g., clicking a "recently completed" row navigates directly to that intervention).

## Technician Performance View
**Purpose:** let supervisors drill into any individual technician's own performance metrics and history, in the same visual language as the main dashboards. **Workflow:** a Chef des Techniciens or Administration Supervisor toggles into a "technician performance" mode showing a card grid of every technician (points, completed count, current workload, next scheduled job), and can click through to a single technician's own detail page. **User interaction:** a card grid plus a detailed per-technician profile page.

## Notifications
**Purpose:** the centralized alerting system replacing informal phone-based communication. **Workflow:** every relevant system event (new assignment, urgent assignment, planning change, submission, approval, rejection) generates a notification for the relevant recipient(s); the notification list shows unread items distinctly and clicking one both marks it read and deep-links directly to the relevant intervention or planning entry. **User interaction:** a paginated notification list, a "mark all read" action, and content-aware click-through routing.

## Reports and Export
**Purpose:** answer the operational questions the paper process could never answer — interventions by period, by technician, by client, by project, by contract, plus dedicated approval-history and planning-history reports, plus a historical period-vs-period comparison view. **Workflow:** a supervisor selects a report type and filters, views the filtered result set plus a summary of totals, and optionally exports the current report as PDF or Excel. **Business logic:** filters are combinable and default to a sensible trailing window (e.g., "weekly" defaults to the last 7 days) when no explicit dates are given. **User interaction:** a tabbed report-selection interface with consistent filter controls and one-click export buttons.

## Profile Pages
**Purpose:** let every user view their own account information and (for technicians) their own performance summary. **Workflow:** the logged-in user's own profile shows role-appropriate content — a technician sees their full performance-stat grid and recent activity; a Chef des Techniciens or Administration Supervisor sees a lighter identity-plus-recent-decisions view. **User interaction:** a shared header component (avatar, name, role, status) reused identically across the self-service profile and the supervisor-facing technician-detail view, so both present a consistent visual identity.

---

# PART 10 — Business Rules

## Point calculation
Points are awarded automatically at the moment of submission, based purely on the local time of day the technician submits (never anything the technician can influence directly): 17:00–19:00 → +5 points, 19:00–22:00 → +2 points, 22:00–24:00 → +1 point, any other hour → a flat -1 penalty. The evaluation is performed in the company's own local timezone (Africa/Casablanca), converted from the UTC timestamp stored in the database, specifically so a technician's own local end-of-day submission time is what determines their points, regardless of what timezone the server itself happens to run in.

## Duration calculation
Net Duration = End Time − Start Time − Lunch Break. The system rejects any lunch-break value that would exceed the raw (gross) elapsed time between start and end. Duration is always computed and stored by the backend; the frontend may show a live estimate while a form is being filled in, but that estimate is explicitly never treated as authoritative.

## Lunch break
A technician may indicate "No Lunch Break" (a break of 0 minutes) or choose a break duration from a fixed set of presets (30, 60, 90, or 120 minutes); the selected break is subtracted from the gross working window to produce net duration.

## Status transitions (the 9-state lifecycle)
Draft → (submission) → Pending Technical Approval → (technical approval) → Pending Administrative Approval → (administrative approval) → Fully Approved (permanently locked, terminal). A rejection at either approval stage moves the record to Rejected, from which editing resets it back to Draft, and resubmission re-enters at Pending Technical Approval — regardless of how far the record had previously progressed before being rejected. Fully Approved is the only truly terminal state; every illegal transition attempt is rejected outright by the backend (HTTP 409) rather than silently ignored.

## Two-step approval
Every intervention must pass two independent approval gates before being considered finalized: a **technical** approval performed exclusively by the Chef des Techniciens, followed by an **administrative** approval performed exclusively by the Administration Supervisor. Neither role can perform the other's approval step. Every decision at either level — approved or rejected — permanently records the approving user's identity, the exact timestamp, and an optional comment, in an append-only history that is never modified or deleted after the fact.

## Scheduling
Planned interventions are created exclusively by the Chef des Techniciens (client, site, assigned technician, date, start time, priority, and notes), and the assigned technician is notified immediately and sees the entry on their own calendar right away. An entry can only be edited while it is still in its initial Planned state; once the corresponding work is underway, it is no longer editable through the planning interface.

## Priority / urgent interventions
Interventions carry one of three priority levels (Normal, High, Urgent). Marking an intervention Urgent triggers an immediate, distinctly-worded notification to the assigned technician and surfaces the item at the top of the relevant dashboards with a red visual indicator, which persists until the work is completed. The Chef des Techniciens can additionally impose a manual priority ordering on the set of currently active urgent interventions via drag-and-drop, which is persisted and used to order the urgent queue on their dashboard (falling back to the planned date for any entry that has never been manually reordered).

## Notifications
Technicians are notified on: new assignment, urgent assignment, an intervention being rejected, and an intervention becoming fully approved. Every active Chef des Techniciens is notified whenever any technician submits an intervention (the specification does not designate a single supervisor to route submissions to, so all of them are notified rather than risking a submission going unseen). Every active Administration Supervisor is notified whenever a technical approval is granted (since that is precisely the event that makes an item newly actionable for them).

## Permissions
There are exactly three roles, with no separate "administrator" account — the Administration Supervisor performs all top-level administrative duties directly. A technician may only ever view and edit their own interventions (and only while still Draft or Rejected); they cannot approve anything, manage any reference data, or view organization-wide statistics. The Chef des Techniciens can see and manage all interventions and all planning, perform technical approval, and manage technician assignments, but cannot perform the final administrative approval and cannot manage users, clients, or reference-data catalogs. The Administration Supervisor can do everything except technical approval, and additionally manages every reference-data catalog, users (including activation, deactivation, and password resets), and has full reporting/dashboard access. Every one of these boundaries is enforced identically by the backend on every request — the frontend's role-based menu hiding is a usability convenience only, never the actual security boundary.

## Validation rules
- Clients, client sites (and therefore cities), contracts, projects, and travaux (technical operations) are never entered as free text anywhere in the application — every one of these is always selected from an existing database record.
- Cities specifically are never a standalone field at all; they are always derived by looking at which sites belong to the currently selected client.
- A technician's own name is never manually entered on an intervention — it is always taken directly from their authenticated session.
- The BI number is generated automatically and sequentially and can never be edited by a user.
- Every intervention must have at least one attached image of the signed paper BI before it can be submitted — submission is blocked entirely without one.
- A warranty-type intervention must reference an already-existing, real prior intervention record; the system does not accept a reference to a nonexistent BI number.
- No OCR is performed on any uploaded attachment — attachments are stored purely as documentary evidence, and every field on the digital form is always entered manually by the technician.
- Interventions are never deleted under any circumstances — only their status changes, guaranteeing permanent traceability.
- Every significant action on an intervention (creation, draft save, modification, submission, each approval decision, rejection, resubmission) is timestamped and permanently recorded in an audit trail.

---

# PART 11 — Difficulties Encountered

*Only challenges that are directly supported by evidence in the repository — code, comments, commit history, or documented investigation — are included below.*

## 1. A real ambiguity between the specification's literal state list and its own workflow diagrams

**Problem:** the specification's written lifecycle description lists 9 distinct intervention states, but its own approval-workflow diagrams show two of those nine states (Submitted, Technical Approved) as always advancing automatically, within the very same user action, to the next state — meaning those two states are never actually meant to be something a user or a queue view would ever observe at rest.

**Cause:** a specification that describes a state machine partly through a state list and partly through separate workflow diagrams can produce exactly this kind of internal tension if the two aren't cross-checked against each other before implementation begins.

**Solution adopted:** the transition logic was implemented to jump directly to the next queue-visible state in a single atomic action (e.g., submitting an intervention writes directly to "Pending Technical Approval," never pausing at a literal "Submitted" state), while still recording that the intermediate step genuinely happened via a dedicated timestamp column (`submission_date`, `technical_approval_date`) — so no information described in the specification is lost, but the system's actual observable behavior matches its own workflow diagrams rather than a literal reading of its state list.

**Result:** the implemented state machine behaves consistently with how the approval workflow is actually described end to end, and this exact resolution is what the automated test suite verifies (a full technical-then-administrative approval walkthrough test exists specifically to lock this behavior in).

## 2. A cross-origin (CORS) configuration incompatibility discovered only when actually separating the two deployments

**Problem:** after configuring the backend to accept requests from any frontend origin (a wildcard CORS setting, needed since the exact frontend URL isn't known until after that separate service is deployed), cross-origin requests from a real deployed frontend were still being silently blocked by the browser.

**Cause:** the backend's CORS configuration also allowed credentialed cross-origin requests, and browsers enforce that a wildcard allowed-origin and credentialed requests can never be combined — this is a hard rule of the CORS specification, not a bug in either side's code individually, but the two settings are only actually incompatible together.

**Solution adopted:** confirmed first that the application's authentication genuinely never relies on cookies or credentialed requests anywhere in the frontend (a grep across the entire frontend codebase for any credential-sending configuration came back empty), then removed the credentialed-request allowance on the backend, which made the wildcard-origin configuration valid again.

**Result:** verified with a real cross-origin preflight request and a real cross-origin POST request (not just a same-origin sanity check), confirming the correct response headers came back from a genuinely different origin — proving the fix worked as an actual browser would experience it, not just in theory.

## 3. Missing safety net for a genuinely empty database on first deployment

**Problem:** the application's normal startup path had no step that created the database schema or seeded any initial data — it had only ever been tested and run against a database file that already had everything pre-built into it, so this gap went unnoticed until it was specifically investigated.

**Cause:** every environment the application had been run in up to that point — local development, the automated test suite, and the initial production deployment — happened to always start from an already-initialized database, so the missing initialization step never had a chance to actually fail and reveal itself.

**Solution adopted:** added a startup routine that creates any missing database tables and seeds demo data if the database is empty, confirming first that both of those operations are safe no-ops against a database that's already fully set up (so this change carries zero risk to any environment that already worked correctly).

**Result:** directly verified by deliberately starting the application against a brand-new, genuinely empty database file — confirming it correctly built the full schema and seeded all expected demo accounts on the first boot — and then starting it a second time against that same now-populated file, confirming no duplicate data was created on the second boot.

## 4. Diagnosing a live production login failure required direct evidence, not speculation

**Problem:** a login failure was reported against the live deployed application, initially framed as a possible systemic issue (a wrong database being used, missing seeded users, broken password hashing, or a broken login endpoint).

**Cause investigation:** rather than assuming any of those possibilities, every one of the fourteen demo accounts was tested directly against the live production deployment. Thirteen logged in successfully; only one account failed. Direct inspection of that one account's stored data showed its "last updated" timestamp was meaningfully later than its "created" timestamp — every other account's two timestamps were identical — which, cross-referenced against the application's own password-reset code path, proved that specific account's password had been legitimately changed at some earlier point (most likely during prior manual testing), and that changed state had simply been carried forward into the version of the database that was deployed.

**Solution adopted:** the one affected account's password was restored to the documented default, using the exact same hashing function every other account's password already went through, and — since this investigation also surfaced the separate, more consequential gap described in Challenge 3 above (no safety net for a truly empty database) — that gap was fixed and verified in the same pass.

**Result:** confirmed live, against the actual production deployment, that all fourteen demo accounts log in correctly after the fix — not merely inferred as fixed from local testing.

## 5. Choosing between a maintained wrapper library and a lower-level dependency after finding a real compatibility break

**Problem:** the most commonly used higher-level password-hashing wrapper library was found to have a compatibility break in its own internal self-test logic when paired with a newer release of the underlying hashing library it wraps.

**Cause:** the wrapper library in question had not kept pace with a breaking internal-API change in its dependency.

**Solution adopted:** the lower-level hashing library was used directly instead of through the wrapper, implemented as two small, explicit functions (hash and verify) rather than adopting the wrapper's broader (but, for this project, unnecessary) configurability.

**Result:** password hashing works correctly and predictably, with the reasoning for bypassing the more commonly recommended wrapper documented directly in the code so the decision doesn't appear to be an oversight to anyone reading it later.

---

# PART 12 — Results

## What was achieved

A fully functional, end-to-end digital replacement for the company's paper-based intervention workflow was implemented and deployed: complete role-based authentication and authorization across three distinct roles; full CRUD management of every reference-data type the workflow depends on; the complete intervention creation-through-submission workflow with all nine specified form sections and their conditional logic; a real planning/scheduling module including an urgent-intervention fast path with manual queue reordering; the full two-level approval workflow with permanent, append-only decision history; three genuinely distinct role-specific dashboards plus a shared, period-aware charting subsystem and a dedicated technician-performance drill-down view; a centralized notification system covering every specified trigger event; a ten-report-type reporting module with PDF and Excel export; and a fully automated backend test suite (122 tests) exercising every one of the above.

## Functional state of the application

The application is deployed as a genuinely split, two-service production architecture: a backend API service and a fully separate, independently hosted static frontend, communicating over a correctly configured cross-origin connection with authenticated, role-checked requests. It has been directly, live-verified against its actual production deployment — not only against local development — for both a general health check and, specifically, for real user login across every one of its fourteen demo accounts. The system currently runs against a deterministic, fully realistic synthetic dataset (14 users across all three roles, hundreds of interventions spanning every lifecycle status, tied together with correct referential integrity) rather than a real company database, exactly as intended for this stage of the project.

## Remaining improvements

A small number of gaps remain, identified directly through the development and diagnostic work itself rather than as a generic disclaimer:
- Scheduling/planning currently has no automated double-booking or time-conflict detection — a Chef des Techniciens could technically schedule the same technician into two overlapping time windows without the system flagging it.
- The current production deployment's SQLite database does not persist new writes (new interventions, new users, uploaded attachments) across a redeployment unless a persistent storage volume is separately attached — this is a known, explicitly documented limitation of the current zero-configuration demo deployment, with the fix (either attaching persistent storage, or switching to the already-fully-supported PostgreSQL option) already identified and documented but not yet applied.
- One specific dashboard KPI calculation (average administrative-approval time) currently relies on a SQLite-specific date-arithmetic function; the equivalent PostgreSQL syntax has already been identified and documented in the code for when a production PostgreSQL migration happens, but has not yet been switched over since it isn't needed on the current deployment target.

## Production readiness

The application is production-ready for the specific scope it was built for — a company-internal operational tool for a defined, small set of internal users across three known roles — with a functioning, tested deployment pipeline already in place. It is **not yet** connected to a real company database (still running against the synthetic dataset, exactly as scoped for this phase), and the persistence limitation described above should be resolved (via a storage volume or a migration to PostgreSQL, both already-supported paths) before any deployment is expected to retain real user-entered data across restarts. Both of these are scoping decisions consistent with the project's explicitly stated first-version boundaries, not unaddressed defects.

---

# PART 13 — Skills Acquired

**Software architecture:** designing and consistently maintaining a strict layered backend architecture (API / service / repository / model) across an entire non-trivial application, including recognizing and correcting a real violation of that architecture found late in the project rather than tolerating it as a shortcut.

**REST API design:** designing a complete, role-authorized REST API surface from a written specification, including a genuine API-design optimization (consolidating eight structurally similar report endpoints into one generically filterable endpoint) rather than a literal one-to-one translation of every specified capability into its own endpoint.

**Relational database design:** designing a 14-table normalized schema directly from written requirements, including correctly modeling two distinct many-to-many relationships, a self-referential foreign key, and a schema that evolved safely and only additively across four real migrations as new features were added.

**Authentication and authorization systems:** implementing a complete, stateless, JWT-based authentication system from first principles (password hashing, token issuance and verification, and a reusable, composable role-based-access-control mechanism used identically across every protected endpoint in the application).

**State-machine design and enforcement:** designing and implementing a formally verified, single-source-of-truth status-transition system for a real multi-stage business workflow, including resolving a genuine ambiguity between a specification's literal wording and its own diagrams.

**Full-stack development:** implementing a complete application across both a Python/FastAPI backend and a React/TypeScript frontend, including the full data-contract layer between them (typed request/response schemas on both sides, kept in sync throughout development).

**UI/UX design and component reuse:** building roughly 30 distinct pages on top of a deliberately small, genuinely reusable component library rather than one-off implementations, including a fully responsive application shell adapting correctly across desktop, tablet, and mobile breakpoints.

**Business rule translation:** translating a large volume of prose business rules (a specification with over 150 chapters) into precise, testable, enforced application logic — including calculation formulas with real-world edge cases (timezone-correct point calculation, a bounded lunch-break validation).

**DevOps and deployment:** configuring and debugging a genuinely split-architecture production deployment across two different hosting platforms, including diagnosing and resolving two distinct real deployment-blocking bugs (a configuration-crash bug and a cross-origin/authentication interaction bug) through direct evidence rather than speculation.

**Live production debugging:** diagnosing a real, live-reported production issue methodically — testing every account systematically against the actual deployed system rather than guessing, isolating the true root cause through direct evidence (a timestamp inconsistency), and verifying the eventual fix against the live production system itself rather than assuming a local fix would transfer.

**Automated testing discipline:** building and consistently running a full backend test suite throughout development, using a genuine fresh-database-per-test strategy rather than mocks, and treating "all tests pass" as a hard precondition before considering any backend change complete.

**Git and version control workflow:** organizing incremental development work into clearly scoped, well-documented commits that explain the reasoning behind each change, not only the mechanical diff.

**Requirements analysis:** working from a large, pre-written formal specification document as the definitive source of truth, extracting a coherent data model, API surface, and business-rule set from it before writing implementation code, and correctly identifying and resolving the specification's own internal ambiguities where they existed.

**Debugging and root-cause investigation:** consistently distinguishing between a symptom and its actual root cause across multiple real incidents in this project (a login failure that looked systemic but was isolated to one account; a CORS failure that looked like a backend misconfiguration but was actually an incompatible *combination* of two individually valid settings) — in every case verifying the true cause with direct evidence before implementing or reporting a fix.

---

# PART 14 — Future Improvements

*Realistic, scoped future developments — matching the specification's own explicitly stated out-of-first-version-scope list, plus improvements identified directly through this project's own implementation and diagnostic work.*

- **PostgreSQL production migration** — moving the live deployment from its current SQLite-based demo configuration to the already-fully-supported PostgreSQL target, which resolves both the current data-persistence limitation and the one remaining SQLite-specific dashboard calculation.
- **Persistent storage for the current SQLite deployment** (as an interim step before a full PostgreSQL migration) — attaching a persistent storage volume so uploaded attachments and newly created records survive a redeployment.
- **Scheduling conflict detection** — adding automated double-booking/time-overlap detection to the planning module, which the current implementation does not perform.
- **OCR** — automatically extracting information from the photographed paper BI, rather than requiring every field to be entered manually on the digital form, as explicitly named in the specification's own long-term roadmap.
- **AI-assisted validation** — using extracted or entered data to flag likely data-entry errors or inconsistencies before submission, as referenced in the specification's stated long-term direction (Artificial Intelligence, predictive analytics).
- **Mobile application** — a dedicated native or cross-platform mobile app for technicians in the field, explicitly named in the specification as out of first-version scope.
- **Automatic planning optimization** — algorithmic assignment/scheduling suggestions rather than fully manual dispatch by the Chef des Techniciens, as named in the specification's long-term roadmap.
- **Email notifications** — extending the current in-app notification system with email delivery for users who are not actively using the application at the moment a relevant event occurs.
- **Cloud file storage for attachments** — moving uploaded attachment storage off the application server's local filesystem and onto dedicated object storage, which would also naturally resolve part of the current deployment's persistence limitation for that specific data type.
- **Advanced analytics** — deeper historical trend analysis and predictive workload/performance analytics beyond the current dashboard KPIs and period-vs-period comparison report.
- **Extended audit logging** — while a complete audit trail already exists for every intervention-level event, this could be extended to cover reference-data management actions (e.g., who changed a client's details, or archived a contract) with the same level of permanence and detail.
- **Offline mode** — allowing a technician to complete an intervention form in a location with no connectivity and have it sync automatically once connectivity returns, directly relevant given that a meaningful portion of interventions happen at client premises rather than in the company's own connected office environment.
- **ERP integration** — connecting BIMS to the company's broader enterprise resource-planning system (billing, inventory, client-relationship data) rather than operating as a standalone system, which is the natural next step once the application is validated against the company's real production data.
- **Multi-company support** — extending the current single-company data model to support multiple independent companies/tenants on one shared deployment, explicitly named in the specification's long-term roadmap.
