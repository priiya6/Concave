# Concave Insights checkpoint

## Current status & phase
Final verification phase: core workflows, bonus APIs, migration lifecycle, responsive routes, tests, and live HTTP smoke verified.

## Completed tasks
- Preserved the frozen Day 2 design files and existing incremental Git history.
- Verified FastAPI/SQLite ticket workflows, role permissions, TAT, waiting-for-member pause/resume, escalation, notifications, auto-close, internal tickets, saved replies, and dashboard APIs.
- Added visible staff assignment/unassignment, priority-change reason, and resolve controls with success/error feedback.
- Added reopen policy regression coverage and fixed SQLite-aware UTC comparisons.
- Replaced the bootstrap migration with a real Alembic lifecycle backed by checked SQLAlchemy metadata.
- Corrected README and Windows run documentation; recorded a manual browser checklist because no browser runtime was available.

## Pending tasks
- Full route-level frontend tests and full saved-reply/internal-ticket panels remain optional follow-up work; backend/API workflows are verified.

## Architecture & key decisions
- Python/FastAPI + SQLAlchemy/Alembic backend; React/TypeScript/Vite frontend.
- SQLite local database; UTC timestamps; continuous 24x7 TAT; waiting is a flag, not a status.
- Frozen design files are not edited after Phase 1; divergences use `*-v2.md`.

## Files created/modified
- Backend: `app/main.py`, `tests/test_api.py`, `alembic/env.py`, `alembic/versions/0001_initial.py`.
- Frontend: `src/main.tsx`, `src/style.css`.
- Documentation: `README.md`, `RUN_PROJECT.md`, `status.md`.

## Database & migration status
PASS: `alembic downgrade base` followed by `alembic upgrade head` recreates all ten application tables. Fresh migration, seed, reset/seed, and existing-database upgrade paths were checked.

## API implementation status
- PASS: auth, users/staff, ticket workflow actions, notifications, dashboards, admin settings/jobs, internal tickets, saved replies, auto-close, validation/error envelopes, and staff action endpoints.

## Frontend implementation status
- PASS: login, role shell, member create/list/detail/confirm/reopen, queue filters, Head dashboard/escalations/settings, notification polling, responsive styling, and visible staff assignment/priority/resolve controls.
- PARTIAL: saved-reply picker and internal-ticket panel are not full UI surfaces; focused component tests exist.

## Test results
Backend: 8 passed. Frontend: 2 passed; production build passed. Migration downgrade/upgrade and ten-table inspection passed. Live HTTP smoke passed for member login, Head login, ticket creation, dashboard, and health. No browser executable or Playwright package was available. Mermaid CLI could not run because npm was cache-only.

## Known bugs & resolved issues
- Fixed duplicate SQLite index, SQLite-naive datetime comparisons, JSONResponse argument order, pytest import path, Alembic module path, and live-target serializer regression.
- Fixed reopen policy comparisons for SQLite timestamps and added window/max-attempt coverage.
- Vitest worker spawning hit Windows sandbox `EPERM`; single-thread mode is configured and tests pass.
- Browser and Mermaid rendering verification were unavailable and are not claimed.

## Exact next steps
- Run the manual browser walkthrough in `RUN_PROJECT.md` at 375px, 768px, and 1280px.
- If desired, add full saved-reply/internal-ticket panels and route-level frontend tests.
- Re-run the documented clean setup before assessment submission.

## Git commits
- `3f65dbb` docs: add Day 2 user flow (pushed)
- `8ae22ab` docs: add database ERD (pushed)
- `61ec54e` docs: add design README, root README, status and handoff (pushed)
- `79ad1db` feat: build support ticketing core (local, unpushed)
- `0c6ebf6` chore: ignore frontend build metadata (local, unpushed)
- `3c28e40` fix: make local alembic setup runnable (local, unpushed)
- `033c8c0` feat: complete workflow and bonus API milestone (pushed)
- `b6654df` feat: finish queue filters and verification polish (pushed)
- `77a2378` feat: add head settings and notification polling (pushed)
- `88ce7f2` docs: record pushed UI milestone (pushed)
- `17f30d4` feat: complete member and escalation workflows (pushed)
- `586a10c` docs: record final workflow milestone (pushed)
- `caae724` docs: record final verification results (pushed)
- Current uncommitted changes: migration lifecycle, staff controls/reopen regression, and documentation corrections.

## Does the latest build and test run pass?
Yes: backend pytest (8 passed), frontend tests (2 passed), frontend production build, fresh migration, downgrade/upgrade, reset/seed, and live HTTP smoke all pass. Browser automation was unavailable.

## Suggested push plan
- Commit the migration lifecycle, staff action/reopen coverage, and documentation corrections as separate verified commits.
- Push those commits to `origin main` after the final checks.
