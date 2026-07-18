# Build Order

## Purpose

This document tells a coding agent or developer the recommended implementation order for the Housing Society AI Assistant.

## Principle

Build the system in layers. Do not start with the UI. Start with the backend contracts, security, and data model.

## Step 0 — Read the docs first

Read these files before implementing anything:

1. `PRD.md`
2. `ARCHITECTURE.md`
3. `DB_SCHEMA.md`
4. `API_RBAC_SPEC.md`
5. `RAG_INGESTION_SPEC.md`
6. `PROMPT_GUARDRAILS.md`
7. `SYNTHETIC_DATA_AND_TESTS.md`

## Step 1 — Scaffold the repository

Create:

- backend app structure
- frontend app structure
- data folders
- scripts folder
- env example files
- requirements and package manifests

## Step 2 — Implement backend foundation

- create FastAPI app entrypoint
- create config loader
- create database connection
- create migration setup
- create health endpoint
- create base error handling

## Step 3 — Implement auth and RBAC

- users table
- roles table
- user_roles table
- password hashing
- JWT issue/verify flow
- auth routes
- role-check dependencies

## Step 4 — Implement private SQL domain

- flats model
- residents model
- maintenance_dues model
- payments model
- complaints model
- vehicles model
- query_logs model
- audit_logs model

Then add:
- `/me/profile`
- `/me/dues`
- `/me/payments`
- `/me/complaints`
- `/me/vehicles`

## Step 5 — Seed synthetic SQL data

- create resident users
- create admin user
- create staff user if needed
- seed flats, dues, payments, complaints, vehicles
- document seed credentials clearly

## Step 6 — Implement document upload metadata and ingestion jobs

- notices_metadata table
- ingestion_jobs table
- admin upload endpoint
- ingestion status endpoint

## Step 7 — Implement ingestion pipeline

- file loading
- text extraction
- cleaning
- chunking
- metadata creation
- embedding generation
- vector store write

## Step 8 — Seed synthetic documents

Add the sample policy, notice, and AGM files and index them.

## Step 9 — Implement retrieval and query routing

- public retrieval flow
- private SQL query flow
- hybrid flow
- intent classification / routing logic
- metadata filters where useful

## Step 10 — Implement chat orchestration

- `/chat/query` endpoint
- prompt assembly
- public answer formatting
- private answer formatting
- hybrid answer formatting
- refusal behavior
- citations for document-backed responses

## Step 11 — Add logging and audit behavior

- auth logs
- private query logs
- denial/refusal logs
- ingestion logs
- error logs

## Step 12 — Implement tests

Use `SYNTHETIC_DATA_AND_TESTS.md` as the source of truth.

Add:
- auth tests
- RBAC tests
- private access tests
- ingestion tests
- public retrieval tests
- hybrid tests
- refusal tests

## Step 13 — Build the frontend

Create:

- login page
- chat page
- resident account summary panels
- admin upload page
- citation display
- error and refusal display states

## Step 14 — Improve polish

- loading states
- empty states
- cleaner prompts
- query history
- better admin ingestion visibility
- local demo instructions

## Step 15 — Deployment and demo preparation

- Dockerize backend/frontend if desired
- prepare env files
- prepare local run script
- add screenshots
- add short demo video notes

## Definition of MVP done

The MVP is done when:

- auth works
- RBAC works
- residents can view only their own private data
- public document retrieval works with citations
- ingestion works
- hybrid routing works
- unauthorized access is refused
- logs are present
- demo data is included

## Coding agent execution notes

- complete one step fully before moving to the next
- keep modules separate and testable
- avoid mixing private SQL storage into vector retrieval
- prefer deterministic app logic for auth and access control
- treat the docs in this repo as implementation contracts
