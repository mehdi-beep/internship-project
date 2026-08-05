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
- **T** = Technician, **C** = Chef des Techniciens, **A** = Administration Supervisor

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

---

## Client Sites (Ch.83, Ch.38)

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /sites | T/C/A | all sites, filterable by city |
| GET | /clients/{id}/sites | T/C/A | Rule 4 — cities filtered by selected client |
| POST | /sites | A | |
| PUT | /sites/{id} | A | |
| PATCH | /sites/{id}/deactivate | A | |

---

## Contracts (Ch.83, Ch.39)

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /contracts | T/C/A | filterable by client, status |
| GET | /clients/{id}/contracts | T/C/A | for the Contract intervention-type dropdown |
| POST | /contracts | A | |
| PUT | /contracts/{id} | A | |
| PATCH | /contracts/{id}/archive | A | |

---

## Projects (Ch.83, Ch.40)

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /projects | T/C/A | filterable by client, status |
| GET | /clients/{id}/projects | T/C/A | for the Project intervention-type dropdown |
| POST | /projects | A | |
| PUT | /projects/{id} | A | |
| PATCH | /projects/{id}/archive | A | |

---

## Travaux Catalog (Ch.83, Ch.41)

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /travaux | T/C/A | dropdown source, search by code/name |
| POST | /travaux | A | |
| PUT | /travaux/{id} | A | |
| PATCH | /travaux/{id}/deactivate | A | |

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

## Intervention Tasks (Ch.43) — nested under interventions

| Method | Path | Roles | Description |
|---|---|---|---|
| POST | /interventions/{id}/tasks | T (own, draft/rejected) | attach travail_id(s) |
| DELETE | /interventions/{id}/tasks/{task_id} | T (own, draft/rejected) | remove a task line before submission |

---

## Attachments (Ch.83, Ch.44, Ch.81, Ch.152)

| Method | Path | Roles | Description |
|---|---|---|---|
| POST | /attachments | T (own intervention, draft/rejected) | multipart upload; validates JPG/JPEG/PNG/PDF, max size (config); stores under `uploads/YYYY/MM/BI0000NN/` |
| GET | /attachments/{id} | T (own)/C/A | file metadata + signed/relative path |
| GET | /attachments/{id}/download | T (own)/C/A | stream file |
| DELETE | /attachments/{id} | T (own, draft/rejected) | replace-before-approval (Ch.152) |

---

## Planning (Ch.83, Ch.45, Ch.63, Ch.142) — Chef des Techniciens only

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /planning | C (all) / T (own, read-only) / A (read) | filterable by technician, date range, priority, status |
| POST | /planning | C | create planned intervention; notifies assigned technician |
| PUT | /planning/{id} | C | edit before technician starts (Ch.142) |
| DELETE | /planning/{id} | C | cancel — soft: `status='cancelled'`, history retained, technician notified |
| POST | /planning/{id}/urgent | C | Ch.64 — flag/create as urgent priority, immediate notification |

---

## Approvals (Ch.83, Ch.25–26, Ch.145)

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /approvals/technical-pending | C | queue for Chef |
| GET | /approvals/administrative-pending | A | queue for Admin Supervisor |
| POST | /interventions/{id}/technical-approval | C | `{decision, comment}`; approved→status=pending_administrative_approval + notifies Admin; rejected→status=rejected + notifies technician; always writes approval_history + audit_log |
| POST | /interventions/{id}/administrative-approval | A | `{decision, comment}`; approved→status=fully_approved (locked permanently); rejected→status=rejected + notifies technician |

---

## Dashboard (Ch.83, Ch.56, Ch.61, Ch.65, Ch.107–111)

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | /dashboard/technician | T | own KPI cards, today's planning, recent notifications |
| GET | /dashboard/supervisor | C | team KPIs, pending technical approvals, urgent queue, workload |
| GET | /dashboard/admin | A | global KPIs, approval rates, charts data |

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
| GET | /reports/export.pdf | C/A | same `report` (`interventions`\|`approval`\|`planning`) + filters as whichever report is currently open, streams PDF |
| GET | /reports/export.xlsx | C/A | same as above, streams Excel |

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

## Authorization Matrix (Ch.80)

| Endpoint prefix | T | C | A |
|---|---|---|---|
| /interventions (own) | RW | R (all) | R (all) |
| /interventions/{id}/technical-approval | ✖ | ✔ | ✖ |
| /interventions/{id}/administrative-approval | ✖ | ✖ | ✔ |
| /planning | R (own) | RW (all) | R |
| /users, /clients (write), /contracts (write), /projects (write), /travaux (write) | ✖ | ✖ | ✔ |
| /dashboard/technician | ✔ | ✖ | ✖ |
| /dashboard/supervisor | ✖ | ✔ | ✖ |
| /dashboard/admin | ✖ | ✖ | ✔ |
| /reports | ✖ | ✔ | ✔ |

Backend enforces every row via a role-checking dependency (Ch.80) — the frontend hiding menu items is a UX convenience only, never the security boundary.
