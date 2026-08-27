# BIMS — API Specification

Source: `project_specifications.md` Chapter 83 (Main API Modules), expanded per Ch.79–82, 87. Base path: `/api`. All responses use the standardized envelope (Ch.82). All endpoints except `/auth/login` require `Authorization: Bearer <JWT>`.

## Response Envelope (Ch.82)

Success:
```json
{ "success": true, "message": "Intervention created.", "data": { ... } }
```
Error:
```json
{ "success": false, "message": "Client not found." }
```
Validation error:
```json
{ "success": false, "errors": ["Client is required", "Start Time is required"] }
```

## Roles shorthand
- **T** = Technician, **C** = Chef des Techniciens, **A** = Administration Supervisor,
  **D** = Display (Task 3, post-launch — a strictly read-only hallway-calendar
  account; not part of the original SRS's 3-role model, so it is omitted from
  endpoints below unless explicitly noted)

---

## Auth (Ch.140, Ch.79)

| Method | Path | Roles | Description |
|---|---|---|---|
| POST | /auth/login | public | `{username, password}` → JWT + user profile |
| POST | /auth/logout | T/C/A | invalidate session (client discards token; server may blacklist) |
| GET | /auth/me | T/C/A | current user profile (id, name, role, department) |

---

## Users (Ch.83, Ch.150) — Admin Supervisor manages

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /users | A (C: read-only list of technicians) | paginated, search, filter by role/active |
| GET | /users/technicians | T/C/A | lightweight technician id/name list — colleague-technician pickers |
| GET | /users/chefs | C/A | lightweight chef id/name list |
| GET | /users/{id} | A | |
| POST | /users | A | create user, hash password |
| PUT | /users/{id} | A | update profile/role |
| PATCH | /users/{id}/activate | A | Ch.12 "User activation" |
| PATCH | /users/{id}/deactivate | A | Ch.12 "User deactivation" |
| PATCH | /users/{id}/reset-password | A | Ch.12 "Reset passwords" |

---

## Clients (Ch.83, Ch.150) — Admin manages, all roles read

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /clients | T/C/A | dropdown source (Rule 3), search/pagination |
| GET | /clients/{id} | T/C/A | |
| POST | /clients | A | |
| PUT | /clients/{id} | A | |
| PATCH | /clients/{id}/deactivate | A | soft delete (Ch.50) |
| PATCH | /clients/{id}/activate | A | reactivate |

---

## Client Sites (Ch.83, Ch.38)

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /sites | T/C/A | all sites, filterable by city |
| GET | /clients/{id}/sites | T/C/A | Rule 4 — cities filtered by selected client |
| GET | /sites/{id} | T/C/A | |
| POST | /sites | A | |
| PUT | /sites/{id} | A | |
| PATCH | /sites/{id}/deactivate | A | |
| PATCH | /sites/{id}/activate | A | reactivate |

---

## Contracts (Ch.83, Ch.39)

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /contracts | T/C/A | filterable by client, status |
| GET | /clients/{id}/contracts | T/C/A | for the Contract intervention-type dropdown |
| GET | /contracts/{id} | T/C/A | |
| POST | /contracts | A | |
| PUT | /contracts/{id} | A | |
| PATCH | /contracts/{id}/archive | A | |

---

## Projects (Ch.83, Ch.40)

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /projects | T/C/A | filterable by client, status |
| GET | /clients/{id}/projects | T/C/A | for the Project intervention-type dropdown |
| GET | /projects/{id} | T/C/A | |
| POST | /projects | A | |
| PUT | /projects/{id} | A | |
| PATCH | /projects/{id}/archive | A | |

---

## Travaux Catalog (Ch.83, Ch.41)

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /travaux | T/C/A | dropdown source, search by code/name |
| GET | /travaux/{id} | T/C/A | |
| POST | /travaux | A | |
| PUT | /travaux/{id} | A | |
| PATCH | /travaux/{id}/deactivate | A | |
| PATCH | /travaux/{id}/activate | A | reactivate |

---

## Point Rules (Task 2, post-launch) — Administrator-only configuration

Replaces the previously hardcoded Ch.28 point-award windows. See `DATABASE_SCHEMA.md`
for the `point_rules` table and `ARCHITECTURE.md` §1.12 for the full rationale
(historical points are never recalculated when a rule changes).

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /point-rules | A | list all rules (optional `?active_only=true`) |
| GET | /point-rules/{id} | A | |
| POST | /point-rules | A | create; rejects an interval identical to itself, and rejects any overlap with another currently-active rule (409) |
| PUT | /point-rules/{id} | A | update; same overlap validation as create |
| PATCH | /point-rules/{id}/deactivate | A | |
| PATCH | /point-rules/{id}/activate | A | reactivate; still checked against currently-active rules for overlap (409 if the window is now occupied) |
| DELETE | /point-rules/{id} | A | permanent hard delete — safe because no other table holds a foreign key to `point_rules.id` |

No T/C read access — unlike travaux/clients/etc., no other role ever needs to fetch
this list (the point calculation itself runs server-side, not via an API call the
frontend makes).

---

## Interventions (Ch.83, Ch.42, Ch.57–60) — the core module

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /interventions | T (own only, Ch.16) / C/A (all, with filters) | pagination, search (BI/client/site/technician/project/contract), filters (date, status, priority, client, technician, site, type) |
| GET | /interventions/{id} | T (own) / C/A (any) | full detail incl. tasks, attachments, approval history, audit trail |
| POST | /interventions | T | create as draft or submitted (`status` param); backend generates `bi_number`, computes `net_duration_minutes`, validates warranty reference exists |
| PUT | /interventions/{id} | T (own, only if draft/rejected — Ch.15, Ch.17) | edit; re-locks on resubmission |
| POST | /interventions/{id}/submit | T (own) | Ch.24 — validates required fields + ≥1 attachment (Rule 7), sets status→submitted, submission_date, points_earned, triggers notification to Chef |
| GET | /interventions/{id}/history | T (own)/C/A | audit trail (Ch.18) |

No DELETE endpoint exists — interventions are never deleted (Rule 9).

---

## Intervention Tasks (Ch.43)

Travaux are not managed via separate task endpoints — `travail_ids: list[int]` is a plain field on the `POST /interventions` and `PUT /interventions/{id}` payloads (see above), replacing the intervention's full task list in one call rather than adding/removing lines individually.

---

## Attachments (Ch.83, Ch.44, Ch.81, Ch.152)

| Method | Path | Roles | Description |
|---|---|---|---|
| POST | /attachments | T (own intervention, draft/rejected) | multipart upload; validates JPG/JPEG/PNG/PDF, max size (config); stores under `uploads/YYYY/MM/BI0000NN/` |
| GET | /attachments/{id} | T (own)/C/A | file metadata + signed/relative path |
| GET | /attachments/{id}/download | T (own)/C/A | stream file |
| DELETE | /attachments/{id} | T (own, draft/rejected) | replace-before-approval (Ch.152) |

---

## Planning (Ch.83, Ch.45, Ch.63, Ch.142) — Chef des Techniciens and Admin Supervisor write, Technician reads own

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /planning/display | D/C/A | Task 3, post-launch — global, non-cancelled planning with technician/client/site names already resolved server-side; the display role's only reachable endpoint anywhere in the API. Registered before `/planning/{id}` so the literal path segment isn't captured as an id. |
| GET | /planning | C/A (all) / T (own, read-only) | filterable by technician, date range, priority, status |
| GET | /planning/{id} | C/A (any) / T (own) | single planning entry detail |
| POST | /planning | C/A | create planned intervention; notifies assigned technician |
| PUT | /planning/{id} | C/A | edit before technician starts (Ch.142) |
| DELETE | /planning/{id} | C/A | cancel — soft: `status='cancelled'`, history retained, technician notified |
| POST | /planning/{id}/urgent | C/A | Ch.64 — flag/create as urgent priority, immediate notification |
| PUT | /planning/urgent-queue/reorder | C/A | reorder the urgent queue's display order via a list of ordered planning ids |

Live updates on `/planning/display` are frontend-driven controlled polling
(TanStack Query `refetchInterval`, 20s) — there is no server push mechanism, and none
was added; see `ARCHITECTURE.md` §1.13.

---

## Approvals (Ch.83, Ch.25–26, Ch.145)

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /approvals/my-recent-decisions | C/A | the caller's own recent approve/reject decisions |
| GET | /approvals/technical-pending | C | queue for Chef |
| GET | /approvals/administrative-pending | A | queue for Admin Supervisor |
| POST | /interventions/{id}/technical-approval | C | `{decision, comment}`; approved→status=pending_administrative_approval + notifies Admin; rejected→status=rejected + notifies technician; always writes approval_history + audit_log |
| POST | /interventions/{id}/administrative-approval | A | `{decision, comment}`; approved→status=fully_approved (locked permanently); rejected→status=rejected + notifies technician |

---

## Dashboard (Ch.83, Ch.56, Ch.61, Ch.65, Ch.107–111)

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /dashboard/technician | T | own KPI cards, today's planning, recent notifications |
| GET | /dashboard/technician/charts | T | `mode`/`anchor` query params select the chart period; weekly-completed + monthly-points chart series |
| GET | /dashboard/supervisor | C | team KPIs, pending technical approvals, urgent queue, workload |
| GET | /dashboard/supervisor/charts | C | `mode`/`anchor` query params; team chart series |
| GET | /dashboard/admin | A | global KPIs, approval rates, charts data |
| GET | /dashboard/admin/charts | A | `mode`/`anchor` query params; global chart series |

All dashboard endpoints return pre-aggregated stats computed server-side (Ch.115) — never raw row dumps.

---

## Reports (Ch.83, Ch.71, Ch.112–114)

Revised in Phase 9 to cover the full Ch.71 list of 10 report types through one
consistent pattern rather than 10 bespoke endpoints, since 8 of them
(Daily/Weekly/Monthly/Yearly/Technician/Client/Project/Contract) are all "list
of interventions matching a filter set" and only differ in which filter is
pre-applied — the frontend is what supplies that default filter (e.g. a
"Client Report" pre-fills `client_id`), the backend just accepts whichever
combination of filters is given.

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /reports | C/A | list all 10 available report types (key + label) |
| GET | /reports/interventions | C/A | Daily/Weekly/Monthly/Yearly/Technician/Client/Project/Contract reports — one endpoint, `type` query param selects the label + default date window; `date_from`/`date_to`/`technician_id`/`client_id`/`project_id`/`contract_id` all optional and combinable (Ch.113 "generated directly from current filters") |
| GET | /reports/approval | C/A | Approval Report (Ch.47 approval_history, not filtered by the interventions table) |
| GET | /reports/planning | C/A | Planning Report (Ch.45 planning, not filtered by the interventions table) |
| GET | /reports/comparison | C/A | Ch.114 historical comparison — two independent date ranges (+ optional technician/client filter), returned side-by-side |
| GET | /reports/export.pdf | C/A | same `report` (`interventions`\|`approval`\|`planning`) + filters as whichever report is currently open, streams PDF; `type` is additionally required (400 if omitted) when `report=interventions`, same values as `GET /reports/interventions` |
| GET | /reports/export.xlsx | C/A | same as above, streams Excel |

---

## Technician Performance

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /technician-performance | C/A | summary list, one row per technician (points/completion metrics) |
| GET | /technician-performance/me | T | own performance detail — always the caller's own id, never a client-supplied one |
| GET | /technician-performance/{technician_id} | C/A | performance detail for a specific technician |

---

## Notifications (Ch.83, Ch.46, Ch.70)

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /notifications | T/C/A | own notifications, paginated, unread-first |
| PATCH | /notifications/{id}/read | T/C/A | mark read |
| PATCH | /notifications/read-all | T/C/A | mark all read |

---

## Calendar (Ch.59, Ch.63, Ch.143) — served via existing endpoints

FullCalendar frontend consumes `GET /planning` and `GET /interventions` with `date_from`/`date_to` query params — no separate calendar API needed.

---

## Cities (Ch.5 term, Ch.12) — derived, not a standalone CRUD module

Cities are not a top-level entity per Ch.38: they live as `client_sites.city`. "Manage cities" (Ch.12, Admin permission) is satisfied through `GET/POST/PUT /sites`.

---

## Permanent Deletion (Task 5, post-launch) — Administrator-only

Every administrative entity that supports soft-delete also supports a
**permanent** delete, plus a pre-flight check the UI uses to warn before
confirming. Deletion is refused (409) whenever anything still references the
record — see `DATABASE_SCHEMA.md` and `deletion_service.py`.

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /users/{id}/deletion-check | A | `{deletable, blockers[]}` — what (if anything) blocks deletion |
| DELETE | /users/{id} | A | permanent delete; 409 with an explanation if referenced |
| GET | /clients/{id}/deletion-check | A | |
| DELETE | /clients/{id} | A | |
| GET | /sites/{id}/deletion-check | A | |
| DELETE | /sites/{id} | A | |
| GET | /contracts/{id}/deletion-check | A | |
| DELETE | /contracts/{id} | A | |
| GET | /projects/{id}/deletion-check | A | |
| DELETE | /projects/{id} | A | |
| GET | /travaux/{id}/deletion-check | A | |
| DELETE | /travaux/{id} | A | |

Interventions still have **no** DELETE endpoint (Rule 9), and nothing here
cascades into `interventions`, `approval_history` or `audit_log`.

---

## Authorization Matrix (Ch.80)

| Endpoint prefix | T | C | A | D |
|---|---|---|---|---|
| /interventions (own) | RW | R (all) | R (all) | ✖ |
| /interventions/{id}/technical-approval | ✖ | ✔ | ✖ | ✖ |
| /interventions/{id}/administrative-approval | ✖ | ✖ | ✔ | ✖ |
| /planning | R (own) | RW (all) | RW (all) | ✖ |
| /planning/display (Task 3) | ✖ | R (all) | R (all) | R (all) |
| /users, /clients (write), /contracts (write), /projects (write), /travaux (write) | ✖ | ✖ | ✔ | ✖ |
| /point-rules (Task 2) | ✖ | ✖ | ✔ | ✖ |
| /dashboard/technician | ✔ | ✖ | ✖ | ✖ |
| /dashboard/supervisor | ✖ | ✔ | ✖ | ✖ |
| /dashboard/admin | ✖ | ✖ | ✔ | ✖ |
| /reports | ✖ | ✔ | ✔ | ✖ |

Backend enforces every row via a role-checking dependency (Ch.80) — the frontend hiding menu items is a UX convenience only, never the security boundary. The display role (D) is deliberately absent (✖) from every row except its own — it was never added to any pre-existing router's allowed-roles list.
