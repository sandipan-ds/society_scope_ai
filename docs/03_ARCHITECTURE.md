# System Architecture

## Overview

The Housing Society AI Assistant uses a **secure hybrid architecture**:

- **RAG pipeline** for public and society documents
- **Excel workbook** for private member data
- **JWT + RBAC** for authentication and authorization
- **LLM orchestration layer** for answer generation

## High-level modules

### 1. Frontend

Responsible for login, chat UI, uploads for admins, and displaying answers with citations.

### 2. Backend API

Handles auth, chat requests, document ingestion, protected data access, and admin operations.

### 3. Auth module

Issues and validates JWTs, loads roles, and enforces route-level protection.

### 4. Excel workbook data layer

Stores residents, dues, payments, complaints, flats, fines, and other private society operational data in a structured workbook.

### 5. Vector retrieval layer

Stores embeddings of public housing documents and society-specific documents.

### 6. Ingestion pipeline

Parses documents, chunks them, attaches metadata, embeds them, and stores them for retrieval.

### 7. Query router

Classifies a query as one of:

- public-document query
- private-Excel query
- hybrid query
- unauthorized or unsupported query

### 8. LLM orchestration layer

Builds the final prompt using retrieved document chunks, Excel workbook results, role context, and guardrails.

### 9. Response formatter

Formats the final answer, citations, safe fallback messages, and refusal responses.

### 10. Logging and audit layer

Tracks auth events, private-data access, ingestion jobs, failures, and admin actions.

## Core design rule

Do **not** store private member-specific data as embeddings. Keep resident-private information in the Excel workbook and access it only after authentication and role checks.

## Data separation

### Public / document knowledge

Stored in vector search:

- society handbook
- AGM minutes
- notices and circulars
- parking policy
- pet policy
- vendor and maintenance announcements

### Private resident data

Stored in the Excel workbook:

- resident details
- flat details
- maintenance dues
- payment history
- complaints
- vehicles
- resident profile
- fines and related charge records

## Request flow

```text
User -> Frontend -> Backend API -> JWT validation -> Query Router
If public:
  -> Vector retrieval -> LLM -> Response formatter -> User
If private:
  -> RBAC check -> Excel workbook lookup -> LLM -> Response formatter -> User
If hybrid:
  -> RBAC check + Vector retrieval + Excel workbook lookup -> LLM -> Response formatter -> User
Always:
  -> Audit/logging layer
```

## Recommended backend structure

```text
backend/app/
├── api/              # route definitions
├── auth/             # JWT, password hashing, permission helpers
├── chat/             # chat controller and orchestration
├── workbook/         # workbook readers, validators, mappers
├── ingestion/        # document parsing and embedding pipeline
├── retrieval/        # vector search, hybrid retrieval, reranking hooks
├── prompts/          # prompt builders and templates
├── guardrails/       # refusal and privacy logic
├── logging/          # audit/event logging
└── main.py           # FastAPI app entrypoint
```

## Query routing logic

The router should decide which path to use based on intent.

### Public query examples

- What are the visitor timings?
- What is the parking rule for guests?

### Private query examples

- What are my dues?
- Show my payment history.

### Hybrid query examples

- What is my late fee and what rule defines it?
- Did I miss any maintenance notice relevant to my flat?

## Security enforcement points

Security should be enforced in multiple layers:

- API route protection
- JWT validation
- role permission checks
- query-time resident scoping
- LLM prompt guardrails
- refusal handling
- audit log creation

## Logging requirements

At minimum log:

- login success/failure
- private query attempts
- unauthorized access attempts
- document upload and ingestion status
- chat request metadata
- system errors

## Suggested stack

- FastAPI backend
- Excel workbook as the primary private data source
- Chroma for local vector store MVP
- Pluggable embedding/LLM provider
- React frontend
- Docker for deployment
- Optional SQL backup later if needed, but not required for the core MVP workflow

## Deployment shape

### Local development

- frontend on one port
- backend on one port
- Excel workbook available to the backend locally or through controlled file access
- vector store locally

### Hosted demo

- frontend deployed separately
- backend API deployed with env vars
- securely managed workbook access for private data
- persistent document/vector storage

## Architecture goals

- simple enough for a student to build
- modular enough for future production hardening
- secure enough to demonstrate privacy-aware system design
- clear enough for recruiters and reviewers to understand quickly
