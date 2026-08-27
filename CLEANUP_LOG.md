# Repository Cleanup Log

Every change made during the repo cleanup pass on 2026-08-27. Nothing here
touches how the app runs — this log only records files being relocated into
a new `additions/` folder, plus a full record of what was checked and
confirmed safe *not* to move. If anything about the app's behavior seems
different after this pass, check this file first: every move is a plain
file relocation, no code was edited.

**How to undo any single item:** move the file back from `additions/<same
relative path>` to its original location listed below. Nothing was deleted —
every move is reversible by reversing it.

## Method

1. A full read-only audit was run first (Explore agent) covering every file
   and folder in the repo, checking what's actually imported/run by the
   live app versus what's genuinely unreferenced.
2. Every "dead code" finding was independently re-verified by hand (direct
   `grep` across `frontend/src`) before being trusted — the audit's word
   alone was not treated as sufficient for anything that gets moved.
3. Scope was confirmed with the user in two rounds of explicit questions
   before any file was touched: (a) markdown-file scope — all `.md` files
   except `README.md` — and (b) whether files already flagged in
   `.gitignore` as sensitive/personal-prep material should still move
   (confirmed yes), and whether 2 confirmed-dead frontend components should
   move too (confirmed yes).
4. Only after both confirmations did any move happen.

## What was moved

| # | Original path | New path | Why |
|---|---|---|---|
| 1 | `ARCHITECTURE.md` | `additions/ARCHITECTURE.md` | Markdown doc, not README.md |
| 2 | `API_SPEC.md` | `additions/API_SPEC.md` | Markdown doc, not README.md |
| 3 | `DATABASE_SCHEMA.md` | `additions/DATABASE_SCHEMA.md` | Markdown doc, not README.md |
| 4 | `FUTURE_DATABASE_INTEGRATION.md` | `additions/FUTURE_DATABASE_INTEGRATION.md` | Markdown doc, not README.md |
| 5 | `NOTIFICATIONS.md` | `additions/NOTIFICATIONS.md` | Markdown doc, not README.md |
| 6 | `SYNTHETIC_DATABASE.md` | `additions/SYNTHETIC_DATABASE.md` | Markdown doc, not README.md |
| 7 | `TASKS.md` | `additions/TASKS.md` | Markdown doc, not README.md |
| 8 | `WORK_SUMMARY.md` | `additions/WORK_SUMMARY.md` | Markdown doc, not README.md |
| 9 | `internship_report_extraction.md` | `additions/internship_report_extraction.md` | Markdown doc, not README.md |
| 10 | `project_specifications.md` | `additions/project_specifications.md` | Markdown doc, not README.md |
| 11 | `my_contribution/` (whole folder) | `additions/my_contribution/` | Self-described in its own README as stale copies, not the working source; verified stale by diffing a sample file against the real `backend/app/services/planning_service.py` |
| 12 | `future_ai_validation/` (whole folder) | `additions/future_ai_validation/` | Prototype-only; every backend/frontend file uses a `.py.example`/`.tsx.example` extension specifically so it cannot be imported/run; confirmed never referenced by `main.py` or any route |
| 13 | `frontend/src/components/FilterPanel.tsx` | `additions/frontend/src/components/FilterPanel.tsx` | Confirmed dead code: `grep -i "FilterPanel"` across all of `frontend/src` finds only the file's own declaration, zero import sites anywhere. Re-verified independently, not just taken from the audit. `npx tsc --noEmit` and `npm run lint` both pass clean after removal. |
| 14 | `frontend/src/components/PriorityBadge.tsx` | `additions/frontend/src/components/PriorityBadge.tsx` | Same as above: `grep -i "PriorityBadge"` across all of `frontend/src` finds only the file's own declaration. Re-verified independently. |
| 15 | `frontend/verify-unbounded.png` | `additions/frontend/verify-unbounded.png` | Untracked leftover verification screenshot from an earlier session; referenced by nothing in `index.html`, CSS, or any component |

## What was explicitly confirmed to stay in place (not moved)

- `README.md` — the one markdown file the user explicitly excluded from the move.
- Everything under `backend/` except nothing — the entire backend tree is untouched. Verified: 18 model files, 22 service files, 18 API router files, 8 Alembic migrations (single linear chain, single head) all present and unchanged after the move. Full backend test suite spot-check (`tests/test_deactivation_and_deletion.py`, 21 tests) passes clean post-cleanup.
- `backend/dev.db` — this is the app's real pre-seeded SQLite dataset (README's own documented zero-setup Quick Start data), not a stale/throwaway database file. Confirmed present and unchanged.
- `docker-compose.yml` — defines the real Postgres+backend+frontend services, referenced by README.
- Every file under `frontend/src/` except the 2 confirmed-dead components above. `npx tsc --noEmit -p tsconfig.app.json` and `npm run lint` both run clean with zero new errors/warnings after the move — confirming nothing else in the running app depended on anything that moved.
- All config files at both `backend/` and `frontend/` root level (`.env`, `.env.example`, `requirements.txt`, `package.json`, `vite.config.ts`, `tsconfig*.json`, `Dockerfile` ×2, `pytest.ini`, `alembic.ini`, etc.) — none of these are markdown, none were flagged as dead code.

## Known pre-existing issue found during the audit, NOT fixed by this cleanup (flagged separately to the user)

Several of the files moved above (`ARCHITECTURE.md`, `WORK_SUMMARY.md`, `SYNTHETIC_DATABASE.md`, `FUTURE_DATABASE_INTEGRATION.md`, `internship_report_extraction.md`, `my_contribution/`, `future_ai_validation/`) were already listed in `.gitignore` under a section stating they should "never be pushed" — but they were tracked in git already before that ignore rule was added, so the rule has been silently doing nothing. Moving them into `additions/` does not remove them from git history; that is a separate, unresolved concern the user was made aware of and chose to leave as-is for this pass.
