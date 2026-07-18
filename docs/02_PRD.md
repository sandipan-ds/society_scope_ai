# Product Requirements Document (PRD)

## Project name

Housing Society AI Assistant

## Problem statement

Housing society residents often struggle to find accurate and timely information about rules, notices, dues, and past decisions. Traditional communication channels such as PDFs, circulars, notice boards, and spreadsheets are fragmented and hard to search. This project solves that problem with a secure AI assistant that answers both public and private questions while respecting access control.

## Product goal

Build a secure assistant that:

- answers society-related public questions from documents
- answers resident-specific private questions from SQL data
- refuses unauthorized access to private information
- provides source-backed answers for document-based responses

## Target users

- Residents
- Committee/Admin users
- Security or support staff (optional in MVP)
- Demo evaluators such as recruiters, mentors, or judges

## User roles

### Resident
Can ask public questions and see only their own private data.

### Admin
Can manage documents, ingestion jobs, and view broader operational information depending on policy.

### Security/Staff (optional MVP role)
Can access visitor-related operational information only.

## Core user stories

### Public information
- As a resident, I want to ask about visitor timings, parking rules, pet rules, and notices.
- As a user, I want the answer to cite the relevant document.

### Private information
- As a resident, I want to ask for my outstanding dues.
- As a resident, I want to see my payment history.
- As a resident, I want to view my own complaints and status.

### Admin workflows
- As an admin, I want to upload notices and society documents.
- As an admin, I want to trigger ingestion and see ingestion status.
- As an admin, I want visibility into audit logs for private-data access.

### Unauthorized access handling
- As a resident, if I ask for another resident's dues, the system should refuse.
- As an anonymous user, I should not access any member-specific information.

## MVP scope

Included in MVP:

- Login and JWT auth
- RBAC enforcement
- SQL storage for resident-private data
- Vector retrieval for public/society documents
- Document ingestion pipeline
- Chat endpoint with routing logic
- Public cited answers
- Private resident-specific answers
- Unauthorized access refusal
- Basic audit logging

## Out of scope for MVP

- Multi-language support
- Voice interface
- Native mobile app
- Payments integration
- Real ERP integration
- OCR-heavy scanned document workflows beyond simple support

## Functional requirements

### Authentication and access
- Users must log in to access private data
- JWT must be validated on protected routes
- Role permissions must be enforced at API and query layers

### Public Q&A
- System must retrieve relevant society/public documents
- System must answer using retrieved context only
- System should cite source documents in the response

### Private Q&A
- System must fetch resident-specific structured data from SQL
- System must restrict data to the authenticated user unless role policy allows otherwise

### Hybrid Q&A
- System should support questions needing both document and SQL context
- Example: payment due date plus related society penalty rule

### Ingestion
- Admin should upload PDFs or text documents
- System should parse, chunk, embed, and index documents with metadata

### Logging
- System must log authentication events, private-data query attempts, and ingestion jobs

## Non-functional requirements

- Secure by default
- Clear separation of public and private data
- Explainable/cited responses for documents
- Easy local setup for student development
- Modular enough for future deployment

## Success criteria

The MVP is successful if it can demonstrate:

- secure login
- resident-only access to private data
- cited retrieval for public notices
- clear refusal for unauthorized questions
- local demo with seeded synthetic data

## Example demo questions

### Public
- What are the visitor timings?
- What is the pet policy?
- Was there any water outage notice this week?

### Private
- What are my outstanding maintenance dues?
- Show my payment history.
- What is the status of my complaint?

### Unauthorized
- What are my neighbor's dues?
- Show payment history for flat B-302.

## Risks

- Hallucinated answers when retrieval is weak
- Overexposure of private data if RBAC is poorly enforced
- Poor ingestion quality from badly formatted PDFs
- Weak demo if data is too small or unrealistic

## MVP completion checklist

- Product flows defined
- Roles defined
- Protected private data flows implemented
- Document ingestion implemented
- Query routing implemented
- Demo data prepared
- Test cases passing
- Deployment path documented
