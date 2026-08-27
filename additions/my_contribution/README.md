# My Contribution — BIMS (Bon d'Intervention Management System)

This folder contains **copies** of the files that primarily implement my assigned
responsibilities on the team:

- Business Logic (Logique Métier)
- Point Calculation
- Duration Calculation
- Lunch Break Calculation
- Two-Level Validation Workflow (technical + administrative approval)
- Warranty Intervention Logic
- Business Rules
- Permissions
- Notification Logic
- Planning Logic / Intervention Calendar / Planning Module
- Notifications
- KPIs / Statistics / Dashboards
- Reports / Export (PDF & Excel)

**These are copies, not the working source.** The original files at their real paths
under `backend/` and `frontend/` are untouched and are what the running application
actually uses. Nothing here has had its imports changed — every file is byte-identical
to its source, so import paths still read as if the file were at its original location
(e.g. `from app.repositories import ...`). That's expected: this folder exists purely
so you have one clean place to show your work, not a second working copy of the app.

**62 files total** — 28 backend (Python), 34 frontend (TypeScript/TSX).

---

## 1. Why each file belongs to my work

### Backend — Services (the business-logic core)

| File | Responsibility it implements |
|---|---|
| `services/business_logic_service.py` | **Point Calculation** and **Duration Calculation** and **Lunch Break Calculation** — the three smallest, most foundational rules in the whole system, and the ones most literally "Business Logic." `calculate_net_duration_minutes()` implements Net = (End − Start) − Lunch, with a guard rejecting a lunch break longer than the raw work window. `calculate_points()` implements the four-tier submission-time scoring rule (17:00–19:00 → +5, 19:00–22:00 → +2, 22:00–24:00 → +1, else −1), converting the stored UTC timestamp to the company's own local time (`Africa/Casablanca`) before checking which window applies — this timezone conversion is deliberate and is the one detail worth explaining if asked "why not just check `.hour` directly." |
| `services/status_transition_service.py` | **Business Rules** and the backbone of the **Two-Level Validation Workflow** — a single explicit transition table (`ALLOWED_TRANSITIONS`) is the *only* place in the entire application allowed to say whether a status change is legal. Every status-changing action anywhere in the app is required to call `ensure_transition_allowed()` rather than setting `.status` directly, so this file is genuinely the single source of truth for the intervention lifecycle, not just one of several places that check it. |
| `services/approval_service.py` | **Two-Level Validation Workflow**, directly. `decide_technical_approval()` and `decide_administrative_approval()` are the two functions that actually move an intervention through Chef-approval-then-Admin-approval, write the permanent approval-history record, write the audit-log entry, and fire the correct notification depending on approve vs. reject. |
| `services/planning_service.py` | **Planning Logic**, **Intervention Calendar**, **Planning Module** — full CRUD for scheduled interventions, the urgent-intervention flag (`mark_urgent()`), and the drag-and-drop urgent-queue reordering (`reorder_urgent_queue()`), plus the Rule-2 validation that a chosen site must actually belong to the chosen client. |
| `services/notification_service.py` | **Notification Logic** and **Notifications**, in full — every `notify_*` function in the application lives here: new assignment, urgent assignment, planning modified, planning cancelled, submission received, technical approval granted, rejection (either level), full approval. |
| `services/dashboard_service.py` | **Dashboards**, **KPIs**, **Statistics** — the three role dashboards (Technician / Chef des Techniciens / Administration Supervisor) and every chart-series aggregation behind them, including the Day/Week/Month period-mode logic shared across all three. |
| `services/report_service.py` | **Reports** — the ten report types (Daily/Weekly/Monthly/Yearly/Technician/Client/Project/Contract collapsed into one generically-filterable query, plus a separate Approval report, Planning report, and period-vs-period Comparison report). |
| `services/export_service.py` | **Reports / Export (PDF & Excel)** — `render_pdf()` (reportlab) and `render_excel()` (openpyxl), the two functions that turn a report's row data into a downloadable file. |
| `services/technician_performance_service.py` | **KPIs / Statistics**, at the individual-technician level — completed/pending/rejected/warranty counts, total points, average duration, completed-vs-planned ratio, and the two activity charts shown on a technician's own profile and the drill-down profile a supervisor sees. |

### Backend — API routers (thin HTTP wrappers over the services above)

`api/approvals.py`, `api/planning.py`, `api/notifications.py`, `api/dashboard.py`,
`api/reports.py`, `api/technician_performance.py` — each of these is a thin FastAPI
router that does role-checking (via `require_roles(...)`) and then calls exactly one
function from the matching service file above. They're included because they're the
entry point a reviewer would actually hit first when tracing "where does this feature
start" — but the real logic is always one call away, in the service file.

### Backend — Models, schemas, repositories (the data layer under my services)

- `models/approval_history.py`, `models/planning.py`, `models/notification.py` — the
  three database tables that exist specifically to support the workflows above:
  the permanent approval-decision record, the scheduled-intervention record, and the
  notification record.
- `schemas/approval.py`, `schemas/planning.py`, `schemas/notification.py`,
  `schemas/dashboard.py`, `schemas/report.py`, `schemas/technician_performance.py` —
  the Pydantic request/response shapes for every endpoint above.
- `repositories/approval_history_repository.py`, `repositories/planning_repository.py`,
  `repositories/notification_repository.py` — the query layer each service calls into
  (e.g. `planning_repository.reorder_urgent_queue()` is where the urgent-queue's
  persisted ordering actually gets written).

### Backend — Permissions

- `middleware/auth.py` — this **is** the Permissions implementation. `require_roles(*allowed_roles)`
  is a single reusable dependency factory that every protected endpoint in the *entire*
  application (not just mine) is built on: it resolves the current user from their JWT,
  confirms they're still active, and 403s if their role isn't in the allowed list. I'm
  including the full file because Permissions was an explicit named responsibility and
  this file is unambiguously where that responsibility lives — even though, once built,
  every other team member's endpoints use it too.

### Frontend — Pages

`pages/PlanningPage.tsx`, `pages/TechnicalApprovalsPage.tsx`,
`pages/AdministrativeApprovalsPage.tsx`, `pages/NotificationsPage.tsx`,
`pages/ReportsPage.tsx`, `pages/DashboardPage.tsx`, and all four files under
`pages/dashboards/` — one page (or dashboard-content component) per feature area
above, on the UI side: the planning calendar and creation/edit modal, the two approval
queues, the notification inbox, the four-tab reports screen, and the three role
dashboards plus the technician-performance card grid.

### Frontend — Components

`components/PlanningCalendar.tsx`, `UrgentQueueList.tsx`, `PeriodModeSelector.tsx`,
`ChartCard.tsx`, `SimpleBarChart.tsx`, `SimpleLineChart.tsx`, `TechnicianCard.tsx`,
`StatTile.tsx` — reusable building blocks used exclusively (or almost exclusively) by
the pages above: the planning-specific calendar color-coding, the drag-and-drop urgent
queue, the shared Day/Week/Month selector every dashboard chart is driven by, the two
chart primitives, and the stat-tile/technician-card building blocks every dashboard is
assembled from.

### Frontend — Services, types, utils

- `services/approvalService.ts`, `planningService.ts`, `notificationService.ts`,
  `dashboardService.ts`, `reportService.ts`, `technicianPerformanceService.ts` — the
  typed functions that call the matching backend endpoints above.
- `types/planning.ts`, `dashboard.ts`, `notification.ts`, `report.ts`,
  `technicianPerformance.ts` — the TypeScript shapes matching the backend schemas above.
- `utils/notificationRouting.ts` — the click-through routing rule set (which page a
  notification navigates to depending on its content and the current user's role).
- `utils/planningColors.ts` — the calendar color-coding rules for planning entries,
  including the urgent-priority override.

### Frontend — Permissions (route guard)

- `routes/ProtectedRoute.tsx` — the frontend-side counterpart to `middleware/auth.py`:
  redirects to `/login` if unauthenticated, or to `/403` if the current user's role
  isn't in the route's allowed-roles list. Included for the same reason as
  `middleware/auth.py` above.

---

## 2. Two files included as shared infrastructure, not exclusive ownership

These two are genuinely more mine than not, but I want to be upfront that they're not
100% exclusively my code — be ready to say so if asked at the defense, rather than
claiming the whole file outright.

- **`components/GenericCalendar.tsx`** — this is the underlying FullCalendar wrapper
  that `PlanningCalendar.tsx` is built on, and it's also used directly (unwrapped) by
  both approval pages for their calendar view. All three of those usages are mine. It's
  also reused a fourth time, unmodified, by `MyInterventionsPage.tsx` (a plain
  intervention-list page that isn't part of my scope) — because the component itself
  has zero planning/approval-specific logic in it (it just takes a generic
  `{id, date, title, color, onClick}` event list), it's genuinely shared infrastructure
  rather than something I could claim exclusively. What to say: *"I built the calendar
  views for Planning and both Approval queues on top of a shared, reusable calendar
  engine — that engine itself is also used elsewhere in the app for the same reason any
  well-designed reusable component would be."*

- **`components/InterventionReviewViewer.tsx`** — this is the full-screen split-screen
  review dialog both approval pages open when a Chef or Admin clicks "Review." The
  Approve/Reject action panel, the rejection-reason requirement, and the
  `level="technical"|"administrative"` behavior are all Two-Level-Validation-Workflow
  logic and are mine. However, the bulk of the file's ~500 lines — everything that
  actually *displays* the intervention's fields (client, site, dates, travaux,
  attachments, etc.) — is general intervention-display logic, and the same component is
  reused, unmodified, by `InterventionDetailsPage.tsx` (outside my scope) purely as a
  read-only attachment zoom-viewer, with no Approve/Reject affordances shown there at
  all. What to say: *"I built the review-and-decide workflow on top of the existing
  intervention-detail display component, rather than duplicating that display logic in
  a second component."*

---

## 3. Files that are NOT copied here, even though a real piece of my logic lives inside them

Four files contain a genuine fragment of my work but are **primarily** owned by other
modules — copying the whole file here would overstate what's mine. Instead, here's
exactly where to find each fragment if you need to show it live during the defense.

| File (at its real path, not copied) | What of mine is inside it | Exact location |
|---|---|---|
| `backend/app/services/intervention_service.py` | **Warranty Intervention Logic** — the check that a warranty-type intervention must reference an already-existing prior BI number, or the request is rejected with a 404. | Function `_validate_references()`, lines 41–77. The warranty-specific branch itself is lines 65–71:<br>`if payload.intervention_type == InterventionType.WARRANTY: referenced = intervention_repository.find_by_bi_number(...); if referenced is None: raise 404 "Referenced BI number does not exist."` |
| `backend/app/api/interventions.py` | The create/update/submit endpoints that carry the warranty check above through to the HTTP layer. | No dedicated warranty endpoint exists — it's one branch inside the shared create/update payload, since Contract/Project/Warranty are three variants of the same generic intervention-type field. |
| `backend/app/models/audit_log.py` + `backend/app/repositories/audit_log_repository.py` | `has_ever_been_rejected()` is used by the submit flow to distinguish a first submission from a resubmission (a Two-Level-Validation-Workflow nuance), and the audit repository's `create()` is called by `approval_service.py` for every `TECHNICAL_APPROVED`/`ADMINISTRATIVE_APPROVED`/`REJECTED` event. | The model/repository is genuinely general-purpose (it also logs `CREATED`, `DRAFT_SAVED`, `MODIFIED` — plain CRUD events that have nothing to do with approvals), so it's fair to describe as *used by* my workflow, not *owned by* it. |
| `frontend/src/layouts/AppLayout.tsx` | **Permissions** — the per-role navigation menu, i.e. which sidebar items each of the three roles actually sees. | The `NAV_ITEMS_BY_ROLE` map, lines 51–78, and its one line of usage: `const navItems = user ? NAV_ITEMS_BY_ROLE[user.role] : [];` (line 95). The other ~180 lines of this file are responsive-layout mechanics (desktop sidebar / tablet icon rail / mobile drawer) that belong to whoever built the app shell, not to Permissions. |

---

## 4. How the files interact together

```
                         ┌─────────────────────────────────────────┐
                         │              FRONTEND (React)              │
                         │                                             │
  Pages ──────────────►  │  PlanningPage / TechnicalApprovalsPage /   │
                         │  AdministrativeApprovalsPage /             │
                         │  NotificationsPage / ReportsPage /          │
                         │  DashboardPage + dashboards/*               │
                         │        │                                    │
                         │        ▼ calls                              │
                         │  services/*.ts (typed API functions)        │
                         │        │                                    │
                         └────────┼────────────────────────────────────┘
                                  │  HTTPS + Bearer JWT
                                  ▼
                         ┌─────────────────────────────────────────┐
                         │              BACKEND (FastAPI)              │
                         │                                             │
                         │  api/approvals.py, planning.py,             │
                         │  notifications.py, dashboard.py,             │
                         │  reports.py, technician_performance.py       │
                         │        │ role-checked via                    │
                         │        │ middleware/auth.py:require_roles()  │
                         │        ▼                                     │
                         │  services/approval_service.py                │
                         │  services/planning_service.py                │
                         │  services/notification_service.py            │
                         │  services/dashboard_service.py                │
                         │  services/report_service.py                   │
                         │  services/technician_performance_service.py   │
                         │        │                                      │
                         │        ├──► services/business_logic_service.py │
                         │        │    (points, duration, lunch break —   │
                         │        │     called by approval/planning flows)│
                         │        ├──► services/status_transition_service.py│
                         │        │    (validates every status change)     │
                         │        ├──► services/export_service.py           │
                         │        │    (PDF/Excel rendering, called only     │
                         │        │     by report_service)                   │
                         │        ▼                                          │
                         │  repositories/approval_history_repository.py       │
                         │  repositories/planning_repository.py                │
                         │  repositories/notification_repository.py            │
                         │        │                                             │
                         │        ▼                                             │
                         │  models/approval_history.py, planning.py,             │
                         │  notification.py                                      │
                         └─────────────────────────────────────────┘
```

**Key interaction to explain clearly:** `business_logic_service.py` and
`status_transition_service.py` are the two files everything else in this folder
ultimately depends on — `approval_service.py` calls `status_transition_service` before
every approve/reject to make sure the transition is legal, and `intervention_service.py`
(outside my folder, but the caller) calls `business_logic_service.calculate_points()` at
submission time, before the intervention ever reaches my approval workflow. So the
correct way to describe the relationship is: *"business_logic_service and
status_transition_service are small, pure, foundational services — everything else I
built (approvals, planning, dashboards) either calls into them directly, or depends on
data they've already validated/computed by the time it runs."*

---

## 5. Which files are the most important

If asked to name the two or three files that matter most:

1. **`business_logic_service.py`** — the smallest file in the folder, and the one with
   the most direct, quotable business value: two functions, both implementing a rule
   straight from the specification (Ch.27 duration, Ch.28 points), including the one
   genuinely non-obvious detail (the UTC→local-timezone conversion for point
   calculation) that's worth being ready to explain if asked "why not just use the raw
   timestamp?"
2. **`status_transition_service.py`** — the single source of truth for the entire
   intervention lifecycle. Worth emphasizing that this isn't just "a" place that checks
   status transitions — every status-changing action in the whole application,
   including code outside this folder, is required to go through this file's
   `ensure_transition_allowed()` function rather than setting `.status` directly.
3. **`approval_service.py`** — the two-level validation workflow itself, the feature
   most directly matching the specification's own two-supervisor paper process. A good
   file to walk through end-to-end at the defense: `_get_for_decision()` loads and
   status-checks the intervention, `ensure_transition_allowed()` validates the move,
   the intervention is updated, an `approval_history` row is written permanently, an
   `audit_log` row is written, and exactly one notification fires depending on the
   outcome.
4. **`InterventionReviewViewer.tsx`** — the most visually demonstrable piece: the
   full-screen split-screen review interface a Chef or Admin actually uses to approve
   or reject an intervention side-by-side with the attached photographed paper BI. Good
   for a live demo, with the caveat from Section 2 above about what part is genuinely
   mine.

---

## 6. Execution flow of my part of the application (end to end)

This traces one complete, realistic path through the system, in the order things
actually happen, naming the exact file responsible at each step.

1. **A Chef des Techniciens schedules an intervention.**
   `PlanningPage.tsx` → `planningService.ts:createPlanning()` → backend
   `api/planning.py` (role-checked: `chef_technicien` only, via `middleware/auth.py`) →
   `services/planning_service.py:create_planning()` → validates the client/site
   relationship → `repositories/planning_repository.py:create()` → writes to
   `models/planning.py` → `services/notification_service.py:notify_new_assignment()`
   (or `notify_urgent_assignment()` if flagged urgent) fires immediately.

2. **The technician submits their completed intervention** (outside my folder —
   `intervention_service.py`'s `submit_intervention()` — but it calls two of my
   functions at this exact moment): `business_logic_service.calculate_points()` computes
   the point award from the submission timestamp, and
   `status_transition_service.ensure_transition_allowed()` validates the move into
   `pending_technical_approval`. `notification_service.notify_chefs_of_submission()`
   fires to every active Chef.

3. **The Chef reviews and technically approves (or rejects).**
   `TechnicalApprovalsPage.tsx` opens `InterventionReviewViewer.tsx` → Chef clicks
   Approve/Reject → `approvalService.ts:decideTechnicalApproval()` → backend
   `api/approvals.py` (role-checked: `chef_technicien` only) →
   `services/approval_service.py:decide_technical_approval()` →
   `status_transition_service.ensure_transition_allowed()` validates the move →
   `repositories/approval_history_repository.py:create()` writes the permanent decision
   record → on approve, `notification_service.notify_admins_of_technical_approval()`
   fires to every active Admin; on reject,
   `notification_service.notify_technician_of_rejection()` fires to the technician.

4. **The Administration Supervisor performs the second approval**, following the exact
   same pattern as step 3 through `AdministrativeApprovalsPage.tsx` →
   `decide_administrative_approval()` — on approve, the intervention becomes
   permanently locked (`fully_approved`) and
   `notification_service.notify_technician_of_full_approval()` fires.

5. **The technician sees the notification and clicks it.**
   `NotificationsPage.tsx` → `utils/notificationRouting.ts:resolveNotificationPath()`
   decides where to navigate based on the notification's content and the user's role.

6. **Later, anyone with dashboard access checks the numbers.**
   `DashboardPage.tsx` renders the correct role-specific content component
   (`pages/dashboards/*.tsx`) → `dashboardService.ts` calls the matching backend
   endpoint → `services/dashboard_service.py` aggregates KPIs and chart series (the
   period selected via `PeriodModeSelector.tsx` drives every chart on that dashboard at
   once, through one consolidated request rather than one request per chart).

7. **A supervisor pulls a formal report.**
   `ReportsPage.tsx` → `reportService.ts` → `api/reports.py` →
   `services/report_service.py` builds the filtered dataset → optionally,
   `services/export_service.py:render_pdf()`/`render_excel()` turns it into a
   downloadable file.

This is the same order the files are listed in Section 4's diagram, and walking through
it in this order — schedule → submit → technical approve → administrative approve →
notify → dashboard → report — is the clearest way to present "my part of the
application" as one coherent pipeline rather than a list of unrelated features.
