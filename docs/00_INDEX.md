# 00_INDEX.md

## Purpose of This Index

This repository contains the planning, architecture, security, data, and implementation documents for a **Housing Society AI Assistant**.

The project is intentionally documented in a structured way so that developers, coding agents, reviewers, and stakeholders can understand:

- what the system is supposed to do
- what is in scope for the MVP
- how public and private data are separated
- where access control is enforced
- how RAG, SQL, and orchestration fit together
- what order implementation should follow

This index is the recommended entry point after `AGENTS.md`.

---

## Recommended Reading Paths

### For coding agents and engineers implementing features

Read in this order:

1. `AGENTS.md`
2. `00_INDEX.md`
3. `coding-agent-workflow.md`
4. `01_README.md`
5. `02_PRD.md`
6. `03_ARCHITECTURE.md`
7. `04_DB_SCHEMA.md`
8. `05_API_RBAC_SPEC.md`
9. `06_RAG_INGESTION_SPEC.md`
10. `07_PROMPT_GUARDRAILS.md`
11. `08_SYNTHETIC_DATA_AND_TESTS.md`
12. `09_BUILD_ORDER.md`
13. `10_CURRENT_PROGRESS.md`
14. `11_PERSONALIZATION.md`
15. `12_TROUBLESHOOTING.md`

This order moves from project intent to system design, then to implementation detail, and finally to project-state and collaboration docs.

### For reviewers and maintainers

Recommended order:

1. `AGENTS.md`
2. `01_README.md`
3. `02_PRD.md`
4. `03_ARCHITECTURE.md`
5. `05_API_RBAC_SPEC.md`
6. `06_RAG_INGESTION_SPEC.md`
7. `09_BUILD_ORDER.md`
8. `10_CURRENT_PROGRESS.md`
9. `12_TROUBLESHOOTING.md`

This path helps reviewers understand intent, constraints, and current implementation maturity.

### For stakeholders or beginners

Recommended order:

1. `01_README.md`
2. `02_PRD.md`
3. `03_ARCHITECTURE.md`
4. `09_BUILD_ORDER.md`
5. `10_CURRENT_PROGRESS.md`

This path gives a high-level view before diving into lower-level implementation details.

---

## Document Guide

### `AGENTS.md`
Root instruction file for coding agents. Defines repo-level rules, workflow expectations, architecture constraints, and contribution standards.

### `coding-agent-workflow.md`
Detailed execution workflow for non-trivial coding-agent tasks. Explains how to classify work, inspect entry points and dependencies, identify critical and risky areas, choose the smallest safe change, and verify the result with tests and progress updates.

### `01_README.md`
High-level overview of the project, its purpose, audience, suggested repo structure, stack, development phases, and success criteria.

### `02_PRD.md`
Defines the product problem, goals, target users, MVP scope, functional expectations, non-functional requirements, and risks.

### `03_ARCHITECTURE.md`
Explains the hybrid design: public knowledge through RAG, private resident data through SQL, orchestration flow, module layout, and security enforcement points.

### `04_DB_SCHEMA.md`
Defines the simplified MVP schema, key tables, relationships, and practical data-modeling rules for resident, charge, fine, and document data.

### `05_API_RBAC_SPEC.md`
Specifies roles, permissions, protected routes, endpoint behavior, refusal logic, error policy, and audit expectations.

### `06_RAG_INGESTION_SPEC.md`
Defines the ingestion pipeline, chunking, metadata, vector storage expectations, retrieval routes, prompt inputs, citation rules, and failure handling.

### `07_PROMPT_GUARDRAILS.md`
Documents prompt-level behavior, privacy guardrails, refusal rules, and answer-shaping expectations for the AI layer.

### `08_SYNTHETIC_DATA_AND_TESTS.md`
Describes the synthetic data, seed expectations, acceptance scenarios, and test coverage needed for local development and demos.

### `09_BUILD_ORDER.md`
Provides the implementation sequence for building the system safely from backend foundations through frontend and polish.

### `10_CURRENT_PROGRESS.md`
Tracks what is complete, in progress, blocked, and next.

### `11_PERSONALIZATION.md`
Defines communication and collaboration style expectations for the assistant and collaborating agents.

### `12_TROUBLESHOOTING.md`
Captures important bugs, fixes, root causes, and lessons learned.

---

## How to Use the Docs During Implementation

### When starting a new feature

Read:

- `02_PRD.md`
- `03_ARCHITECTURE.md`
- `05_API_RBAC_SPEC.md`
- `06_RAG_INGESTION_SPEC.md`
- `09_BUILD_ORDER.md`

Then review any directly relevant progress and troubleshooting notes.

### When changing schema or private-data behavior

Read:

- `04_DB_SCHEMA.md`
- `05_API_RBAC_SPEC.md`
- `03_ARCHITECTURE.md`

Confirm that private data remains in SQL and scoped correctly.

### When changing retrieval, ingestion, or citations

Read:

- `06_RAG_INGESTION_SPEC.md`
- `03_ARCHITECTURE.md`
- `07_PROMPT_GUARDRAILS.md`

Confirm grounding, metadata, and versioning expectations remain intact.

### When changing chat behavior or refusals

Read:

- `05_API_RBAC_SPEC.md`
- `06_RAG_INGESTION_SPEC.md`
- `07_PROMPT_GUARDRAILS.md`

Confirm answer types, refusal behavior, and privacy boundaries remain correct.

---

## Documentation Principles for This Repo

When adding or editing code, contributors should preserve these documented principles:

- **Public and private data are handled differently on purpose**
- **Access control is enforced in backend logic, not delegated to prompts**
- **The MVP should stay simple, practical, and locally demoable**
- **Answers should be grounded and explainable**
- **Refusal behavior is a required feature, not a fallback**
- **Progress and troubleshooting should be documented as the project evolves**

---

## Quick Navigation Summary

If you only remember one sequence, use this:

1. `AGENTS.md`
2. `01_README.md`
3. `02_PRD.md`
4. `03_ARCHITECTURE.md`
5. `04_DB_SCHEMA.md`
6. `05_API_RBAC_SPEC.md`
7. `06_RAG_INGESTION_SPEC.md`
8. `09_BUILD_ORDER.md`
9. `10_CURRENT_PROGRESS.md`
10. `12_TROUBLESHOOTING.md`

That path covers purpose, architecture, constraints, execution order, and current reality.

---

## Final Note

This documentation set is designed to reduce ambiguity. When code, assumptions, or requests conflict with the docs, prefer the docs and surface the conflict clearly before implementation.
