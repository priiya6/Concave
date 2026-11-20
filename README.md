# 1. Project Overview

Concave Insights Support is a local member support-query ticketing system. Members raise and track requests; agents manage a queue; Support Heads monitor TAT and escalation. It runs locally with SQLite and has no paid services or API keys.

# 2. Tech Stack

Python 3.14.2, FastAPI, SQLAlchemy 2, Alembic-compatible metadata, Pydantic v2, signed HMAC bearer tokens, SQLite, pytest/httpx; React 18, TypeScript, Vite, responsive CSS, and Vitest.

# 3. Setup and Run

See [RUN_PROJECT.md](RUN_PROJECT.md) for the tested Windows PowerShell walkthrough. Create `.venv`, install `backend/requirements-dev.txt`, copy `.env.example`, run `alembic upgrade head` and `python -m app.scripts.seed` from `backend`, then run `uvicorn app.main:app --reload --port 8000`. In a second terminal run `npm install` and `npm run dev` from `frontend`.

# 4. Demo Logins and Test Data

Head: `head@concave.test` / `Head@123`; agents: `agent1@concave.test` and `agent2@concave.test` / `Agent@123`; members `member1@concave.test` through `member4@concave.test` / `Member@123`. `python -m app.scripts.seed --reset` creates the user/settings baseline. SQLite data is local and gitignored.

# 5. Features

| Feature | Status |
|---|---|
| Mocked role login and permissions | Done |
| Member create/list/detail/messages/confirm/reopen | Done |
| Category default priority and TAT fields | Done |
| Agent list/search/filter/assign/reply/request-info/priority/resolve | Partly done |
| Head dashboard, notifications, settings, escalation job | Partly done |
| Optimistic version checks and audit events | Partly done |
| Internal tickets, saved replies, auto-close | Not done |
| Responsive member/staff shell | Partly done |

# 6. Database Design

The planned schema covers users, TAT targets, settings, tickets, messages, events, notifications, internal tickets, and saved replies. See the frozen [database ERD](design/database-erd.md). The running initial implementation creates the core operational tables from SQLAlchemy metadata.

# 7. API Endpoints

Implemented endpoints include `POST /api/auth/login`, `GET /api/auth/me`, `POST/GET /api/tickets`, `GET /api/tickets/{no}`, message/assign/priority/resolve/confirm/reopen actions, `GET /api/users/staff`, member/head dashboards, notifications, `GET/PUT /api/admin/settings`, and `POST /api/admin/jobs/run`. Example: `POST /api/tickets` with `{"category":"payment","subject":"Payment missing","description":"My completed study payment is missing."}` returns `201` with a ticket such as `{"ticket_number":"TKT-0001","priority":"high","status":"open"}`.

# 8. Assumptions and Decisions

TAT is continuous 24×7, including nights and weekends. Waiting for member pauses active TAT through a flag and resumes when the member replies; it is not a seventh status. Category defaults are Payment→High, Eligibility/Survey Issue→Medium, Profile Change/Other→Low because payment is trust-critical and study questions are time-bound. Reopen is only from Resolved, requires a reason, respects the configured window/attempts, and starts a fresh TAT cycle. TAT targets apply live; escalation leaves only by Resolve; any agent may act on any ticket; messages are a flat chronological thread. Dashboard open means open/in-progress/reopened/escalated; overdue means due time passed or escalated; resolution averages exclude waiting time. `Asia/Kolkata` is the default application timezone while storage is UTC. Authentication is a 12-hour HMAC-SHA256 signed mock token and every request reloads the user. Internal work is simulated by staff in the local demo.

# 9. Known Issues and Next Steps

The current checkpoint is a functional core and responsive shell, not the complete assessment scope: richer queue/detail pages, background loop, full migration script, bonus features, visual test suite, and seeded scenario matrix remain. Mermaid CLI could not be downloaded in the sandbox because npm was cache-only; the source was manually checked. Later work should add the remaining service-layer tests, full UI routes/components, and a fresh-clone/live HTTP walkthrough. No walkthrough video or assessment emails are included.
