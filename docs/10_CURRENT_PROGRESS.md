# 10_CURRENT_PROGRESS.md

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
**Current phase:** Phase 6 — UI and demo experience (backend fully working: auth, RBAC, Excel workbook data layer, JSON state store, ingestion, retrieval, chat orchestration; 60 tests passing)  
**Goal:** Build a strong MVP with login, RAG for public documents, Excel-backed private resident data, and role-based access control.

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
| Data schema written | ✅ | Simplified MVP schema documented; runtime source is the Excel workbook |
| API + RBAC spec written | ✅ | Endpoint and authorization behavior documented |
| RAG + ingestion spec written | ✅ | Retrieval and ingestion design documented |
| Prompt + guardrails written | ✅ | Grounding, privacy, and refusal rules documented |
| Synthetic data + tests written | ✅ | Demo data and test plan documented |
| Build order written | ✅ | Execution sequence documented |
| Agent operating guide written | ✅ | AGENTS.md created |

### Phase 1 — Backend foundation

| Area | Status | Notes |
|---|---|---|
| Backend repo scaffold | ✅ | `backend/app/{api,auth,chat,config,db,guardrails,ingestion,logging,prompts,retrieval,workbook}` + `backend/tests` |
| FastAPI app entrypoint | ✅ | `backend/app/main.py` with `/health` and `/health/data` endpoints |
| Config management | ✅ | `backend/app/config/settings.py` (pydantic-settings, env-driven, anchored at repo root) |
| Workbook + state store paths | ✅ | `members_data_file` and `app_state_dir` settings added |
| Health endpoint | ✅ | `/health` and `/health/data` verified by `backend/tests/test_smoke.py` (2 passing) |
| Base error handling | ✅ | Validation / generic exception handlers registered in `main.py`; SQLAlchemy handler removed |

### Phase 2 — Authentication and authorization

| Area | Status | Notes |
|---|---|---|
| Users model | 🟡 | `backend/app/db/models.py::User` retained for reference; runtime auth uses `WorkbookUser` + `StateUser` |
| JWT auth flow | ✅ | `backend/app/auth/jwt.py` (issue/verify); 60-min expiry via env |
| Password hashing | ✅ | `backend/app/auth/passwords.py` (raw `bcrypt`; truncates >72 bytes per spec; DEV placeholder fallback) |
| Resident/admin roles | ✅ | `backend/app/auth/dependencies.py::require_role` / `require_admin` / `require_resident` |
| Route protection | ✅ | `get_current_user` dependency + `HTTPBearer` validation on `/auth/me`, `/me/*` |
| Resident scoping rules | ✅ | Service layer (`app/api/me_service.py`) always queries by the authenticated flat number; no request-supplied ids |
| Auth routes | ✅ | `POST /auth/login`, `GET /auth/me` (audit-logged); registration disabled in Excel-only runtime |
| Auth tests | ✅ | `backend/tests/test_auth.py` — 9 tests covering login success/fail, /me, invalid token, DEV placeholder fallback |
| Resident self-service endpoints | ✅ | `GET /me/profile`, `/me/dues`, `/me/payments`, `/me/fines` — scoped, audit-logged, 10 tests in `test_me.py` |

### Phase 3 — Private data layer (Excel workbook)

| Area | Status | Notes |
|---|---|---|
| Workbook data layer | ✅ | `backend/app/workbook/store.py` reads `data/members_data/Housing_Society_Charges_and_Fines_Template_108_Residents.xlsx`; mtime-cached; exposes residents, charges, fines, payments, users |
| Workbook normalization | ✅ | `scripts/normalize_workbook.py` added formula-driven Maintenance Charges and a zero-filled Payments sheet |
| JSON state store | ✅ | `backend/app/statestore.py` manages users, documents, ingestion_jobs, audit_logs in `data/app_state/*.json` |
| Migration script | ✅ | `scripts/migrate_to_statestore.py` one-off migration of admin users, documents, jobs, and audit logs from legacy `database/society.db` |
| Residents | ✅ | 108 flats in workbook (`Residents` sheet) |
| Maintenance charges | ✅ | Base ₹3,500/month, formula-driven total including fines |
| Fines | ✅ | Six fine sheets: parking, waste, pet, noise, property_damage, miscellaneous |
| Payments | ✅ | `Payments` sheet tracks amount paid per month per flat |
| Admin seed users | ✅ | `admin1@society.in`, `admin2@society.in` migrated to `data/app_state/users.json` |

### Phase 4 — RAG and ingestion

| Area | Status | Notes |
|---|---|---|
| Sample documents prepared | ✅ | 12 seeded metadata rows migrated to `data/app_state/documents.json` |
| Upload flow | ✅ | `POST /admin/documents/upload` (admin-only; .pdf/.txt/.md; creates document + pending ingestion job; files stored in `data/uploads/`) |
| Document list/delete | ✅ | `GET /admin/documents`, `DELETE /admin/documents/{id}` |
| Ingestion job tracking | ✅ | `data/app_state/ingestion_jobs.json` + `GET /admin/ingestion-jobs` |
| Audit log viewing | ✅ | `GET /admin/audit-logs` (admin-only) |
| Text extraction | ✅ | `app/ingestion/extractor.py` — .txt/.md direct read, .pdf via pypdf, plus conservative cleaner |
| Chunking logic | ✅ | `app/ingestion/chunker.py` — ~600-token chunks, ~80-token overlap, paragraph/sentence boundary aware |
| Embedding/indexing | ✅ | Chroma persistent store (`data/chroma/`) with default ONNX all-MiniLM-L6-v2; per-chunk metadata (document_id, title, type, issue_date, chunk_index) |
| Vector retrieval | ✅ | `app/retrieval/vector_store.py` (add/delete/count/reset) + `app/retrieval/search.py` (top-k semantic search, distance-threshold weak-retrieval filter) |
| Ingestion pipeline | ✅ | `app/ingestion/pipeline.py` — full job lifecycle pending→processing→completed/failed, audit-logged, idempotent re-ingest |
| Ingest trigger | ✅ | `POST /admin/documents/ingest` processes all pending jobs |
| Sample docs corpus | ✅ | 12 markdown docs in `data/sample_docs/` (generated by `scripts/generate_sample_docs.py`); all ingested |
| Real docs corpus | ✅ | Maharashtra Co-operative Societies Act, 1960 (147-page PDF) registered as policy doc + ingested; store holds 422 chunks across 13 documents |
| Re-ingestion script | ✅ | `scripts/ingest_docs.py` — creates missing jobs + processes them, safe to re-run |

### Phase 5 — Chat and orchestration

| Area | Status | Notes |
|---|---|---|
| Query router | ✅ | `app/chat/router.py` — deterministic rule-based classify → public/private/hybrid/refused BEFORE any data access or LLM call; updated for plain 3-4 digit flat numbers |
| Public answer flow | ✅ | `app/chat/orchestrator.py` + `composer.py` — retrieval-grounded answers with safe fallback on weak/empty retrieval |
| Private answer flow | ✅ | `app/chat/private_context.py` — scoped summary from workbook (dues + fines); never guesses missing records |
| Hybrid answer flow | ✅ | Workbook summary + retrieved policy chunks, clearly separated ("Your account:" / "Society rule:") |
| Refusal handling | ✅ | Deterministic refusal for other-resident/flat references + login-required refusal for anonymous private queries; audit-logged |
| Citation formatting | ✅ | Document-backed answers return `{document_id, title, document_type, issue_date}`; workbook answers never get fake citations |
| Chat endpoint | ✅ | `POST /chat/query` (`app/api/chat_routes.py`) — auth optional for public, required for private/hybrid |
| Answer composition | ✅ | Deterministic composer (no external LLM needed for MVP); prompt templates in `app/prompts/templates.py` ready for LLM plug-in |

### Phase 6 — UI and demo experience

| Area | Status | Notes |
|---|---|---|
| Login page | ✅ | `demo-login.html` (static HTML + fetch, no build step) — sign in with any workbook/admin account, view `/auth/me` |
| Chat interface | ✅ | Chat panel in `demo-login.html` — route badges (public/private/hybrid/refused), citation chips, typing state, suggestion chips for all 4 routes, works anonymously for public questions |
| Resident payment/fine summary view | ✅ | Auto-loads after resident login — outstanding dues + unpaid fines totals with item lists from `/me/dues` + `/me/fines` |
| Admin upload page | ⬜ | Not started (admin API documented in `ADMIN.md`; curl/PowerShell flow works) |
| Error/refusal states | ✅ | Refused answers render in red with `refused` badge; login/401/403 errors shown clearly; backend-down note in chat |
| User guide | ✅ | `USER.md` in repo root updated for Excel-only runtime |
| Admin guide | ✅ | `ADMIN.md` in repo root updated for JSON state store |

### Phase 7 — Quality, security, and polish

| Area | Status | Notes |
|---|---|---|
| Auth tests | ✅ | `backend/tests/test_auth.py` — 9 passing |
| Smoke tests | ✅ | `backend/tests/test_smoke.py` — 2 passing (`/health`, `/health/data`) |
| RBAC tests | ✅ | `require_role` + 401/403 coverage in `test_admin.py` (resident blocked from all `/admin/*`) |
| Retrieval tests | ✅ | `test_ingestion.py` — extraction, chunking bounds, job lifecycle, admin guard, end-to-end upload→ingest→store (11 tests) |
| Chat tests | ✅ | `test_chat.py` — 19 tests: router unit cases, public+citations, anonymous public, private scoping/isolation, hybrid, all spec refusal examples, refusal audit entries |
| Refusal tests | ✅ | Covered in `test_chat.py` (neighbor dues, specific flat fine, other-resident payments, unauthenticated private) |
| Eval harness | ✅ | `data/eval_queries/eval_queries.jsonl` (73 cases: 23 public incl. 3 Act-based / 20 private / 20 unauthorized / 10 hybrid) + `scripts/run_eval.py` — scores routing, citations, refusals, leakage, content; 73/73 passing |
| Audit logging | ✅ | Login/me + `query_private`/`query_public` + `access_denied` + `upload_document`/`delete_document`/`ingest_trigger`/`ingestion_job` events all logged to `data/app_state/audit_logs.json` |
| Deployment prep | ⬜ | Not started |
| Demo assets/screenshots | ⬜ | Not started |

---

## Current documents available

The following documents are now available in the repo:

1. `README.md`
2. `00_INDEX.md`
3. `02_PRD.md`
4. `03_ARCHITECTURE.md`
5. `04_DB_SCHEMA.md`
6. `05_API_RBAC_SPEC.md`
7. `06_RAG_INGESTION_SPEC.md`
8. `07_PROMPT_GUARDRAILS.md`
9. `08_SYNTHETIC_DATA_AND_TESTS.md`
10. `09_BUILD_ORDER.md`
11. `AGENTS.md`
12. `10_CURRENT_PROGRESS.md`
13. `11_PERSONALIZATION.md`
14. `12_TROUBLESHOOTING.md`

---

## Important project decisions already made

### 1. The schema has been simplified
The project uses a simpler housing-society-sized design rather than a large enterprise schema.

### 2. Excel workbook is the runtime source of truth for resident data
- private resident data is read directly from the workbook
- public notices/policies go through RAG
- app-managed metadata (users, documents, jobs, audit logs) lives in JSON files

### 3. Monthly payments are tracked in a `Payments` sheet
Each cell holds the amount paid for that month; 0 = unpaid, full maintenance + fines = paid, anything between = partial.

### 4. Security is a core feature
The project must refuse unauthorized access to another resident's private data.

---

## Immediate next steps

### Recommended next implementation order

1. ✅ Create the local repo/folder scaffold
2. ✅ Seed synthetic resident/payment/fine data (108 residents in workbook)
3. ✅ Create backend FastAPI app structure (foundation complete — config, health endpoints)
4. ✅ Add auth and JWT flow (bcrypt passwords, JWT issue/verify, `/auth/{login,me}`, role guards, audit logging)
5. ✅ Add `/me/*` resident endpoints (profile, dues, payments, fines — scoped to authenticated resident)
6. ✅ Add document metadata + ingestion pipeline (extract → clean → chunk → embed → Chroma; sample docs ingested)
7. ✅ Add vector retrieval and chat routing (`POST /chat/query` — public/private/hybrid/refused, citations, audit logging)
8. ✅ Build chat UI (extended `demo-login.html` — chat panel with route badges, citations, refusal states, suggestion chips, resident account summary)
9. ✅ Add evaluation harness (`data/eval_queries/` + `scripts/run_eval.py` — 73/73 passing)
10. ✅ Ingest real corpus (Maharashtra Co-operative Societies Act, 1960 — 422 chunks across 13 documents)
11. ✅ Switch to Excel-only runtime (`backend/app/workbook/`, `backend/app/statestore.py`, workbook normalization, migration script)
12. ⬜ Optional: plug an OpenAI-compatible LLM behind `app/chat/composer.py` (prompt templates already in `app/prompts/templates.py`)
13. ⬜ Optional: admin upload page (API works; UI would extend `demo-login.html`)
14. ⬜ Deployment prep + demo assets (screenshots, demo script)

---

## What a coding agent should do next

If a coding agent starts from this repo now, the next action should be:

### First task
The MVP core is complete end-to-end (auth → RBAC → Excel workbook → JSON state store → ingestion → retrieval → chat → demo UI, 60 tests + 73 eval cases passing). Remaining work is polish, not function.

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
