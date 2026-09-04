# AI-Powered Border Checkpoint & Travel Document Verification Platform

## 1. What this is

A student-built (SIH 2026) platform assisting immigration/security officers in verifying
travel documents. **This repository contains Phase 1 only**: authentication, RBAC, users,
and checkpoints. AI modules (OCR, MRZ, face verification, tamper detection, risk scoring)
are added in later phases by other developers on the team, on top of this foundation.

## 2. Architecture

Modular monolith. Frontend (Next.js) and backend (FastAPI) are fully separate processes
communicating over REST. See `/docs/architecture.md` for the full system architecture
document, which is the source of truth for the whole project — this README only covers
the Phase 1 slice.

## 3. Folder structure

```
border-verification/
├── frontend/       Next.js 15 App Router application
├── backend/        FastAPI application (app/, alembic/, tests/)
├── docs/           Full architecture documentation
├── docker-compose.yml
└── README.md
```

Backend internals:
```
backend/app/
├── api/v1/        Route handlers only — no business logic here
├── core/          config, security, logging, exceptions
├── db/            SQLAlchemy engine/session, declarative base
├── models/        ORM models (one file per entity)
├── schemas/       Pydantic request/response schemas
├── services/      Business logic (called by routes)
├── repositories/  Database queries (called by services)
```

Frontend internals:
```
frontend/
├── app/                 pages (App Router): login, dashboard, verification, checkpoints, users, settings
├── components/ui/       generic UI primitives (Button, Card)
├── components/layout/   Sidebar, Header, PlaceholderScreen
├── services/            API client layer (api.ts, auth.ts, users.ts, checkpoints.ts)
├── hooks/                useAuth
├── lib/                  token storage helper
├── types/                shared TypeScript types
```

## 4. Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16 (or Docker Desktop, if using the Docker option)

## 5. Installation — Option A: Local development (Windows)

### Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend\.env` and set `DATABASE_URL` to your local PostgreSQL connection string,
and set `JWT_SECRET` to any long random string.

```powershell
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### Frontend

Open a new terminal:

```powershell
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Frontend runs at `http://localhost:3000`.

## 5b. Installation — Option B: Docker

```powershell
docker compose up --build
```

This starts PostgreSQL, backend, and frontend together. After the containers are up, run
migrations and seed data once:

```powershell
docker compose exec backend alembic upgrade head
docker compose exec backend python seed.py
```

## 6. Environment variables

**Backend (`backend/.env`)**

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET` | Secret used to sign JWTs — never commit a real value |
| `JWT_ALGORITHM` | Defaults to `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins |

**Frontend (`frontend/.env.local`)**

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_API_URL` | Base URL of the backend API, e.g. `http://localhost:8000/api/v1` |

## 7. Database setup & migrations

Migrations are managed with Alembic. After changing a model in `backend/app/models/`,
generate a new migration:

```powershell
cd backend
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

## 8. Test accounts

Created by `python seed.py`:

| Role | Email | Password |
|---|---|---|
| ADMIN | admin@demo.example | Admin@12345 |
| SUPERVISOR | supervisor@demo.example | Supervisor@12345 |
| OFFICER | officer@demo.example | Officer@12345 |

These are synthetic demo accounts only — never use real personal data here.

## 9. How authentication works

1. Frontend posts credentials to `POST /api/v1/auth/login`.
2. Backend verifies the hashed password and issues a signed JWT (role + checkpoint embedded).
3. Frontend stores the token (localStorage + a cookie for middleware route protection) and
   attaches it as a Bearer header on every request.
4. Protected backend routes decode the JWT and re-fetch the live user record from the
   database (so a deactivated account loses access immediately, even with a valid token).
5. Role-restricted routes use the reusable `require_role(...)` FastAPI dependency.

## 10. Running tests

```powershell
cd backend
pytest
```

Covers: health endpoint, registration, login (valid/invalid), the protected `/auth/me`
endpoint, and RBAC (an OFFICER is correctly blocked from an ADMIN-only route).

## 11. How six developers can work on this independently

- **Dev 1 (Backend/DB):** extends `models/`, `schemas/`, `repositories/`, `services/`,
  adds new Alembic migrations. Owns `backend/app/db` and `backend/app/models`.
- **Dev 2 (OCR/MRZ):** adds `backend/app/ai/ocr/` and `backend/app/ai/mrz/`, returning
  results in the `ServiceResult` envelope defined in `app/schemas/common.py`.
- **Dev 3 (Face verification):** adds `backend/app/ai/face/`, same result envelope.
  Must only implement 1:1 verification — no face search/identification endpoint.
- **Dev 4 (Tamper detection):** adds `backend/app/ai/tamper/`, same result envelope.
- **Dev 5 (Frontend):** builds out `frontend/app/verification/`, evidence panels, and
  new components under `frontend/components/`, consuming the same `services/` API layer.
- **Dev 6 (Synthetic DB + risk engine):** adds `backend/app/services/risk_engine.py` and
  seed data for synthetic passports/visas/watchlist entries.

Because routes never contain business logic (it lives in `services/`) and services never
run raw SQL (that lives in `repositories/`), each developer's module stays isolated and
mergeable without touching files owned by someone else.

## 12. API documentation

Interactive Swagger UI: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`
