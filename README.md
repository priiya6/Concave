# 1. Project Overview

Concave Insights Support is a local member support-query ticketing system.
Members raise and track requests while agents manage a shared support queue.
Support Heads monitor TAT, escalations, settings, and resolution performance.
It runs locally with SQLite and has no paid services or API keys.

# 2. Tech Stack

Python 3.14.2, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, signed HMAC bearer tokens, SQLite, pytest/httpx; React 18, TypeScript, Vite, responsive CSS, and Vitest.

# 3. Setup and Run

Prerequisites: Git, Python 3.11+ (tested with Python 3.14.2), and Node.js 20 LTS+ (tested with Node 22.18.0). From a fresh clone, open PowerShell at the repository root and run:

```powershell
cd backend
python -m venv ..\.venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
..\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
alembic upgrade head
python -m app.scripts.seed --reset
uvicorn app.main:app --reload --port 8000
```

The backend runs at `http://127.0.0.1:8000` and its API documentation is at `/docs`. Leave that terminal running. In a second PowerShell terminal, from the same repository root, run:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The copied backend `.env` uses a local SQLite database and a development-only signing key; it contains no secret that should be reused outside local assessment.

# 4. Demo Logins and Test Data

Head: `head@concave.test` / `Head@123`; agents: `agent1@concave.test` and `agent2@concave.test` / `Agent@123`; members `member1@concave.test` through `member4@concave.test` / `Member@123`. `python -m app.scripts.seed --reset` creates 7 users, 10 representative tickets covering every status/category/priority, 2 internal tickets, 6 saved replies, notifications, TAT targets, and lifecycle settings. SQLite data is local and gitignored.

# 5. Features

| Feature | Status |
|---|---|
| Mocked role login and permissions | Done |
| Member create/list/detail/messages/confirm/reopen | Done |
| Category default priority and TAT fields | Done |
| Agent list/search/filter/assign/unassign/reply/request-information/priority/resolve | Done |
| Head dashboard, escalations, notifications, settings, and escalation job | Done |
| Optimistic version checks and audit events | Done |
| Internal tickets, saved replies, auto-close, and history log | Done |
| Responsive member/staff shell, mobile navigation, ticket detail, queue filters, and Head settings | Done |
| Automated browser end-to-end coverage | Done |
| Email, file attachments, and production deployment | Future scope |

# 6. Database Design

The schema contains 9 application tables: users, TAT targets, app settings, tickets, ticket messages, ticket events, notifications, internal tickets, and saved replies. Users own tickets and messages; tickets own messages, events, notifications, and internal work; TAT targets define ticket priority deadlines. See the frozen [database ERD](design/database-erd.md). `alembic upgrade head` creates all 9 application tables in a fresh SQLite database.

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

Working hours: the four-hour High-priority TAT runs continuously. A ticket created at 11 pm on Saturday therefore uses the night and weekend hours; the demo does not apply a business-hours calendar. This keeps the rule predictable and matches the implemented timer and escalation job.

Waiting for the member: when Support requests information, the ticket is marked `waiting_for_member` and active TAT is paused. If the member replies two days later, those two days are excluded and the clock resumes with the remaining time. The waiting flag is stored separately from the public ticket status so the queue can still show the conversation clearly.

Other decisions are deliberately small: category defaults are Payment → High, Eligibility/Survey Issue → Medium, and Profile Change/Other → Low; changing priority requires a reason; reopening is limited by the configured window and attempts and starts a fresh TAT cycle; resolution averages exclude member-waiting time. Timestamps are stored in UTC and displayed using the configured `Asia/Kolkata` timezone. Authentication is a 12-hour HMAC-SHA256 mock token for this local assessment, not a production identity system.

# 9. Known Issues and Next Steps

The local backend tests and frontend component/build checks pass, and the documented seeded workflow is available. Browser verification is still a manual checklist rather than automated end-to-end coverage. The application also intentionally uses SQLite, mock credentials, HMAC bearer tokens, and local polling; it is not production-ready authentication, deployment, or notification infrastructure.

With more development time, the next useful steps would be:

- Add Playwright coverage for the three role journeys and mobile layouts.
- Replace mock authentication with the deployment identity provider and secure secret management.
- Add file attachments, email/in-app delivery, and a production database migration/deployment path.
- Add server-side pagination and stronger observability around background escalation jobs.
