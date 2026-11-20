# Concave Insights checkpoint

## Current status & phase
Phase 1 — frozen design and repository checkpoint complete; committing/pushing now.

## Completed tasks
- Confirmed the remote repository was empty; default branch is `main`.
- Confirmed local tools: Python 3.14.2, Node 22.18.0, npm 11.12.1, Git 2.50.1.
- Added frozen Day 2 flow/ERD design, repository hygiene, handoff, and initial README.
- Mermaid CLI attempt was blocked because npm is offline/cache-only; source blocks were manually checked and will be revalidated when package access is available.

## Pending tasks
- Commit and push the three Phase 1 documentation commits.
- Build backend foundations, frontend shell, workflows, tests, and final documentation.

## Architecture & key decisions
- Python/FastAPI + SQLAlchemy/Alembic backend; React/TypeScript/Vite/Tailwind frontend.
- SQLite local database; UTC timestamps; continuous 24x7 TAT; waiting is a flag, not a status.
- Frozen design files are not edited after Phase 1; divergences use `*-v2.md`.

## Files created/modified
- Root: `.gitignore`, `.gitattributes`, `CODEX_HANDOFF.md`, `status.md`, `README.md`.
- Design: `design/user-flow.md`, `design/database-erd.md`, `design/README.md`.

## Database & migration status
Not started. ERD is the authoritative planned schema.

## API implementation status
No endpoints implemented yet.

## Frontend implementation status
No frontend implemented yet.

## Test results
No application tests yet. Mermaid source blocks are balanced and syntactically conservative; `npx -y @mermaid-js/mermaid-cli` could not run because the npm registry is unavailable in the sandbox (`ENOTCACHED`).

## Known bugs & resolved issues
- Remote clone initially failed in the sandbox; rerun with approved network access succeeded and confirmed the remote is empty.

## Exact next steps
- Render/parse Mermaid diagrams and fix any syntax errors.
- Make the three Phase 1 commits and push `main`.
- Scaffold backend configuration, database, models, migration, auth, and seed.
- Scaffold frontend shell and login.

## Git commits
No commits yet.

## Does the latest build and test run pass?
No application build exists yet.

## Suggested push plan
- Phase 1: push the three documentation commits together.
- Later phases: keep local; push only after review in sensible feature batches.
