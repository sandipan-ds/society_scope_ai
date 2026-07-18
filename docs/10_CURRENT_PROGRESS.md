# 03_CURRENT_PROGRESS.md

## Purpose

This document tracks the current status of the Housing Society AI Assistant project.

It is meant to help:

- coding agents know what is already done
- stakeholders understand current project maturity
- collaborators see what to do next

Status markers used here:

- **✅ Done**
- **🟡 In progress / partially done**
- **⬜ Not started**

---

## Project snapshot

**Project:** Housing Society AI Assistant  
**Type:** Secure Hybrid RAG MVP  
**Current phase:** Documentation-first planning and repo definition  
**Goal:** Build a strong MVP with login, RAG for public documents, SQL for private resident data, and role-based access control.

---

## High-level status

### Phase 0 — Planning and documentation

| Area | Status | Notes |
|---|---|---|
| Project concept defined | ✅ | Secure hybrid RAG assistant for housing society use cases |
| Resume-value direction defined | ✅ | Project aimed at strong MVP quality and recruiter appeal |
| Core repo overview created | ✅ | README created |
| Document index created | ✅ | INDEX created to guide reading order |
| Product requirements written | ✅ | PRD created |
| System architecture written | ✅ | Architecture doc created |
| Database schema written | ✅ | Simplified MVP schema created |
| API + RBAC spec written | ✅ | Endpoint and authorization behavior documented |
| RAG + ingestion spec written | ✅ | Retrieval and ingestion design documented |
| Prompt + guardrails written | ✅ | Grounding, privacy, and refusal rules documented |
| Synthetic data + tests written | ✅ | Demo data and test plan documented |
| Build order written | ✅ | Execution sequence documented |
| Agent operating guide written | ✅ | AGENTS.md created |

### Phase 1 — Backend foundation

| Area | Status | Notes |
|---|---|---|
| Backend repo scaffold | ✅ | `backend/app/{api,auth,chat,config,db,guardrails,ingestion,logging,prompts,retrieval}` + `backend/tests` |
| FastAPI app entrypoint | ✅ | `backend/app/main.py` with `/health` and `/health/db` endpoints |
| Config management | ✅ | `backend/app/config/settings.py` (pydantic-settings, env-driven, anchored at repo root) |
| DB connection setup | ✅ | `backend/app/db/session.py` (SQLAlchemy engine + session factory) |
| Migration setup | ✅ | `scripts/build_database.py` applies `data/schema.sql` idempotently |
| Health endpoint | ✅ | `/health` and `/health/db` verified by `backend/tests/test_smoke.py` (2 passing) |
| Base error handling | ✅ | Validation / SQLAlchemy / generic exception handlers registered in `main.py` |

### Phase 2 — Authentication and authorization

| Area | Status | Notes |
|---|---|---|
| Users model | ✅ | `backend/app/db/models.py::User` with role enum (`resident`/`admin`/`staff`) |
| JWT auth flow | ✅ | `backend/app/auth/jwt.py` (issue/verify); 60-min expiry via env |
| Password hashing | ✅ | `backend/app/auth/passwords.py` (raw `bcrypt`; truncates >72 bytes per spec; DEV placeholder fallback for seeded users) |
| Resident/admin roles | ✅ | `backend/app/auth/dependencies.py::require_role` / `require_admin` / `require_resident` |
| Route protection | ✅ | `get_current_user` dependency + `HTTPBearer` validation on `/auth/me`, `/me/*` |
| Resident scoping rules | ✅ | Service layer (`app/api/me_service.py`) always queries by `current_user.resident_id`; no request-supplied ids |
| Auth routes | ✅ | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` (all audit-logged) |
| Auth tests | ✅ | `backend/tests/test_auth.py` — 10 tests covering register, login success/fail, /me, invalid token, DEV placeholder fallback |
| Resident self-service endpoints | ✅ | `GET /me/profile`, `/me/dues`, `/me/payments`, `/me/fines` — scoped, audit-logged, 12 tests in `test_me.py` |

### Phase 3 — Private data layer

| Area | Status | Notes |
|---|---|---|
| Residents table/model | ✅ | Table created via `data/schema.sql`; seeded with 108 Indian-name residents |
| Monthly charges table/model | ✅ | Row-per-month design; seeded 1,296 rows for FY 2026 (1160 paid / 24 partial / 112 unpaid) |
| Fines table/model | ✅ | Seeded 25 fines across wrong_parking / late_fee / damage / other |
| Documents metadata table/model | ✅ | Seeded 12 documents (handbook, policies, notices, AGM minutes); embeddings remain in vector store |
| Optional audit logs table/model | ✅ | Table created empty (real events populate it later) |
| Seed data script | ✅ | `scripts/seed_data.py` (deterministic, Indian names + realistic phones, 80/20 owner/tenant split) |
| DB build script | ✅ | `scripts/build_database.py` applies schema and runs seed (idempotent; --reset to recreate) |

### Demo credentials (placeholder hashes — replace when auth module is wired)

Admins: `admin1@society.in`, `admin2@society.in`  
Residents: `resident1@society.in` (A-101), `resident2@society.in` (A-202), `resident3@society.in` (A-304), `resident4@society.in` (A-405), `resident5@society.in` (B-101), `resident6@society.in` (B-203), `resident7@society.in` (B-306), `resident8@society.in` (B-404), `resident9@society.in` (A-505), `resident10@society.in` (B-606)  
All seeded users currently store a `DEV_PASSWORD_HASH` placeholder string — the real bcrypt hash will be added by the auth module.

### Phase 4 — RAG and ingestion

| Area | Status | Notes |
|---|---|---|
| Sample documents prepared | ⬜ | Not started |
| Upload flow | ⬜ | Not started |
| Text extraction | ⬜ | Not started |
| Chunking logic | ⬜ | Not started |
| Embedding/indexing | ⬜ | Not started |
| Vector retrieval | ⬜ | Not started |

### Phase 5 — Chat and orchestration

| Area | Status | Notes |
|---|---|---|
| Query router | ⬜ | Not started |
| Public answer flow | ⬜ | Not started |
| Private SQL answer flow | ⬜ | Not started |
| Hybrid answer flow | ⬜ | Not started |
| Refusal handling | ⬜ | Not started |
| Citation formatting | ⬜ | Not started |

### Phase 6 — UI and demo experience

| Area | Status | Notes |
|---|---|---|
| Login page | 🟡 | `demo-login.html` (static HTML + fetch, no build step) — sign in with any seeded account, view `/auth/me` |
| Chat interface | ⬜ | Not started |
| Resident payment/fine summary view | ⬜ | Not started |
| Admin upload page | ⬜ | Not started |
| Error/refusal states | 🟡 | Demo page shows 401/403 errors clearly; chat refusal UI pending |
| User guide | ✅ | `USER.md` in repo root — credentials, login flow, curl examples, role permissions, troubleshooting |

### Phase 7 — Quality, security, and polish

| Area | Status | Notes |
|---|---|---|
| Auth tests | ✅ | `backend/tests/test_auth.py` — 10 passing |
| Smoke tests | ✅ | `backend/tests/test_smoke.py` — 2 passing (`/health`, `/health/db`) |
| RBAC tests | 🟡 | `require_role` exists; `/admin/*` and `/me/*` route tests pending |
| Retrieval tests | ⬜ | Not started |
| Refusal tests | ⬜ | Not started |
| Audit logging | 🟡 | Login/register/me + `query_private` events logged; chat/refusal logging pending |
| Deployment prep | ⬜ | Not started |
| Demo assets/screenshots | ⬜ | Not started |

---

## Current documents available

The following documents are now available in the repo:

1. `README.md`
2. `INDEX.md`
3. `PRD.md`
4. `ARCHITECTURE.md`
5. `DB_SCHEMA.md`
6. `API_RBAC_SPEC.md`
7. `RAG_INGESTION_SPEC.md`
8. `PROMPT_GUARDRAILS.md`
9. `SYNTHETIC_DATA_AND_TESTS.md`
10. `BUILD_ORDER.md`
11. `AGENTS.md`
12. `03_CURRENT_PROGRESS.md`

---

## Important project decisions already made

### 1. The schema has been simplified
The project uses a simpler housing-society-sized database design rather than a large enterprise schema.

### 2. SQL and RAG are separated intentionally
- private resident data stays in SQL
- public notices/policies go through RAG

### 3. Monthly payments are row-based, not column-based
Months like `jan`, `feb`, `mar` are not stored as separate DB columns. Instead, one row is stored per resident per month.

### 4. Security is a core feature
The project must refuse unauthorized access to another resident's private data.

---

## Immediate next steps

### Recommended next implementation order

1. ✅ Create the local repo/folder scaffold
2. ✅ Seed synthetic resident/payment/fine data (108 residents + 12 demo login users)
3. ✅ Create backend FastAPI app structure (foundation complete — config, DB session, ORM models, health endpoints)
4. ✅ Create SQLAlchemy models for the simplified schema (`backend/app/db/models.py`)
5. ✅ Add auth and JWT flow (bcrypt passwords, JWT issue/verify, `/auth/{register,login,me}`, role guards, audit logging)
6. ✅ Add `/me/*` resident endpoints (profile, dues, payments, fines — scoped to authenticated resident)
7. ⬜ Add document metadata + ingestion pipeline
8. ⬜ Add vector retrieval and chat routing

---

## What a coding agent should do next

If a coding agent starts from this repo now, the next action should be:

### First task
Scaffold the project directories and backend foundation according to `README.md`, `ARCHITECTURE.md`, and `BUILD_ORDER.md`.

### Second task
Implement the simplified SQL schema from `DB_SCHEMA.md`.

### Third task
Implement JWT auth and RBAC rules from `API_RBAC_SPEC.md` and `AGENTS.md`.

---

## Update rule

Update this file whenever:

- a new major doc is added
- a new module is implemented
- a major bug blocks progress
- a phase changes from not started to in progress or done

Keep updates short, factual, and current.
