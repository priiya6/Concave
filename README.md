# 1. Project Overview

Concave Insights Support is a local member support-query ticketing system.
Members raise and track requests while agents manage a shared support queue.
Support Heads monitor TAT, escalations, settings, and resolution performance.
It runs locally with SQLite and has no paid services or API keys.

# 2. Tech Stack

Python 3.14.2, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, signed HMAC bearer tokens, SQLite, pytest/httpx; React 18, TypeScript, Vite, responsive CSS, and Vitest.

# 3. Setup and Run

See [RUN_PROJECT.md](RUN_PROJECT.md) for the tested Windows PowerShell walkthrough. Create `.venv`, install `backend/requirements-dev.txt`, copy `.env.example`, run `alembic upgrade head` and `python -m app.scripts.seed` from `backend`, then run `uvicorn app.main:app --reload --port 8000`. In a second terminal run `npm install` and `npm run dev` from `frontend`.

# 4. Demo Logins and Test Data

Head: `head@concave.test` / `Head@123`; agents: `agent1@concave.test` and `agent2@concave.test` / `Agent@123`; members `member1@concave.test` through `member4@concave.test` / `Member@123`. `python -m app.scripts.seed --reset` creates 7 users, 10 representative tickets covering every status/category/priority, 2 internal tickets, 6 saved replies, notifications, TAT targets, and lifecycle settings. SQLite data is local and gitignored.

# 5. Features

| Feature | Status |
|---|---|
| Mocked role login and permissions | Done |
| Member create/list/detail/messages/confirm/reopen | Done |
| Category default priority and TAT fields | Done |
| Agent list/search/filter/assign/unassign/reply/request-info/priority/resolve | Done |
| Head dashboard, escalations, notifications, settings, escalation job | Done (local UI/API) |
| Optimistic version checks and audit events | Done |
| Internal tickets, saved replies, auto-close, history log | Done (local UI/API; browser verification still pending) |
| Responsive member/staff shell, mobile navigation, ticket detail, queue filters, Head settings | Done (browser screenshots still pending) |

# 6. Database Design

The schema contains users, TAT targets, app settings, tickets, messages, ticket events, notifications, internal tickets, and saved replies. Users own tickets and messages; tickets own messages, events, notifications, and internal work; TAT targets define ticket priority deadlines. See the frozen [database ERD](design/database-erd.md). `alembic upgrade head` recreates all ten application tables from a fresh SQLite database.

# 7. API Endpoints

| Method | URL | Purpose |
|---|---|---|
| POST | `/api/auth/login` | Mock login and signed bearer token |
| GET | `/api/auth/me` | Reload current authenticated user |
| GET | `/api/users/staff` | List active staff for assignment |
| POST/GET | `/api/tickets` | Create a member ticket or list role-scoped tickets |
| GET | `/api/tickets/{no}` | Ticket detail, conversation, TAT, history, and reopen policy |
| POST | `/api/tickets/{no}/messages` | Member/agent reply and request-information pause |
| POST | `/api/tickets/{no}/assign` | Assign or unassign staff |
| POST | `/api/tickets/{no}/priority` | Change priority with a mandatory reason |
| POST | `/api/tickets/{no}/resolve` | Resolve a ticket |
| POST | `/api/tickets/{no}/confirm` / `reopen` | Member closure or policy-controlled reopening |
| GET | `/api/dashboard/summary` | Head performance metrics |
| GET | `/api/dashboard/member` | Member status counts and awaiting confirmation |
| GET/PUT | `/api/admin/settings` | Read/update TAT and lifecycle settings |
| POST | `/api/admin/jobs/run` | Run escalation and auto-close checks |
| POST | `/api/tickets/{no}/internal-tickets` | Create linked internal work |
| GET | `/api/internal-tickets` | Staff internal-ticket list |
| POST | `/api/internal-tickets/{id}/complete` | Complete linked internal work |
| GET/POST/DELETE | `/api/saved-replies[/{id}]` | List, create and deactivate saved replies |
| GET/POST | `/api/notifications[/{id}/read]` | List notifications and mark one read |

Ticket list filters include `status`, `category`, `priority`, `overdue=true`, `assignee=me|unassigned|<id>`, and `q` for ticket/member search.

Representative request/response examples captured from the local API:

```text
POST /api/auth/login
{"email":"member1@concave.test","password":"Member@123"}
→ 200 {"access_token":"<signed-token>","token_type":"bearer","user":{"role":"member",...}}

POST /api/tickets
{"category":"payment","subject":"Payment missing","description":"My completed study payment is missing."}
→ 201 {"ticket_number":"TKT-0001","priority":"high","status":"open","version":1,"messages":[],"tat":{"state":"running",...}}

GET /api/tickets?q=TKT-0001&overdue=true&assignee=unassigned
→ 200 {"items":[...],"total":1,"page":1,"page_size":20}

GET /api/tickets/TKT-0001
→ 200 {"ticket_number":"TKT-0001","messages":[...],"events":[...],"can_reopen":false,...}

GET /api/auth/me or GET /api/users/staff or GET /api/dashboard/member
→ 200 {"id":1,"role":"head",...} / {"items":[...]} / {"counts":{...},"awaiting_confirmation":[...]}

POST /api/tickets/TKT-0001/messages
{"body":"Please share the payment reference.","request_info":true,"expected_version":1}
→ 200 {"status":"in_progress","waiting_for_member":true,"version":2,...}

POST /api/tickets/TKT-0001/assign
{"assignee_id":2,"expected_version":2}
→ 200 {"assignee":{"id":2,...},"version":3,...}

POST /api/tickets/TKT-0001/priority
{"priority":"medium","reason":"Evidence is now available.","expected_version":3}
→ 200 {"priority":"medium","version":4,...}

POST /api/tickets/TKT-0001/resolve or /confirm or /reopen
{"expected_version":4} or {"reason":"The issue is still unresolved.","expected_version":4}
→ 200 {"status":"resolved|closed|reopened","version":5,...}

GET /api/dashboard/summary
→ 200 {"open":2,"overdue":1,"escalated":1,"resolved_today":0,"avg_resolution_seconds":...,"avg_wall_clock_resolution_seconds":...,"by_category":[...]}

GET /api/admin/settings
→ 200 {"tat_minutes":{"high":240,"medium":1440,"low":2880},"reopen_window_days":3,"max_reopens":2,"auto_close_days":7}
PUT /api/admin/settings
{"tat_minutes":{"high":1,"medium":1440,"low":2880},"reopen_window_days":3,"max_reopens":2,"auto_close_days":7}
→ 200 {"tat_minutes":{...},"reopen_window_days":3,...}

POST /api/admin/jobs/run
{}
→ 200 {"escalated":1,"auto_closed":0}

GET /api/notifications or POST /api/notifications/{id}/read
→ 200 {"items":[{"ticket_id":4,"message":"...","is_read":false,...}],"unread_count":1} or {"ok":true}

POST /api/tickets/TKT-0001/internal-tickets
{"team":"finance","title":"Verify ledger","description":"Confirm the finance record.","expected_version":5}
→ 201 {"internal_number":"INT-0001","status":"open",...}

GET /api/internal-tickets or POST /api/internal-tickets/1/complete
→ 200 {"items":[...]} or {"ok":true,"status":"done"}

GET /api/saved-replies or POST /api/saved-replies or DELETE /api/saved-replies/{id}
→ 200 {"items":[{"title":"Payment acknowledgement","body":"..."}]} / 201 {"id":7,...} / 200 {"ok":true}
```

# 8. Assumptions and Decisions

TAT is continuous 24×7, including nights and weekends. Waiting for member pauses active TAT through a flag and resumes when the member replies; it is not a seventh status. Category defaults are Payment→High, Eligibility/Survey Issue→Medium, Profile Change/Other→Low because payment is trust-critical and study questions are time-bound. Reopen is only from Resolved, requires a reason, respects the configured window/attempts, and starts a fresh TAT cycle. TAT targets apply live; escalation leaves only by Resolve; any agent may act on any ticket; messages are a flat chronological thread. Dashboard open means open/in-progress/reopened/escalated; overdue means due time passed or escalated; resolution averages exclude waiting time. `Asia/Kolkata` is the default application timezone while storage is UTC. Authentication is a 12-hour HMAC-SHA256 signed mock token and every request reloads the user. Internal work is simulated by staff in the local demo.

# 9. Known Issues and Next Steps

The implementation is locally runnable and the core workflow plus four bonus UI/API surfaces are covered by focused tests. A complete route-level test matrix and browser screenshots were not captured because no browser runtime was available. Mermaid CLI was unavailable because npm was cache-only; no walkthrough video or assessment emails are included.
