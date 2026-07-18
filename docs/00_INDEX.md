# Project Document Index

This index explains the recommended reading and execution order for the Housing Society AI Assistant project documents.

It is designed for three audiences:

- **Coding agents** that need a build sequence
- **Stakeholders/managers** that need product and delivery clarity
- **Beginners/collaborators** that need a structured overview

## Recommended order

### 1. [01_README.md](01_README.md)
**Purpose:** Entry point for the repository.

Read this first to understand what the project is, why it exists, who it is for, the suggested folder structure, and how the rest of the documents are organized.

### 2. [02_PRD.md](02_PRD.md)
**Purpose:** Product Requirements Document.

Defines the problem, target users, core use cases, MVP scope, out-of-scope features, success criteria, and the main product goals.

### 3. [03_ARCHITECTURE.md](03_ARCHITECTURE.md)
**Purpose:** System architecture blueprint.

Explains how the project is split into frontend, backend, auth, SQL, vector retrieval, ingestion, query router, LLM orchestration, logging, and response formatting.

### 4. [04_DB_SCHEMA.md](04_DB_SCHEMA.md)
**Purpose:** Private data model and relational schema.

Defines the SQL tables, relationships, access boundaries, and the structured data that powers resident-specific and admin-facing functionality.

### 5. [05_API_RBAC_SPEC.md](05_API_RBAC_SPEC.md)
**Purpose:** Endpoint contracts and authorization rules.

Defines roles, permissions, protected routes, chat behavior, refusal behavior, and the API request/response structure needed for backend implementation.

### 6. [06_RAG_INGESTION_SPEC.md](06_RAG_INGESTION_SPEC.md)
**Purpose:** Document ingestion and retrieval design.

Explains how documents are uploaded, parsed, chunked, embedded, indexed, retrieved, filtered, and cited in responses.

### 7. [07_PROMPT_GUARDRAILS.md](07_PROMPT_GUARDRAILS.md)
**Purpose:** AI behavior and safety rules.

Defines prompt templates, privacy guardrails, refusal rules, grounding expectations, fallback behavior, and how public/private/hybrid answers should be handled.

### 8. [08_SYNTHETIC_DATA_AND_TESTS.md](08_SYNTHETIC_DATA_AND_TESTS.md)
**Purpose:** Demo data and validation plan.

Defines the synthetic SQL data, synthetic document corpus, test users, acceptance scenarios, and baseline evaluation cases for local development.

### 9. [09_BUILD_ORDER.md](09_BUILD_ORDER.md)
**Purpose:** Implementation sequence.

This is the execution guide for the coding agent or developer. It gives the step-by-step build order from scaffolding to auth, SQL, ingestion, retrieval, chat orchestration, tests, UI, and deployment prep.

## Additional project documents

### 10. [10_CURRENT_PROGRESS.md](10_CURRENT_PROGRESS.md)
Tracks the live status of the project, including what is done, what is in progress, what is blocked, and what should happen next.

### 11. [11_PERSONALIZATION.md](11_PERSONALIZATION.md)
Defines how the assistant and collaborating agents should communicate while working on this project, including response behavior, tone, structure, clarification style, and writing preferences.


## Best way to use this index

### For coding agents
Read documents in order from **1 to 9**, then use `BUILD_ORDER.md` as the implementation checklist.

### For stakeholders/managers
Focus first on:

- `README.md`
- `PRD.md`
- `ARCHITECTURE.md`
- `BUILD_ORDER.md`

These give the clearest view of project value, scope, system design, and delivery plan.

### For beginners/collaborators
Start with:

- `README.md`
- `PRD.md`
- `ARCHITECTURE.md`
- `DB_SCHEMA.md`

Then move into the technical implementation specs.

## Quick summary of document roles

| No. | Document | Main role |
|---|---|---|
| 1 | `README.md` | Repo entry point and overview |
| 2 | `PRD.md` | Product scope and requirements |
| 3 | `ARCHITECTURE.md` | Technical system design |
| 4 | `DB_SCHEMA.md` | SQL data model |
| 5 | `API_RBAC_SPEC.md` | API contracts and permissions |
| 6 | `RAG_INGESTION_SPEC.md` | Retrieval and document pipeline |
| 7 | `PROMPT_GUARDRAILS.md` | LLM behavior and safety |
| 8 | `SYNTHETIC_DATA_AND_TESTS.md` | Demo data and validation |
| 9 | `BUILD_ORDER.md` | Build sequence and execution plan |

## Suggested future additions

If the project grows, add these after the current set:

- `DEPLOYMENT.md`
- `EVALUATION_PLAN.md`
- `UI_UX_SPEC.md`
- `RESUME_CASE_STUDY.md`
- `ER_DIAGRAM.mmd`
- `ARCHITECTURE_FLOW.mmd`
