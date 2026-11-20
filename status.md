# Concave Insights checkpoint

## Current status & phase
Phase 2/3 — core backend and responsive frontend shell implemented; local checkpoint ready.

## Completed tasks
- Confirmed the remote repository was empty; default branch is `main`.
- Confirmed local tools: Python 3.14.2, Node 22.18.0, npm 11.12.1, Git 2.50.1.
- Added frozen Day 2 flow/ERD design, repository hygiene, handoff, and initial README.
- Mermaid CLI attempt was blocked because npm is offline/cache-only; source blocks were manually checked and will be revalidated when package access is available.
- Backend core API, seed/reset scripts, settings/escalation endpoints, member UI, staff shell, and responsive styling are implemented.

## Pending tasks
- Add full service-layer TAT/escalation/reopen tests and expand seed scenarios.
- Add detailed staff/head routes, dialogs, notifications UI, and bonus features.

## Architecture & key decisions
- Python/FastAPI + SQLAlchemy/Alembic backend; React/TypeScript/Vite/Tailwind frontend.
- SQLite local database; UTC timestamps; continuous 24x7 TAT; waiting is a flag, not a status.
- Frozen design files are not edited after Phase 1; divergences use `*-v2.md`.

## Files created/modified
- Root: `.gitignore`, `.gitattributes`, `CODEX_HANDOFF.md`, `status.md`, `README.md`.
- Design: `design/user-flow.md`, `design/database-erd.md`, `design/README.md`.

## Database & migration status
Core SQLAlchemy metadata creates the local SQLite schema; `alembic/env.py` supports local `upgrade head` by creating metadata. A checked SQL migration still needs to be generated.

## API implementation status
✔ auth, users/staff, ticket workflow actions, notifications, dashboards, admin settings/jobs. ✘ internal tickets, saved replies, complete background sweep.

## Frontend implementation status
✔ login, role shell, member create/list, staff queue shell, responsive styling. ✘ ticket detail route, full filters/dialogs/head settings pages.

## Test results
Backend: 3 passed. Frontend: build passed; Vitest reports no test files. Mermaid CLI could not run because npm was cache-only (`ENOTCACHED`).

## Known bugs & resolved issues
- Remote clone initially failed in the sandbox; rerun with approved network access succeeded and confirmed the remote is empty.
- Fixed duplicate SQLite index, UTC-naive SQLite datetime comparisons, JSONResponse argument order, and pytest import path.

## Exact next steps
- Add UTCDateTime decorator and generated initial migration.
- Implement background escalation/auto-close loop and full target recomputation tests.
- Build staff ticket detail, head dashboard/settings/escalations, and notification UI.
- Add frontend RTL tests and broaden backend workflow/permission/concurrency tests.

## Git commits
- `3f65dbb` docs: add Day 2 user flow (pushed)
- `8ae22ab` docs: add database ERD (pushed)
- `61ec54e` docs: add design README, root README, status and handoff (pushed)
- `79ad1db` feat: build support ticketing core (local, unpushed)

## Does the latest build and test run pass?
Yes for the current checkpoint: `pytest -q` (3 passed), `npm run build` (passed), `npm test -- --passWithNoTests` (no test files, exit 0).

## Suggested push plan
- Phase 1: push the three documentation commits together.
- Later phases: keep local; push only after review in sensible feature batches.
- Current local batch: `79ad1db` — push after the remaining implementation and review.
