# RAG and Ingestion Specification

## Purpose

This document defines how public and society documents are ingested, indexed, retrieved, and used in answers.

## Core principle

Use RAG only for:

- generic housing knowledge
- society-specific documents

Do not store member-private data in vector embeddings.

## Document categories

### Generic housing knowledge
Examples:
- housing bylaws
- visitor policy
- parking rules
- pet policy
- maintenance norms

### Society-specific knowledge
Examples:
- AGM minutes
- circulars
- notices
- maintenance updates
- water outage notices
- lift repair announcements
- vendor information

## Supported file inputs for MVP

- PDF
- TXT
- Markdown

Optional later:
- DOCX
- scanned PDFs with OCR

## Ingestion pipeline

```text
Upload document
-> parse text
-> clean text
-> split into chunks
-> attach metadata
-> generate embeddings
-> store vectors
-> save metadata + ingestion job status
```

## Parsing rules

- Extract readable text from each document
- Preserve page number when possible
- Remove obvious repeated headers/footers if they hurt retrieval
- Keep a copy of original file metadata

## Chunking strategy

Recommended starting configuration:

- chunk size: 500 to 800 tokens
- overlap: 50 to 100 tokens

Chunking goals:

- preserve enough context for policy answers
- avoid extremely small fragments
- avoid giant chunks that hurt retrieval precision

## Metadata schema for each chunk

Each chunk should include at least:

- document_id
- title
- document_type
- source_file
- issue_date
- page_number
- society_name
- applicable_role
- version
- tags

Optional useful fields:

- building_scope
- flat_scope
- validity_start
- validity_end

## Vector storage recommendation

### Local MVP
Use Chroma.

### Later scale-up options
- Pinecone
- Weaviate
- FAISS if kept local and simple

## Retrieval strategy

Use **hybrid retrieval** where possible:

- semantic search
- keyword-aware matching
- metadata filtering

If the first MVP is simpler, start with semantic retrieval + metadata filtering, then add keyword support.

## Retrieval routes

### Public route
Use vector retrieval only.

### Private route
Use SQL only.

### Hybrid route
Use vector retrieval plus SQL.

## Query classification expectations

Classify each query as:

- public
- private
- hybrid
- refused/unsupported

### Examples

Public:
- What are the visitor timings?
- What did the last notice say about parking?

Private:
- What are my dues?
- Show my complaint status.

Hybrid:
- What late fee applies to my unpaid dues?
- Did I miss any notice relevant to my flat?

## Retrieval parameters

Suggested defaults:

- top_k: 4 to 6 chunks
- metadata filters where applicable
- fallback if no relevant chunk found

## Prompt assembly inputs

For public answers, prompt context should include:

- user question
- top retrieved chunks
- citation metadata
- instruction to stay grounded

For hybrid answers, prompt context should include:

- user question
- private SQL summary
- retrieved document chunks
- role context
- refusal rules

## Citation rules

For document-backed answers:

- cite source title
- optionally cite page number if available
- never fabricate citations

For SQL-backed answers:

- do not pretend SQL rows are document citations
- format as personal account information without fake references

## Failure handling

### Weak retrieval
If retrieval is weak:
- return a cautious answer
- say the relevant document could not be confidently found
- avoid hallucination

### Empty retrieval
If no result is found:
- say no relevant document was found
- suggest rephrasing or checking uploaded documents

### Ingestion failure
- mark ingestion job as failed
- store error message
- surface status to admin endpoint

## Document versioning guidance

If a notice or policy is re-uploaded:

- preserve version metadata
- prefer the latest valid version in retrieval
- optionally archive superseded versions

## MVP corpus recommendation

Start with a synthetic corpus such as:

- 1 society handbook
- 5 policy documents
- 10 notices
- 5 AGM/resolution documents
- 5 maintenance/vendor updates

## Coding agent notes

- Keep ingestion scripts separate from API handlers where possible
- Make chunk metadata visible for debugging
- Add local scripts for re-ingestion and reset
- Build retrieval in a way that can later swap vector providers
