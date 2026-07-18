# API and RBAC Specification

## Purpose

This document defines:

- user roles and permissions
- protected API behavior
- endpoint contracts
- refusal and unauthorized access policy

## Roles

### Resident
Can access public information and their own private records only.

### Admin
Can manage documents, ingestion, and operational views according to policy.

### Staff (optional MVP)
Can access limited operational or visitor-related information only.

## Core RBAC rules

### Resident permissions
Allowed:

- ask public document questions
- ask for own dues
- ask for own payment history
- ask for own complaints
- ask for own profile data

Denied:

- another resident's dues
- another resident's payments
- another resident's complaint history
- raw audit logs
- admin ingestion controls

### Admin permissions
Allowed:

- upload documents
- trigger ingestion
- view ingestion status
- view audit logs
- view operational query logs
- ask public questions

Admin access to private resident data should be explicit and policy-scoped, not assumed. For MVP, prefer **no open-ended admin access to all private resident data through chat** unless a specific business rule is implemented.

### Staff permissions
Allowed only if implemented:

- view public notices
- view visitor-related policies
- validate operational info allowed by policy

Denied:

- dues
- payments
- complaint internals unless explicitly allowed

## Protected routes

Any endpoint returning private resident data must require a valid JWT.

## Authentication endpoints

### POST /auth/register
Creates a user account for local/demo usage.

Request body:

```json
{
  "email": "resident1@example.com",
  "password": "StrongPassword123",
  "full_name": "Demo Resident"
}
```

Response:

```json
{
  "message": "User registered successfully"
}
```

### POST /auth/login
Returns access token and role context.

Request body:

```json
{
  "email": "resident1@example.com",
  "password": "StrongPassword123"
}
```

Response:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "roles": ["resident"]
}
```

### GET /auth/me
Returns current authenticated user.

Auth required: yes

Response:

```json
{
  "user_id": "uuid",
  "email": "resident1@example.com",
  "roles": ["resident"]
}
```

## Chat endpoint

### POST /chat/query
Primary question-answering endpoint.

Auth required:
- optional for public-only usage
- required for private or hybrid usage

Request body:

```json
{
  "query": "What are my outstanding dues?",
  "session_id": "demo-session-1"
}
```

Response shape:

```json
{
  "route_type": "private",
  "answer": "Your outstanding dues for July 2026 are AUD 2,500.",
  "citations": [],
  "refused": false
}
```

Public response shape:

```json
{
  "route_type": "public",
  "answer": "Visitor timings are 8 AM to 10 PM.",
  "citations": [
    {
      "title": "Visitor Policy Notice",
      "document_id": "doc-123"
    }
  ],
  "refused": false
}
```

Refusal response shape:

```json
{
  "route_type": "refused",
  "answer": "I can't help with another resident's private account information.",
  "citations": [],
  "refused": true
}
```

## Resident self-service endpoints

### GET /me/profile
Returns authenticated resident profile.

### GET /me/dues
Returns dues for authenticated resident.

### GET /me/payments
Returns payment history for authenticated resident.

### GET /me/complaints
Returns complaint history for authenticated resident.

### GET /me/vehicles
Returns registered vehicles for authenticated resident.

All `/me/*` endpoints require JWT and must be scoped to the authenticated resident only.

## Admin endpoints

### POST /admin/documents/upload
Uploads a document for ingestion.

### POST /admin/documents/ingest
Triggers or confirms ingestion.

### GET /admin/ingestion-jobs
Returns ingestion job status.

### GET /admin/audit-logs
Returns audit log summaries.

### GET /admin/query-logs
Returns query log summaries.

All `/admin/*` endpoints require admin role.

## Query-time RBAC behavior

The API layer alone is not enough. The chat orchestration layer must also enforce RBAC.

### Examples

Allowed:
- "What are my dues?" from logged-in resident
- "Show my payment history" from logged-in resident
- "What is the visitor policy?" from any public user

Denied:
- "Show dues for flat B-302" from resident
- "How much does my neighbor owe?" from resident
- "Show payment details of resident ID 18" from resident or staff

## Refusal policy

When access is denied:

- do not reveal whether detailed hidden data exists
- do not guess or summarize restricted data
- return a clear refusal message
- create an audit log entry

## Error policy

### 401 Unauthorized
No valid token for protected access.

### 403 Forbidden
Authenticated but not permitted for this operation.

### 404 Not found
Requested self-resource not found.

### 422 Validation error
Invalid request payload.

### 500 Internal server error
Unexpected server-side issue.

## Audit expectations

Create audit events for:

- login success/failure
- protected query access
- refusal / denied private access attempt
- document upload
- ingestion start/finish/failure

## MVP implementation notes

- Start with route-level role decorators/dependencies
- Add resident scoping in service layer, not just controller layer
- Keep chat RBAC logic explicit and testable
- Prefer simple, deterministic refusal messages over clever LLM phrasing
