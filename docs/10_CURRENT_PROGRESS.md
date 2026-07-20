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
**Current phase:** Phase 6 — UI and demo experience (backend fully working: auth, RBAC, private SQL, ingestion, retrieval, chat orchestration; 61 tests passing)  
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
| Sample documents prepared | ✅ | 12 seeded metadata rows (handbook, policies, notices, AGM minutes) |
| Upload flow | ✅ | `POST /admin/documents/upload` (admin-only; .pdf/.txt/.md; creates document + pending ingestion job; files stored in `data/uploads/`) |
| Document list/delete | ✅ | `GET /admin/documents`, `DELETE /admin/documents/{id}` |
| Ingestion job tracking | ✅ | `ingestion_jobs` table + `GET /admin/ingestion-jobs` |
| Audit log viewing | ✅ | `GET /admin/audit-logs` (admin-only) |
| Text extraction | ✅ | `app/ingestion/extractor.py` — .txt/.md direct read, .pdf via pypdf, plus conservative cleaner |
| Chunking logic | ✅ | `app/ingestion/chunker.py` — ~600-token chunks, ~80-token overlap, paragraph/sentence boundary aware |
| Embedding/indexing | ✅ | Chroma persistent store (`data/chroma/`) with default ONNX all-MiniLM-L6-v2; per-chunk metadata (document_id, title, type, issue_date, chunk_index) |
| Vector retrieval | ✅ | `app/retrieval/vector_store.py` (add/delete/count/reset) + `app/retrieval/search.py` (top-k semantic search, distance-threshold weak-retrieval filter) |
| Ingestion pipeline | ✅ | `app/ingestion/pipeline.py` — full job lifecycle pending→processing→completed/failed, audit-logged, idempotent re-ingest |
| Ingest trigger | ✅ | `POST /admin/documents/ingest` processes all pending jobs |
| Sample docs corpus | ✅ | 12 markdown docs in `data/sample_docs/` (generated by `scripts/generate_sample_docs.py`); all ingested |
| Real docs corpus | ✅ | Maharashtra Co-operative Societies Act, 1960 (147-page PDF) registered as policy doc + ingested via `scripts/ingest_real_docs.py`; store holds 422 chunks across 13 documents |
| Re-ingestion script | ✅ | `scripts/ingest_docs.py` — creates missing jobs + processes them, safe to re-run |

### Phase 5 — Chat and orchestration

| Area | Status | Notes |
|---|---|---|
| Query router | ✅ | `app/chat/router.py` — deterministic rule-based classify → public/private/hybrid/refused BEFORE any data access or LLM call |
| Public answer flow | ✅ | `app/chat/orchestrator.py` + `composer.py` — retrieval-grounded answers with safe fallback on weak/empty retrieval |
| Private SQL answer flow | ✅ | `app/chat/private_context.py` — scoped summary from `me_service` (dues + fines); never guesses missing records |
| Hybrid answer flow | ✅ | SQL summary + retrieved policy chunks, clearly separated ("Your account:" / "Society rule:") |
| Refusal handling | ✅ | Deterministic refusal for other-resident/flat references + login-required refusal for anonymous private queries; audit-logged |
| Citation formatting | ✅ | Document-backed answers return `{document_id, title, document_type, issue_date}`; SQL answers never get fake citations |
| Chat endpoint | ✅ | `POST /chat/query` (`app/api/chat_routes.py`) — auth optional for public, required for private/hybrid |
| Answer composition | ✅ | Deterministic composer (no external LLM needed for MVP); prompt templates in `app/prompts/templates.py` ready for LLM plug-in |

### Phase 6 — UI and demo experience

| Area | Status | Notes |
|---|---|---|
| Login page | ✅ | `demo-login.html` (static HTML + fetch, no build step) — sign in with any seeded account, view `/auth/me` |
| Chat interface | ✅ | Chat panel in `demo-login.html` — route badges (public/private/hybrid/refused), citation chips, typing state, suggestion chips for all 4 routes, works anonymously for public questions |
| Resident payment/fine summary view | ✅ | Auto-loads after resident login — outstanding dues + unpaid fines totals with item lists from `/me/dues` + `/me/fines` |
| Admin upload page | ⬜ | Not started (admin API documented in `ADMIN.md`; curl/PowerShell flow works) |
| Error/refusal states | ✅ | Refused answers render in red with `refused` badge; login/401/403 errors shown clearly; backend-down note in chat |
| User guide | ✅ | `USER.md` in repo root — credentials, login flow, curl examples, role permissions, troubleshooting |
| Admin guide | ✅ | `ADMIN.md` in repo root — admin login, all `/admin/*` endpoints with PowerShell/curl examples, permissions, errors, demo script |

### Phase 7 — Quality, security, and polish

| Area | Status | Notes |
|---|---|---|
| Auth tests | ✅ | `backend/tests/test_auth.py` — 10 passing |
| Smoke tests | ✅ | `backend/tests/test_smoke.py` — 2 passing (`/health`, `/health/db`) |
| RBAC tests | ✅ | `require_role` + 401/403 coverage in `test_admin.py` (resident blocked from all `/admin/*`) |
| Retrieval tests | ✅ | `test_ingestion.py` — extraction, chunking bounds, job lifecycle, admin guard, end-to-end upload→ingest→store (11 tests) |
| Chat tests | ✅ | `test_chat.py` — 18 tests: router unit cases, public+citations, anonymous public, private scoping/isolation, hybrid, all spec refusal examples, refusal audit entries |
| Refusal tests | ✅ | Covered in `test_chat.py` (neighbor dues, specific flat fine, other-resident payments, unauthenticated private) |
| Eval harness | ✅ | `data/eval_queries/eval_queries.jsonl` (73 cases: 23 public incl. 3 Act-based / 20 private / 20 unauthorized / 10 hybrid) + `scripts/run_eval.py` — scores routing, citations, refusals, leakage, content; 73/73 passing |
| Retrieval quality fixes | ✅ | Section-aware chunking (64 topical chunks, was 12 diluted); `delete_document` now removes embeddings; tests clean up their uploads (store stays hermetic); distance threshold re-measured |
| Audit logging | ✅ | Login/register/me + `query_private`/`query_public` + `access_denied` + `upload_document`/`delete_document`/`ingest_trigger`/`ingestion_job` events all logged |
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
7. ✅ Add document metadata + ingestion pipeline (extract → clean → chunk → embed → Chroma; 12 sample docs ingested)
8. ✅ Add vector retrieval and chat routing (`POST /chat/query` — public/private/hybrid/refused, citations, audit logging; 61 tests passing)
9. ✅ Build chat UI (extended `demo-login.html` — chat panel with route badges, citations, refusal states, suggestion chips, resident account summary)
10. ✅ Add evaluation harness (`data/eval_queries/` + `scripts/run_eval.py` — 73/73 passing; drove real fixes: section-aware chunking, orphan-embedding deletion, test-store hermeticity, threshold tuning)
11. ✅ Ingest real corpus (Maharashtra Co-operative Societies Act, 1960 — 358 chunks; eval expanded with Act-based cases)
12. ⬜ Optional: plug an OpenAI-compatible LLM behind `app/chat/composer.py` (prompt templates already in `app/prompts/templates.py`)
13. ⬜ Optional: admin upload page (API works; UI would extend `demo-login.html`)
14. ⬜ Deployment prep + demo assets (screenshots, demo script)

---

## What a coding agent should do next

If a coding agent starts from this repo now, the next action should be:

### First task
The MVP core is complete end-to-end (auth → RBAC → private SQL → ingestion → retrieval → chat → demo UI, 61 tests passing). Remaining work is polish, not function.

### Second task
Optionally plug in a real LLM behind the composer layer for more natural phrasing. Not required for MVP — the deterministic composer is grounded by construction and cannot hallucinate account data.

### Third task
Deployment prep and demo assets (Phase 7 leftovers + Phase 3 polish): Docker/local run scripts, screenshots, short demo notes, optional admin upload page.

---

## Update rule

Update this file whenever:

- a new major doc is added
- a new module is implemented
- a major bug blocks progress
- a phase changes from not started to in progress or done

Keep updates short, factual, and current.
