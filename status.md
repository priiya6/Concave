# Concave Insights checkpoint

## Current status & phase
Final completion phase: mandatory workflows and all four bonus UI/API workflows implemented; automated verification passed; browser runtime unavailable.

## Completed tasks
- Preserved the frozen Day 2 design files and incremental Git history.
- Verified member, agent, and Support Head workflows, TAT, waiting pause/resume, escalation, notifications, settings, and dashboard APIs.
- Added staff assignment/priority/resolve controls and ticket-detail internal work, history, and member-safe internal status panels.
- Added agent saved-reply insertion with editable composer and Head saved-reply create/deactivate management.
- Added auto-close configuration and run-check behavior already present in the Head settings UI.
- Added backend visibility coverage and frontend interaction tests for the bonus panels.

## Pending tasks
- Actual browser/responsive execution and screenshots remain unavailable because no browser executable or Playwright package is installed.
- Full route-level frontend coverage remains larger than the focused component/interaction suite.

## Architecture & key decisions
- Python/FastAPI + SQLAlchemy/Alembic backend; React/TypeScript/Vite frontend.
- SQLite local database; UTC timestamps; continuous 24x7 TAT; waiting is a flag, not a status.
- Frozen design files are not edited after Phase 1; divergences use `*-v2.md`.

## Files created/modified
- Backend: `app/main.py`, `tests/test_api.py`.
- Frontend: `src/components.tsx`, `src/components.test.tsx`, `src/main.tsx`, `src/style.css`.
- Documentation: `README.md`, `RUN_PROJECT.md`, `status.md`.

## Database & migration status
PASS: downgrade-to-base, upgrade-to-head, reset/seed, and ten-table inspection completed. Internal ticket detail serialization exposes only team/status/title metadata to members; staff receive full internal fields.

## API implementation status
- PASS: auth, permissions, ticket lifecycle, assignment/unassignment, priority reasons, TAT, escalation, notifications, dashboard, settings/jobs, internal tickets, saved replies, auto-close, validation, and error envelopes.

## Frontend implementation status
- PASS: member confirmation/reopen, staff actions, Head dashboard/escalations/settings, saved-reply editor/admin, internal-ticket create/complete panel, history panel, member-safe internal status, loading/empty/error states, and responsive CSS.
- Route-level browser automation remains unverified.

## Test results
Backend: 9 passed sequentially. Frontend: 6 passed. Production build passed. Migration downgrade/upgrade and reset/seed passed. Live HTTP smoke passed for `/api/health`, Head login, and dashboard summary. A parallel test/migration attempt was correctly rerun sequentially after a SQLite seed race.

## Known bugs & resolved issues
- Fixed missing internal ticket data in ticket detail responses and protected internal descriptions from member responses.
- Fixed callback typing and test-environment issues in the new panels.
- Windows pytest cache permission warnings remain environmental only; tests pass.
- Browser and Mermaid rendering verification were unavailable and are not claimed.

## Exact next steps
- Run the manual browser checklist in `RUN_PROJECT.md` at 375px, 768px, and 1280px.
- If a browser becomes available, capture screenshots and check horizontal overflow, dialogs, navigation, and all three roles.
- Re-run the documented clean setup before assessment submission.

## Git commits
- Existing history through `60e6ed1` is pushed.
- `8920a96` feat: add bonus workflow panels (pushed)
- `c91481e` feat: improve responsive bonus panels (pushed)
- `dbe8b20` test: expand bonus workflow coverage (pushed)
- `83666a3` docs: record bonus completion and verification (pushed)

## Does the latest build and test run pass?
Yes: backend 9 tests, frontend 6 tests, frontend production build, migration/reset/seed, and live HTTP smoke pass. Browser verification is not available.

## Suggested push plan
- `8920a96`, `c91481e`, `dbe8b20`, and `83666a3` are pushed to `origin/main`.
