# BIMS — Database Schema

Source of truth: `project_specifications.md`, Part 5 (Chapters 33–53). PostgreSQL. Snake_case tables/columns (Ch.119). No hard deletes — soft-delete via `active`/`status`/`archived` flags (Ch.50). Interventions are never deleted (Rule 9, Ch.20).

## Conventions

- Every table has `id` (PK, `SERIAL`/`BIGSERIAL` or `UUID`), `created_at`, `updated_at` (`TIMESTAMPTZ`, default `now()`).
- Foreign keys use `ON DELETE RESTRICT` by default (Ch.49 "Foreign keys cannot be broken"); nothing cascades into destructive deletes.
- Enums implemented as PostgreSQL `ENUM` types (or `VARCHAR` + `CHECK` — decision left to Phase 2 model implementation, both are spec-compliant).

---

## Enums

### role_name
`technician`, `chef_technicien`, `admin_supervisor` (Ch.36 — exactly 3 roles, no Administrator)

### intervention_status (Ch.9 — 9 states)
`draft`, `planned`, `in_progress`, `submitted`, `pending_technical_approval`, `technical_approved`, `pending_administrative_approval`, `fully_approved`, `rejected`

### intervention_type (Ch.22 Section C)
`standard`, `contract`, `project`, `warranty`

### location_type (Ch.22 Section D)
`sur_site`, `atelier`

### priority (Ch.29, Ch.64, Ch.98)
`normal`, `high`, `urgent`

### approval_level (Ch.47)
`technical`, `administrative`

### approval_decision (Ch.47)
`approved`, `rejected`

### contract_status / project_status (Ch.39, Ch.40, Ch.50)
`active`, `archived`

### planning_status (Ch.45, Ch.142)
`planned`, `in_progress`, `completed`, `cancelled`

---

## Tables

### roles (Ch.36)
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| name | role_name ENUM, UNIQUE, NOT NULL | |

Seed: exactly 3 rows.

---

### users (Ch.35)
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| first_name | VARCHAR(100) NOT NULL | |
| last_name | VARCHAR(100) NOT NULL | |
| username | VARCHAR(50) UNIQUE NOT NULL | |
| password_hash | VARCHAR(255) NOT NULL | bcrypt |
| email | VARCHAR(255) UNIQUE NOT NULL | |
| phone | VARCHAR(30) | |
| role_id | INT FK → roles.id NOT NULL | |
| active | BOOLEAN NOT NULL DEFAULT TRUE | soft delete (Ch.50) |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

Index: `username`, `role_id`.

---

### clients (Ch.37)
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| client_name | VARCHAR(200) NOT NULL | |
| phone | VARCHAR(30) | |
| email | VARCHAR(255) | |
| active | BOOLEAN NOT NULL DEFAULT TRUE | soft delete |
| created_at / updated_at | TIMESTAMPTZ | |

---

### client_sites (Ch.38)
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| client_id | INT FK → clients.id NOT NULL | |
| site_name | VARCHAR(200) NOT NULL | |
| city | VARCHAR(100) NOT NULL | |
| address | VARCHAR(300) | |
| active | BOOLEAN DEFAULT TRUE | |
| created_at / updated_at | TIMESTAMPTZ | |

Index: `client_id`, `city`. Cities are never typed manually anywhere in the app — always derived from this table (Rule 4).

---

### contracts (Ch.39)
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| client_id | INT FK → clients.id NOT NULL | |
| contract_name | VARCHAR(200) NOT NULL | |
| start_date | DATE NOT NULL | |
| end_date | DATE | |
| status | contract_status ENUM DEFAULT 'active' | archived instead of deleted |
| created_at / updated_at | TIMESTAMPTZ | |

Index: `client_id`.

---

### projects (Ch.40)
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| client_id | INT FK → clients.id NOT NULL | |
| project_name | VARCHAR(200) NOT NULL | |
| start_date | DATE NOT NULL | |
| end_date | DATE | |
| status | project_status ENUM DEFAULT 'active' | |
| created_at / updated_at | TIMESTAMPTZ | |

Index: `client_id`.

---

### travaux (Ch.41)
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| travail_code | VARCHAR(20) UNIQUE NOT NULL | e.g. "101" |
| travail_name | VARCHAR(200) NOT NULL | e.g. "Firewall Installation" |
| category | VARCHAR(100) | |
| active | BOOLEAN DEFAULT TRUE | |
| created_at / updated_at | TIMESTAMPTZ | |

Index: `travail_code`.

---

### interventions (Ch.42 — central table)
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| bi_number | VARCHAR(20) UNIQUE NOT NULL | auto-generated `BI000001` (Rule 6) |
| technician_id | INT FK → users.id NOT NULL | owner (Ch.15) |
| client_id | INT FK → clients.id NOT NULL | |
| site_id | INT FK → client_sites.id NOT NULL | |
| contract_id | INT FK → contracts.id NULLABLE | only if type=contract |
| project_id | INT FK → projects.id NULLABLE | only if type=project |
| warranty_reference_id | INT FK → interventions.id NULLABLE | self-reference, only if type=warranty |
| intervention_type | intervention_type ENUM NOT NULL | |
| location_type | location_type ENUM NOT NULL | |
| intervention_date | DATE NOT NULL DEFAULT current_date | |
| start_time | TIME NOT NULL | |
| end_time | TIME NOT NULL | |
| lunch_break_minutes | INT NOT NULL DEFAULT 0 | 0/30/60/90/120/custom |
| net_duration_minutes | INT NOT NULL | backend-computed, never client-supplied |
| number_of_technicians | INT NOT NULL DEFAULT 1 | |
| technical_report | TEXT | comments (Section H) |
| contact_person | VARCHAR(200) | optional (Section B) |
| status | intervention_status ENUM NOT NULL DEFAULT 'draft' | |
| submission_date | TIMESTAMPTZ NULLABLE | |
| technical_approval_date | TIMESTAMPTZ NULLABLE | |
| administrative_approval_date | TIMESTAMPTZ NULLABLE | |
| points_earned | INT NOT NULL DEFAULT 0 | backend-computed (Ch.28) |
| created_at / updated_at | TIMESTAMPTZ | |

Indexes (Ch.52): `bi_number`, `technician_id`, `client_id`, `site_id`, `status`, `submission_date`.
Constraint: `warranty_reference_id` required (NOT NULL) when `intervention_type = 'warranty'` — enforced at service layer (Ch.22 "referenced BI must already exist") plus a DB CHECK where practical.

---

### intervention_tasks (Ch.43 — join table)
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| intervention_id | INT FK → interventions.id NOT NULL | |
| travail_id | INT FK → travaux.id NOT NULL | |

Unique constraint: `(intervention_id, travail_id)`. Index: `intervention_id`.

---

### attachments (Ch.44)
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| intervention_id | INT FK → interventions.id NOT NULL | |
| file_name | VARCHAR(255) NOT NULL | |
| file_path | VARCHAR(500) NOT NULL | relative path under `uploads/` (Ch.126) |
| content_type | VARCHAR(50) | jpg/jpeg/png/pdf only |
| upload_date | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| uploaded_by | INT FK → users.id NOT NULL | |

Index: `intervention_id`. At least one attachment required before an intervention can transition to `submitted` (Rule 7) — enforced in service layer, not DB, since drafts legitimately have zero.

---

### planning (Ch.45)
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| technician_id | INT FK → users.id NOT NULL | |
| client_id | INT FK → clients.id NOT NULL | |
| site_id | INT FK → client_sites.id NOT NULL | |
| intervention_id | INT FK → interventions.id NULLABLE | linked once technician starts the actual BI |
| planned_date | DATE NOT NULL | |
| planned_start_time | TIME NOT NULL | |
| estimated_duration_minutes | INT | |
| priority | priority ENUM NOT NULL DEFAULT 'normal' | |
| status | planning_status ENUM NOT NULL DEFAULT 'planned' | |
| notes | TEXT | |
| created_by | INT FK → users.id NOT NULL | Chef des Techniciens |
| created_at / updated_at | TIMESTAMPTZ | |

Indexes: `technician_id`, `planned_date`, `priority`.

---

### notifications (Ch.46)
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| user_id | INT FK → users.id NOT NULL | recipient |
| title | VARCHAR(200) NOT NULL | |
| message | VARCHAR(500) NOT NULL | |
| related_intervention_id | INT FK → interventions.id NULLABLE | |
| read | BOOLEAN NOT NULL DEFAULT FALSE | |
| created_at | TIMESTAMPTZ NOT NULL DEFAULT now() | |

Index: `user_id`, `read`.

---

### approval_history (Ch.47)
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| intervention_id | INT FK → interventions.id NOT NULL | |
| approval_level | approval_level ENUM NOT NULL | technical / administrative |
| approved_by | INT FK → users.id NOT NULL | |
| decision | approval_decision ENUM NOT NULL | approved / rejected |
| comment | TEXT | |
| approval_date | TIMESTAMPTZ NOT NULL DEFAULT now() | |

Index: `intervention_id`, `approval_date`. Append-only — nothing is ever deleted or updated (Ch.47 "Nothing is deleted", Ch.20).

---

### audit_log (Ch.18, Ch.151 — supports full audit trail)
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| intervention_id | INT FK → interventions.id NOT NULL | |
| user_id | INT FK → users.id NOT NULL | |
| action | VARCHAR(50) NOT NULL | created / draft_saved / modified / submitted / technical_approved / administrative_approved / rejected / resubmitted |
| comment | TEXT | |
| created_at | TIMESTAMPTZ NOT NULL DEFAULT now() | |

Index: `intervention_id`. Append-only, never deleted.

---

## Entity Relationships (Ch.48)

```
roles 1──* users
users 1──* interventions        (technician_id, owner)
users 1──* planning              (technician_id)
users 1──* notifications         (user_id)
users 1──* approval_history      (approved_by)
users 1──* attachments           (uploaded_by)

clients 1──* client_sites
clients 1──* contracts
clients 1──* projects
clients 1──* interventions
clients 1──* planning

client_sites 1──* interventions
client_sites 1──* planning

contracts 1──* interventions     (nullable FK)
projects  1──* interventions     (nullable FK)

interventions 1──* intervention_tasks *──1 travaux
interventions 1──* attachments
interventions 1──* approval_history
interventions 1──* audit_log
interventions 1──1 interventions (self-ref: warranty_reference_id, nullable)
interventions 1──* notifications (related_intervention_id, nullable)
interventions 1──0/1 planning    (planning.intervention_id, nullable)
```

## Constraints Summary (Ch.49)

- Every user has exactly one role (`users.role_id` NOT NULL FK).
- Every intervention belongs to exactly one technician, one client, one client site (`interventions.technician_id/client_id/site_id` NOT NULL FK).
- Every attachment belongs to one intervention (NOT NULL FK).
- Every notification belongs to one user (NOT NULL FK).
- Every approval belongs to one intervention (NOT NULL FK).
- `interventions.status` is a single ENUM column — one current status by construction.
- `bi_number` UNIQUE NOT NULL.
- No FK uses `ON DELETE CASCADE` into interventions/approval_history/audit_log — deletion is structurally prevented; the app never issues DELETE on these tables.

## Cascade / Soft-Delete Rules (Ch.50)

| Entity | "Delete" behavior |
|---|---|
| users | `active = false` |
| clients | `active = false` |
| travaux | `active = false` |
| projects | `status = 'archived'` |
| contracts | `status = 'archived'` |
| interventions | never removed or archived — status transitions only |

## Indexing Plan (Ch.52)

`bi_number`, `technician_id`, `client_id`, `site_id`, `status`, `planned_date` (on planning), `submission_date`, `approval_date` (on approval_history) — all listed above per-table.
