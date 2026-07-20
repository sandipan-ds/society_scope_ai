# Housing Society AI Assistant

A secure hybrid RAG project for answering housing society questions with a clear split between public document knowledge and private resident data.

## What this project does

This system answers:

- **Public questions** from housing rules, notices, circulars, and AGM minutes
- **Private questions** such as a resident's dues, payments, complaints, and profile data
- **Hybrid questions** that require both document retrieval and private Excel workbook lookup

The core design principle is:

- **RAG for public and society documents**
- **Excel for private resident data**
- **JWT + RBAC for access control**

## Why this repo exists

This repo is designed to help three groups understand and build the project:

- **Coding agents**: need implementation-ready specs and build order
- **Stakeholders / managers**: need scope, users, risks, and success criteria
- **Beginners / collaborators**: need a clear, structured explanation of how the system works

## Minimum required starter documents

Yes — most of the documents discussed earlier are genuinely useful. For a strong start, the minimum recommended set is:

1. `PRD.md`
2. `ARCHITECTURE.md`
3. `DB_SCHEMA.md`
4. `API_RBAC_SPEC.md`
5. `RAG_INGESTION_SPEC.md`
6. `PROMPT_GUARDRAILS.md`
7. `SYNTHETIC_DATA_AND_TESTS.md`
8. `BUILD_ORDER.md`

These are enough to let a coding agent build the project with much less back-and-forth.

## Suggested local repo structure

```text
housing-society-ai/
├── README.md
├── PRD.md
├── ARCHITECTURE.md
├── DB_SCHEMA.md
├── API_RBAC_SPEC.md
├── RAG_INGESTION_SPEC.md
├── PROMPT_GUARDRAILS.md
├── SYNTHETIC_DATA_AND_TESTS.md
├── BUILD_ORDER.md
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── chat/
│   │   ├── workbook/
│   │   ├── ingestion/
│   │   ├── retrieval/
│   │   ├── prompts/
│   │   ├── guardrails/
│   │   ├── logging/
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── data/
│   ├── sample_docs/
│   ├── synthetic_excel/
│   └── eval_queries/
├── scripts/
│   ├── seed_workbook.py
│   ├── ingest_docs.py
│   └── run_eval.py
├── deployments/
│   ├── docker/
│   └── render_or_railway/
└── docs/
    ├── screenshots/
    └── demo-notes/
```

## Recommended build stack

- **Backend**: Python + FastAPI
- **Primary data source**: Excel workbook
- **Optional backup database**: PostgreSQL later if needed
- **Vector DB**: Chroma for local MVP, Pinecone/Weaviate later if needed
- **LLM layer**: API-based LLM or local model abstraction
- **Auth**: JWT + RBAC
- **Frontend**: React / Next.js or simple React SPA
- **Deployment**: Docker + Render/Railway/VPS

## Project phases

### Phase 0 — Docs and data model

Write the core specs before coding.

### Phase 1 — MVP

Build auth, Excel workbook handling, ingestion, vector retrieval, query router, and chat API.

### Phase 2 — Quality and safety

Add guardrails, audit logs, refusal behavior, and evaluations.

### Phase 3 — Resume polish

Deploy, add clean UI, provide demo data, screenshots, and a short demo video.

## What success looks like

A strong MVP should let a user:

- log in securely
- ask public questions with cited answers
- ask private questions and receive only their own data
- be denied access to unauthorized private information
- use a simple UI that clearly shows source-backed answers

## How to use these docs

Start in this order:

1. Read `PRD.md`
2. Read `ARCHITECTURE.md`
3. Read `DB_SCHEMA.md`
4. Read `API_RBAC_SPEC.md`
5. Read `RAG_INGESTION_SPEC.md`
6. Read `PROMPT_GUARDRAILS.md`
7. Read `SYNTHETIC_DATA_AND_TESTS.md`
8. Execute `BUILD_ORDER.md`

## Notes

- Use **synthetic data first** if real society data is not available.
- Keep **private resident workbook data out of vector embeddings**.
- Treat this as a **secure product system**, not just a chatbot.
- Keep auditability and refusal behavior visible in the implementation.
- Use **Excel as the primary admin-facing operational tool** for charges and fines.
