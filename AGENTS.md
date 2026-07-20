# AGENTS.md

## Purpose

This repository builds a **secure Housing Society AI Assistant** that answers:

- **Public questions** from society and housing documents using RAG
- **Private resident-specific questions** from SQL data
- **Hybrid questions** by combining authorized SQL data with relevant public document retrieval

This file is the **root instruction file for coding agents**. Treat the repository documents as implementation contracts. Default to safe, grounded, testable changes that preserve privacy, role boundaries, and MVP simplicity.

---

## Read This Before Coding

Before making any non-trivial change, review the repo documents in this order:

1. `AGENTS.md`
2. `00_INDEX.md`
3. `coding-agent-workflow.md`
4. `01_README.md`
5. `02_PRD.md`
6. `03_ARCHITECTURE.md`
7. `04_DB_SCHEMA.md`
8. `05_API_RBAC_SPEC.md`
9. `06_RAG_INGESTION_SPEC.md`
10. `09_BUILD_ORDER.md`

For non-trivial implementation work, follow `coding-agent-workflow.md` as the detailed execution process for analysis, risk review, change planning, implementation, and verification.

When relevant, also review:

- `07_PROMPT_GUARDRAILS.md`
- `08_SYNTHETIC_DATA_AND_TESTS.md`
- `10_CURRENT_PROGRESS.md`
- `11_PERSONALIZATION.md`
- `12_TROUBLESHOOTING.md`

If a request conflicts with the documented architecture, schema, RBAC rules, or build order, do not improvise. Surface the conflict explicitly.

---

## Repo Core Rules

### 1. Public and private data must stay separated

- Public and society document knowledge belongs in the RAG layer.
- Private resident-specific data belongs in SQL.
- Do **not** move private resident data into embeddings or the vector store.

### 2. Access control must be enforced outside the LLM

- Enforce JWT validation, route protection, and RBAC in backend code.
- Enforce authorization again at query time where needed.
- Do **not** rely on prompts alone to protect private data.

### 3. The system must support four clear answer types

- **Public**: document-backed
- **Private**: SQL-backed and scoped to the caller
- **Hybrid**: authorized SQL + public documents
- **Refused/unsupported**: safe denial without leaking hidden data

### 4. MVP simplicity beats over-engineering

- Build the simplest thing that satisfies the PRD and architecture.
- Avoid speculative abstractions, premature optimization, or unnecessary infrastructure.

### 5. Grounded responses are required

- Public answers must be grounded in retrieved documents.
- SQL-backed answers must come from scoped structured data.
- Do not fabricate citations, sources, or private facts.

---

## How to Work

For any non-trivial task, follow this order:

1. **Understand the request**
2. **Classify the flow** as public, private, hybrid, or refusal-sensitive
3. **Inspect the affected path** end to end
4. **Identify dependencies, boundaries, and risks**
5. **Propose the smallest safe change**
6. **Implement in the right layer**
7. **Add or update tests**
8. **Update progress/troubleshooting docs when applicable**

Do not jump straight to code for changes involving auth, RBAC, SQL scoping, ingestion, retrieval, orchestration, refusal logic, or logging.

---

## Required Pre-Change Analysis

Before architecture-sensitive changes, produce a concise change impact report covering:

- **Task**
- **Classification**: public / private / hybrid / refusal-sensitive
- **Entry points**: routes, handlers, services, jobs
- **Execution flow**: request to response path
- **Relevant modules/files**
- **Dependencies**: auth, SQL, vector retrieval, prompts, logging, external services
- **Security boundary**: where access control is enforced
- **Critical areas**
- **Breaking points**: API contracts, schema assumptions, RBAC behavior, metadata contracts
- **Risk level**: low / medium / high
- **Smallest safe implementation**
- **Test plan**
- **Open questions**

Separate **observed facts** from **assumptions** whenever the codebase is ambiguous.

---

## Repo-Specific Critical Areas

Treat these as high-risk unless proven otherwise:

- authentication and JWT validation
- RBAC and role-based route protection
- query-time authorization
- SQL scoping to the authenticated resident
- chat routing between public, private, hybrid, and refused flows
- prompt assembly and context construction
- ingestion, chunking, metadata, and retrieval quality
- citation behavior and response grounding
- logging and audit trails
- schema changes affecting dues, fines, residents, users, or documents

Any change touching these areas needs careful analysis and tests.

---

## Implementation Rules

- Prefer the **smallest safe diff**.
- Keep logic in the **correct layer**.
- Preserve **public/private data separation**.
- Keep backend logic **modular and testable**.
- Preserve documented **API contracts** unless the change explicitly updates the contract and dependent code.
- Keep the project **easy to run locally**.
- Surface uncertainty instead of guessing.
- Avoid unrelated refactors during scoped feature work.

---

## What Not To Do

Do not:

- put resident-private data into embeddings or vector retrieval
- use prompts as the main privacy mechanism
- leak hidden information through refusal wording
- fabricate citations or document grounding
- over-engineer the MVP
- redesign the simplified schema without clear need
- store month-wise charges as separate month columns instead of row-based records
- skip synthetic-data thinking and refusal-path handling
- bypass logging for sensitive actions

---

## Build Order Discipline

Default implementation sequence should remain aligned with the project build order:

1. backend foundation
2. auth and RBAC
3. private SQL domain
4. synthetic SQL data
5. document metadata and ingestion jobs
6. ingestion pipeline
7. synthetic documents
8. retrieval and query routing
9. chat orchestration
10. logging and audit behavior
11. tests
12. frontend
13. polish
14. deployment/demo preparation

If a requested task depends on unfinished earlier steps, say so clearly and propose the right order.

---

## Testing Expectations

Security and refusal behavior are product features. Test accordingly.

At minimum, relevant changes should verify:

- valid and invalid authentication flows
- route protection and JWT validation
- resident access to own data only
- denial of access to another resident’s data
- correct admin/staff behavior where applicable
- public query grounding
- private query scoping
- hybrid query composition
- safe refusal behavior
- ingestion success/failure visibility
- retrieval quality and metadata use
- logging/audit behavior for sensitive actions

---

## Progress Tracking Rule

After completing a meaningful work unit, update the relevant tracking docs when applicable:

- `10_CURRENT_PROGRESS.md`
- `12_TROUBLESHOOTING.md`

Record completed work, current status, blockers, notable bugs, and lessons that future contributors should know.

---

## Definition of a Good Contribution

A good contribution:

- aligns with the PRD and architecture
- keeps data boundaries clean
- improves correctness, clarity, or security
- preserves or strengthens access control
- remains grounded and explainable
- is easy to test and demo locally
- avoids unnecessary complexity

---

## Default Decision Order

When trade-offs appear, prioritize:

1. correctness
2. security
3. clarity
4. testability
5. grounded behavior
6. local demoability
7. maintainability
8. simplicity over cleverness

If you are unsure, choose the safer and simpler path, and state the uncertainty explicitly.
