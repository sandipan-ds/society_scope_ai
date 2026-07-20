# coding-agent-workflow.md

## Goal

Use coding agents as **disciplined implementation partners**, not as blind code generators.

For this repository, the agent’s job is to make safe, grounded, production-aware changes for a **secure hybrid Housing Society AI Assistant**. The workflow must preserve:

- public/private data separation
- backend-enforced JWT and RBAC
- grounded public retrieval
- authorized private SQL access
- safe refusal behavior
- MVP simplicity and local demoability

---

## When to Use This Workflow

Use this workflow for any non-trivial change, especially changes touching:

- authentication
- authorization / RBAC
- resident-private SQL data
- query routing
- chat orchestration
- refusal behavior
- ingestion or retrieval
- citations and grounding
- logging / audit behavior
- schema or API contracts

For tiny isolated edits, a lighter version is acceptable, but the core architecture rules still apply.

---

## Phase 0: Read the Right Documents First

Before coding, review the relevant project documents in order:

1. `AGENTS.md`
2. `00_INDEX.md`
3. `01_README.md`
4. `02_PRD.md`
5. `03_ARCHITECTURE.md`
6. `04_DB_SCHEMA.md`
7. `05_API_RBAC_SPEC.md`
8. `06_RAG_INGESTION_SPEC.md`
9. `09_BUILD_ORDER.md`

Then read task-specific supporting docs when relevant:

- `07_PROMPT_GUARDRAILS.md`
- `08_SYNTHETIC_DATA_AND_TESTS.md`
- `10_CURRENT_PROGRESS.md`
- `11_PERSONALIZATION.md`
- `12_TROUBLESHOOTING.md`

Treat these docs as implementation contracts.

---

## Phase 1: Classify the Change Before Touching Code

Classify the requested work as one of these:

### Public
Document-backed question answering only.

### Private
Resident-specific SQL-backed access only.

### Hybrid
Authorized SQL data combined with public document retrieval.

### Refusal-sensitive
Requests where the system must deny, limit, or carefully phrase the response to avoid leaking protected information.

This classification determines what boundaries must be protected.

---

## Phase 2: Build a Change Impact Report

Before implementation, create a short impact report.

### Include

**Task**
- what change is requested

**Classification**
- public / private / hybrid / refusal-sensitive

**Entry points**
- routes, handlers, scheduled jobs, ingestion triggers, orchestration entry functions

**Execution flow**
- the end-to-end path from input to response

**Relevant files and modules**
- only the files directly involved or likely affected

**Dependencies**
- auth dependencies
- SQL dependencies
- retrieval / vector dependencies
- prompt and formatting dependencies
- logging / audit dependencies
- external integrations

**Security boundary**
- where JWT, route protection, RBAC, and query-time authorization are enforced

**Critical areas**
- where failure would create security, privacy, correctness, or audit issues

**Breaking points**
- API contracts
- role behavior
- schema assumptions
- metadata contracts
- response-shape expectations

**Risk level**
- low / medium / high with reason

**Smallest safe implementation**
- the least disruptive way to solve it

**Test plan**
- unit, integration, and refusal-path coverage needed

**Open questions**
- anything uncertain or blocked

If uncertain, distinguish between observed facts and assumptions.

---

## Phase 3: Inspect the Five Things That Matter Most

Before editing, explicitly inspect these five areas.

### 1. Entry points
Find where the flow begins. Examples include:

- API routes
- auth dependencies
- chat query handlers
- admin document upload endpoints
- ingestion jobs
- retrieval services
- orchestration functions

### 2. Dependency chain
Trace:

- module imports
- function calls
- data dependencies
- shared utilities
- external service touchpoints

### 3. Critical path
Identify the minimal path that must remain correct for the feature to work safely.

### 4. Breaking points
Look for interfaces where a change can silently break behavior, especially:

- request/response shapes
- SQL filters and joins
- role checks
- metadata fields
- response formatting contracts

### 5. Risky areas
Mark anything involving:

- authentication
- resident scoping
- side effects or writes
- hidden coupling
- retries / async work
- mixed public/private context assembly
- refusal wording
- logging requirements

---

## Repo-Specific Invariants

The following must remain true after any change.

### Data separation invariant
Public document knowledge may be embedded and retrieved. Private resident data must stay in SQL.

### Access-control invariant
JWT validation, route protection, and RBAC must be enforced in backend code, not delegated to the LLM.

### Response-type invariant
The system must continue to support clear public, private, hybrid, and refusal paths.

### Grounding invariant
Public answers must be grounded in retrieval results. Private answers must come from scoped SQL data. No fabricated citations.

### MVP invariant
Favor simple, practical, reviewable implementations over clever abstractions.

---

## Implementation Rules

When coding, follow these rules:

- make the **smallest safe change**
- edit the **correct layer** instead of patching symptoms elsewhere
- preserve **documented contracts** unless intentionally updating them
- keep private/public data **strictly separated**
- avoid unrelated refactors
- keep logic modular enough to test directly
- preserve local setup and demoability
- prefer explicitness over magic

If the request seems to require a rule violation, stop and surface the conflict.

---

## High-Risk Areas in This Repo

Treat these as high-risk by default:

- auth and JWT handling
- role enforcement
- query-time resident scoping
- SQL service-layer filters
- query router classification
- public/private/hybrid prompt assembly
- ingestion pipeline quality
- chunk metadata and versioning
- response grounding and citation formatting
- audit logging and refusal logging
- schema changes affecting users, residents, monthly charges, fines, or documents

These areas deserve closer review and stronger tests.

---

## What Not To Do

Do not:

- move private resident data to embeddings
- depend on prompts alone for privacy
- leak hidden information through denials or summaries
- fabricate document support or citations
- overcomplicate the MVP architecture
- redesign schema patterns casually
- represent monthly charges as separate month columns
- skip refusal scenarios in testing
- ignore audit and logging expectations

---

## Testing Workflow

Every meaningful change should answer two questions:

1. **What behavior did we intend to change?**
2. **What behavior must remain unchanged?**

### Minimum test categories

**Authentication**
- valid login
- invalid login
- token validation
- protected-route behavior

**Authorization**
- resident can access only their own data
- cross-resident access is denied
- admin/staff permissions behave correctly

**Chat behavior**
- public question returns document-grounded output
- private question returns scoped SQL-backed output
- hybrid question combines only allowed sources
- unauthorized question is refused safely

**RAG / ingestion**
- upload metadata persists correctly
- ingestion status is visible
- retrieval uses metadata and returns useful chunks

**Logging / audit**
- protected activity is logged where expected
- denial/refusal paths are logged where expected
- ingestion events are trackable

---

## Recommended Output Template for Agents

### Before coding

**Change Impact Report**

- Task
- Classification
- Entry points
- Execution flow
- Relevant files/modules
- Dependencies
- Security boundary
- Critical areas
- Breaking points
- Risk level
- Smallest safe implementation
- Test plan
- Open questions

### After coding

**Change Summary**

- Files changed
- Why each file changed
- Contracts intentionally preserved
- Tests added or updated
- Residual risks
- Whether progress docs were updated

---

## Progress Tracking

After a meaningful work unit, update the project tracking docs when appropriate:

- `10_CURRENT_PROGRESS.md`
- `12_TROUBLESHOOTING.md`

Record:

- completed work
- remaining work
- blockers
- bug root causes and fixes
- lessons useful for future contributors

---

## How to Decide Between Two Implementations

If several implementations are possible, choose the one that best preserves:

1. correctness
2. security
3. privacy boundaries
4. clear reasoning
5. testability
6. grounded behavior
7. maintainability
8. simplicity

If one version is more clever and the other is more obvious, prefer the more obvious one unless there is a strong reason not to.

---

## Definition of Done for Agent Work

Agent work is done only when:

- the change matches the documented project intent
- data boundaries remain intact
- authorization still holds
- the implementation is testable
- refusal behavior is still safe
- grounding/citations remain correct where required
- important risks are either handled or clearly documented
- progress tracking is updated when applicable

A fast patch is not a good result if future contributors cannot safely reason about it.
