# Run Concave Insights locally on Windows

## Prerequisites

Install Python 3.11+ (tested with Python 3.14.2) from https://www.python.org/downloads/, Node 20 LTS+ (tested with Node 22.18.0) from https://nodejs.org/, Git from https://git-scm.com/download/win, and VS Code from https://code.visualstudio.com/.

Open the repository in VS Code, then open an integrated PowerShell terminal. From the repository root:

```powershell
cd backend
py -3 -m venv ..\.venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
..\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
alembic upgrade head
python -m app.scripts.seed
uvicorn app.main:app --reload --port 8000
```

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Use http://localhost:5173, API http://127.0.0.1:8000, and API docs at http://127.0.0.1:8000/docs.

Demo accounts: `head@concave.test` / `Head@123`; `agent1@concave.test` / `Agent@123`; `agent2@concave.test` / `Agent@123`; `member1@concave.test` / `Member@123` (members 2–4 use the same password).

## Workflow smoke test

As a member, raise a payment ticket, reply, and confirm a resolved ticket; reopen a recently resolved ticket with a reason. As an agent, filter/search, assign, reply, request information, change priority with a reason, and resolve. As Head, inspect dashboard, configure High to one minute, create a payment ticket, run the escalation check, and inspect the alert. Test reopen limits from the settings. The dashboard shows active, overdue, escalated, resolved, averages, and category counts.

## Tests and common fixes

Run backend tests with `cd backend; pytest`, frontend tests with `cd frontend; npm test`, and the production build with `npm run build`. If PowerShell blocks activation, run the execution-policy command above. If `python` is not found, use `py -3`. Run backend commands from `backend` with the virtual environment active. Install `tzdata` if ZoneInfo fails. Stop both servers with Ctrl+C. Reset the database with `python -m app.scripts.reset_db`. Port conflicts use another terminal only after stopping the old process; proxy/CORS errors mean the backend is not on port 8000. A blank page after login usually means the frontend dev server needs restarting.

