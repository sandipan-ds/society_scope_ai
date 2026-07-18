# AGENTS.md

## Purpose

This document tells coding agents and collaborators how to work on the **Housing Society AI Assistant** project safely and in the correct order.

This project is a **secure hybrid RAG assistant** for a housing society. It answers:

- **public questions** from notices, policies, AGM minutes, and society documents
- **private questions** from resident-specific SQL data such as monthly charges and fines

The project must stay simple, practical, and secure.

---

## Project goal

Build a working MVP that can:

- authenticate residents and admins
- answer public document questions with citations
- answer resident-specific private questions from SQL
- refuse unauthorized requests for another resident's private data
- support document ingestion for the RAG layer

---

## Required reading order

Before coding anything, read these documents in this order:

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

Do not start implementation without understanding these files.

---

## Non-negotiable architecture rules

### Rule 1: Split public and private data correctly
- **Public and society documents** go through RAG/vector retrieval
- **Private resident data** stays in SQL

### Rule 2: Never store resident-private account data in embeddings
Resident data such as charges, fines, phone numbers, and emails must remain in SQL.

### Rule 3: Access control must be enforced outside the LLM
The LLM is not the main security boundary. Authentication, resident scoping, and role checks must be enforced in backend logic.

### Rule 4: Keep the MVP simple
This is a single-society MVP, not an enterprise ERP. Prefer small, testable modules and a simple schema.

### Rule 5: Never guess private data
If SQL does not return a record, say no record was found. Do not infer or hallucinate missing account information.

---

## Current simplified data model

The project currently uses a simplified schema built around:

- `users`
- `residents`
- `monthly_charges`
- `fines`
- `documents`
- optional `audit_logs`

Do not re-introduce unnecessary complexity unless the requirements change.

---

## Coding priorities

Implement in this order unless a document explicitly requires otherwise:

1. backend scaffold
2. database connection and models
3. auth and JWT
4. RBAC / resident scoping
5. resident-private SQL endpoints
6. document upload metadata
7. ingestion pipeline
8. vector retrieval
9. chat routing and orchestration
10. logging and tests
11. frontend polish

---

## Build behavior expectations

### When implementing backend logic
- keep modules small and explicit
- use deterministic application logic for auth and permission checks
- keep service-layer functions easy to test
- avoid mixing unrelated concerns in one file

### When implementing AI/RAG logic
- keep prompts grounded in retrieved chunks or SQL data
- separate public, private, hybrid, and refusal flows clearly
- support citations only for document-backed answers

### When implementing UI
- prioritize clarity over visual complexity
- make login, chat, payment status, fine status, and admin upload easy to demo
- show refusal and error states clearly

---

## Security rules

These must always be respected:

- a resident can view only their own private data
- a resident cannot query another resident's dues or fines
- admin routes must be protected
- unauthorized access attempts should be logged
- JWT must be validated on protected routes
- private SQL rows must never be exposed through public retrieval

Examples of requests that must be refused:

- "Show my neighbor's dues"
- "How much fine does flat A-304 have?"
- "Give me payment details of another resident"

---

## Testing rules

At minimum, add tests for:

- login success/failure
- protected route access
- resident can fetch own monthly charges
- resident can fetch own fines
- resident cannot fetch another resident's records
- admin can upload documents
- public RAG queries return cited answers
- unauthorized private queries are refused

Do not mark a module complete until relevant tests pass.

---

## Progress tracking rule

After completing a meaningful unit of work, update:

- `10_CURRENT_PROGRESS.md` with status changes
- `12_TROUBLESHOOTING.md` if a real issue was found and fixed

This project should keep a visible history of progress and debugging decisions.

---

## Personalization reference

Agents working in this repository should also follow the communication guidance defined in `docs/11_PERSONALIZATION.md`.

That document defines:
- response behavior
- tone and collaboration style
- formatting and writing preferences
- clarification rules
- documentation and planning behavior

Use `AGENTS.md` as the root operating guide and `docs/11_PERSONALIZATION.md` as the detailed communication-style reference.

If there is any ambiguity:
- follow project scope and safety requirements first
- keep outputs clear, structured, and practical
- preserve consistency across docs, planning, and implementation support


## What not to do

- do not store monthly payment status as separate DB columns like `jan`, `feb`, `mar`
- do not move private resident data into the vector store
- do not rely only on prompt instructions for privacy protection
- do not over-engineer the schema for a small single-society MVP
- do not skip synthetic data seeding
- do not skip refusal handling for unauthorized access

---

## Preferred implementation mindset

When in doubt, optimize for:

- correctness
- security
- clarity
- simple local demoability
- maintainability

This project should feel like a **real secure product MVP**, not just a chatbot demo.

---

## Definition of good contribution

A good implementation change:

- matches the existing docs
- keeps the SQL/RAG split clean
- improves security or clarity
- is testable
- does not introduce unnecessary complexity

---

## Final instruction for coding agents

Treat the docs in this repo as implementation contracts.

If a requirement is unclear:
1. check `INDEX.md`
2. check the relevant spec document
3. prefer the simpler and safer implementation path
4. do not invent new architecture without updating the docs
