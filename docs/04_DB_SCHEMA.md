# Database Schema (Simplified MVP)

## Purpose

This version of the schema is intentionally simple.

It is designed for a single housing society MVP where the main needs are:

- store flat number and resident details
- track monthly society charges as paid or unpaid
- track fines such as wrong parking or rule violations
- support login for residents/admins
- support RAG documents separately from private resident data

For this project, **simple and practical is better than over-engineered**.

## Society scale assumption

Example scale:

- 19 storeys
- ground floor excluded from flats
- 6 flats per floor
- about **108 flats** total

This scale does **not** need a complex enterprise schema.

## Important design choice

Do **not** store months like `jan`, `feb`, `mar` as separate database columns.

That style works in Excel, but it becomes messy in an app because:

- it is hard to support multiple years
- it is hard to query unpaid months cleanly
- it is hard to track exact paid dates and amounts
- it becomes awkward for reports and analytics

Instead, store **one row per flat/resident per month**.

## Recommended minimal tables

### 1. users

Use this table only if you want login.

| Column | Type | Notes |
|---|---|---|
| id | UUID / SERIAL | Primary key |
| email | VARCHAR | Unique login email |
| password_hash | TEXT | Hashed password |
| role | VARCHAR | `resident` or `admin` |
| resident_id | FK -> residents.id, nullable | Linked resident for resident users |
| is_active | BOOLEAN | Active/inactive account |
| created_at | TIMESTAMP | Audit field |

**Why it exists:**
- supports JWT login
- separates authentication from resident profile data

---

### 2. residents

Main resident master table.

| Column | Type | Notes |
|---|---|---|
| id | UUID / SERIAL | Primary key |
| flat_no | VARCHAR | Example: `A-101` |
| resident_name | VARCHAR | Primary resident name |
| phone | VARCHAR | Contact number |
| email | VARCHAR | Contact email |
| is_owner | BOOLEAN | Owner or tenant flag |
| is_active | BOOLEAN | Current resident status |
| created_at | TIMESTAMP | Audit field |
| updated_at | TIMESTAMP | Audit field |

**Why it exists:**
- stores the core flat + person information
- easy for admin view and resident linking

**Example row:**

| flat_no | resident_name | phone | email |
|---|---|---|---|
| A-101 | Amit Sharma | 9876543210 | amit@example.com |

---

### 3. monthly_charges

Tracks society maintenance/charges month by month.

| Column | Type | Notes |
|---|---|---|
| id | UUID / SERIAL | Primary key |
| resident_id | FK -> residents.id | Linked resident |
| charge_year | INTEGER | Example: `2026` |
| charge_month | VARCHAR | Example: `jan`, `feb`, `mar` |
| amount | NUMERIC | Society charge amount |
| status | VARCHAR | `paid`, `unpaid`, `partial` |
| paid_date | DATE, nullable | Filled if paid |
| remarks | TEXT, nullable | Optional note |
| created_at | TIMESTAMP | Audit field |

**Why it exists:**
- lets you ask questions like:
  - which months are unpaid?
  - how much is due this year?
  - when was March paid?
- works across multiple years without changing schema

**Example rows:**

| resident_id | charge_year | charge_month | amount | status | paid_date |
|---|---|---|---|---|---|
| 1 | 2026 | jan | 2500 | paid | 2026-01-05 |
| 1 | 2026 | feb | 2500 | unpaid | null |
| 1 | 2026 | mar | 2500 | paid | 2026-03-07 |

---

### 4. fines

Tracks fines such as wrong parking, late fee, or other rule violations.

| Column | Type | Notes |
|---|---|---|
| id | UUID / SERIAL | Primary key |
| resident_id | FK -> residents.id | Linked resident |
| fine_type | VARCHAR | `wrong_parking`, `late_fee`, `damage`, `other` |
| description | TEXT | Reason for fine |
| amount | NUMERIC | Fine amount |
| fine_date | DATE | Date issued |
| status | VARCHAR | `paid`, `unpaid`, `waived` |
| remarks | TEXT, nullable | Optional note |
| created_at | TIMESTAMP | Audit field |

**Why it exists:**
- separate sheet/table for penalty records
- one resident can have zero, one, or many fines

**Example rows:**

| resident_id | fine_type | description | amount | fine_date | status |
|---|---|---|---|---|---|
| 1 | wrong_parking | Parked in visitor slot | 500 | 2026-07-05 | unpaid |
| 1 | late_fee | Late payment charge for February | 200 | 2026-02-15 | paid |

---

### 5. documents

Stores metadata for society documents used by the RAG system.

| Column | Type | Notes |
|---|---|---|
| id | UUID / SERIAL | Primary key |
| title | VARCHAR | Document title |
| document_type | VARCHAR | `notice`, `policy`, `agm_minutes`, `circular` |
| file_name | VARCHAR | Stored file name |
| issue_date | DATE | Notice/policy date |
| uploaded_by | FK -> users.id, nullable | Admin uploader |
| created_at | TIMESTAMP | Audit field |

**Why it exists:**
- keeps track of uploaded notice/policy files
- actual chunks/embeddings live in the vector store, not in this table

---

### 6. audit_logs (optional but recommended)

Useful if you want the project to look stronger and more secure.

| Column | Type | Notes |
|---|---|---|
| id | UUID / SERIAL | Primary key |
| user_id | FK -> users.id, nullable | Actor |
| action | VARCHAR | Example: `login`, `query_private`, `upload_document`, `access_denied` |
| details | TEXT | Short event description |
| created_at | TIMESTAMP | Event timestamp |

**Why it exists:**
- useful for debugging
- useful for admin visibility
- useful for demonstrating secure access tracking on a resume

## Relationships

```text
residents 1--* monthly_charges
residents 1--* fines
residents 1--0..1 users
users 1--* documents
users 1--* audit_logs
```

## What the app can answer from this schema

### Private SQL questions

- What is my flat number?
- What is my phone/email on record?
- Which months are unpaid?
- How much society charge did I pay in March?
- Do I have any pending fine?
- Was I fined for wrong parking?

### Public/RAG questions

- What are the visitor timings?
- What is the parking policy?
- What did the latest notice say?
- What are the society rules for pets?

## Best fit with your current sheets

If you already think in spreadsheet form, map them like this:

### Sheet 1: Resident + monthly payment data
Can be split into:
- `residents`
- `monthly_charges`

### Sheet 2: Fine / wrong parking data
Can be stored in:
- `fines`

### Society notices / PDFs
Can be stored as:
- `documents` metadata + vector store chunks

## Suggested seed size for local demo

For a solid MVP demo, you can seed:

- 108 resident records max if you want full-building realism
- 12 months of charges per resident
- 10 to 30 fine records
- 10 to 20 society documents
- 2 to 5 admin accounts

## Simplest possible MVP version

If you want the smallest working version, use only these tables:

1. `users`
2. `residents`
3. `monthly_charges`
4. `fines`
5. `documents`

Add `audit_logs` after that.

## Example SQL-style model summary

```text
users
- id
- email
- password_hash
- role
- resident_id
- is_active
- created_at

residents
- id
- flat_no
- resident_name
- phone
- email
- is_owner
- is_active
- created_at
- updated_at

monthly_charges
- id
- resident_id
- charge_year
- charge_month
- amount
- status
- paid_date
- remarks
- created_at

fines
- id
- resident_id
- fine_type
- description
- amount
- fine_date
- status
- remarks
- created_at

documents
- id
- title
- document_type
- file_name
- issue_date
- uploaded_by
- created_at

audit_logs
- id
- user_id
- action
- details
- created_at
```

## Recommendation

For this project, this simplified schema is the right starting point.

It is:

- easy to understand
- easy to seed with synthetic data
- easy to connect with login + RAG
- strong enough for an MVP and resume project
- much better than overcomplicating the database too early
