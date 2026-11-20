# Concave Insights checkpoint

## Current status & phase
Final verification phase — core workflows, bonus APIs, responsive UI routes, tests, and live HTTP smoke verified.

## Completed tasks
- Confirmed the remote repository was empty; default branch is `main`.
- Confirmed local tools: Python 3.14.2, Node 22.18.0, npm 11.12.1, Git 2.50.1.
- Added frozen Day 2 flow/ERD design, repository hygiene, handoff, and initial README.
- Mermaid CLI attempt was blocked because npm is offline/cache-only; source blocks were manually checked and will be revalidated when package access is available.
- Backend core API, seed/reset scripts, settings/escalation endpoints, member UI, staff shell, and responsive styling are implemented.
- Added automatic background job loop, auto-close, internal tickets, saved replies, richer seed data, ticket detail, dashboard metrics UI, and frontend component tests.
- Added queue status/category/priority/member search controls, database/unexpected-error envelopes, and verified live HTTP login/create/dashboard flow.
- Added Head settings page, Run checks control, and notification unread polling.

## Pending tasks
- Add richer staff assignment/priority dialogs and expand frontend workflow tests if further assessment polish is needed.
- Replace metadata-backed Alembic bootstrap with a fully generated SQL revision.

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
✔ auth, users/staff, ticket workflow actions, notifications, dashboards, admin settings/jobs, internal tickets, saved replies, auto-close. ✘ complete validation/error handler and all endpoint polish.

## Frontend implementation status
✔ login, role shell, member create/list, ticket detail, staff queue shell, head dashboard shell, responsive styling, StatusBadge tests. ✘ full filters/dialogs/settings/notifications UI.

## Test results
Backend: 8 passed. Frontend: 2 passed; production build passed. Live HTTP smoke passed for member login, Head login, ticket creation, dashboard, and health. No browser executable/Playwright package was available. Mermaid CLI could not run because npm was cache-only (`ENOTCACHED`).

## Known bugs & resolved issues
- Remote clone initially failed in the sandbox; rerun with approved network access succeeded and confirmed the remote is empty.
- Fixed duplicate SQLite index, UTC-naive SQLite datetime comparisons, JSONResponse argument order, pytest import path, and Alembic module path.
- Fixed live-target serializer regression discovered by the expanded test suite.
- Vitest worker spawning hit Windows sandbox `EPERM`; switched to single-thread mode and verified tests pass.
- Browser verification was unavailable; recorded rather than claimed.

## Exact next steps
- Finish staff/head controls and member confirmation/reopen UI.
- Add real Alembic revision parity and injectable clock tests.
- Run live HTTP smoke tests and inspect responsive screens at 375/768/1280.
- Add browser screenshots if Playwright becomes available; otherwise document no browser automation.

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

## Does the latest build and test run pass?
Yes for the current checkpoint: `alembic upgrade head`, `python -m app.scripts.reset_db`, backend `pytest -q` (8 passed), frontend `npm test` (2 passed), frontend `npm run build` (passed), and live HTTP smoke passed.

## Suggested push plan
- Phase 1: push the three documentation commits together.
- Later phases: keep local; push only after review in sensible feature batches.
- Current local batch: `79ad1db`, `0c6ebf6`, `3c28e40`, `70165fa`, plus current uncommitted Phase 6 polish; push after review.
