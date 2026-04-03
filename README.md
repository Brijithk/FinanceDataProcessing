# Finance Dashboard API

Backend service for a finance dashboard: **users and roles**, **financial entries**, **aggregated summaries**, and **role-based access control**. Built as a small, readable [FastAPI](https://fastapi.tiangolo.com/) application with **async SQLAlchemy 2** and **SQLite** (file `finance.db` in the project root by default).

Interactive API docs are served at **`/docs`** (Swagger UI) and **`/redoc`**.

## Stack

- Python 3.11+ (tested on 3.14)
- FastAPI, Uvicorn
- SQLAlchemy 2 (async), aiosqlite
- JWT bearer authentication (`Authorization: Bearer <token>`)
- bcrypt for password hashes

## Assumptions

- **Roles** (enum `viewer` | `analyst` | `admin`):
  - **Viewer**: may call **dashboard** endpoints (`/api/v1/dashboard/*`) only. Cannot list or mutate raw financial records.
  - **Analyst**: may **read** financial records (`GET /api/v1/records`, `GET /api/v1/records/{id}`) and use the dashboard. Cannot create, update, or delete records or manage users.
  - **Admin**: full **CRUD** on records, **user management**, and dashboard access.
- **Bootstrap admin**: on first startup, if the database has no users, an admin account is created (see below). This keeps local evaluation simple without a separate migration seed step.
- **Persistence**: SQLite file database; suitable for development and demos. Swap `DATABASE_URL` in `.env` for another SQLAlchemy URL if you move to Postgres, etc.
- **Soft delete**: `DELETE /api/v1/records/{id}` sets `deleted_at`; aggregates and listings ignore soft-deleted rows.

## Setup

```powershell
cd "d:\Finance Data Processing and Access Control Backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Optional environment variables (see `app/config.py`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | dev placeholder | JWT signing secret |
| `DATABASE_URL` | `sqlite+aiosqlite:///./finance.db` | SQLAlchemy async URL |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT lifetime |

Create a `.env` file in the project root to override these.

## Run

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: `GET http://localhost:8000/health`
- OpenAPI: `http://localhost:8000/docs`

## Default admin (after first boot)

If the database was empty on startup:

- **Email:** `admin@example.com`
- **Password:** `admin123`

Change this account in production or delete `finance.db` and rely on your own user-creation flow.

## API overview

| Area | Method | Path | Roles |
|------|--------|------|--------|
| Auth | POST | `/api/v1/auth/login` | Public (returns JWT) |
| Auth | GET | `/api/v1/auth/me` | Any authenticated user |
| Users | GET/POST | `/api/v1/users` | Admin |
| Users | PATCH | `/api/v1/users/{id}` | Admin |
| Records | GET | `/api/v1/records` | Analyst, Admin (filters: `from_date`, `to_date`, `category`, `entry_type`, pagination) |
| Records | POST | `/api/v1/records` | Admin |
| Records | GET | `/api/v1/records/{id}` | Analyst, Admin |
| Records | PATCH | `/api/v1/records/{id}` | Admin |
| Records | DELETE | `/api/v1/records/{id}` | Admin (soft delete) |
| Dashboard | GET | `/api/v1/dashboard/summary` | All authenticated roles |

**Dashboard summary** includes: total income, total expenses, net balance, category totals (by type), recent activity, and monthly trends (up to `trend_months`, default 12).

## Example: login and create a record

```powershell
$body = @{ email = "admin@example.com"; password = "admin123" } | ConvertTo-Json
$r = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/auth/login" -Body $body -ContentType "application/json"
$token = $r.access_token
$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/v1/dashboard/summary" -Headers $headers
```

## Tradeoffs

- **SQLite + single file**: easy to ship and review; not ideal for high concurrent write loads.
- **JWT in `Authorization` header**: stateless and simple; no refresh-token rotation (acceptable for this assessment scope).
- **Direct bcrypt** instead of passlib: avoids compatibility issues between passlib and newer bcrypt releases on bleeding-edge Python versions.

## Python 3.14 note

Pinned `pydantic>=2.12` so `pydantic-core` installs from wheels (older pins may try to compile from source). If you use an older Python, the same `requirements.txt` should still resolve.
