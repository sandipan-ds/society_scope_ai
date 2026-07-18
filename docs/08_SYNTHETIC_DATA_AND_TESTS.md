# Synthetic Data and Test Specification

## Purpose

This document defines the synthetic data needed for local development and the baseline test scenarios for validating the MVP.

## Why synthetic data is needed

Real housing society data is private and often unavailable. A strong student MVP can and should start with realistic synthetic data that mirrors actual product structure.

## Synthetic SQL data plan

### Suggested initial scale

- 50 users
- 50 residents
- 3 roles
- 100 flats
- 6 months of maintenance dues
- 6 months of payment history
- 50 to 60 complaints
- 80 registered vehicles

## SQL seed entities

### Users
Fields:
- email
- password_hash
- active status
- created_at

### Roles
Values:
- resident
- admin
- staff

### Residents
Fields:
- full_name
- linked user
- flat
- occupancy_status
- phone

### Flats
Fields:
- building_code
- flat_number
- floor
- parking_slot

### Maintenance dues
Fields:
- resident_id
- billing_month
- amount_due
- late_fee
- due_date
- status

### Payments
Fields:
- resident_id
- amount_paid
- payment_date
- payment_method
- transaction_ref
- status

### Complaints
Fields:
- resident_id
- category
- title
- description
- status

### Vehicles
Fields:
- resident_id
- vehicle_type
- plate_number
- sticker_id

## Synthetic document corpus plan

Create a local folder such as `data/sample_docs/` with documents like:

- `society_handbook.pdf`
- `visitor_policy.pdf`
- `parking_policy.pdf`
- `pet_policy.pdf`
- `agm_minutes_jan.md`
- `agm_minutes_apr.md`
- `water_outage_notice_may.md`
- `lift_maintenance_notice_june.md`
- `festival_event_circular.md`
- `vendor_contact_notice.md`
- `maintenance_due_reminder_july.md`
- `waste_segregation_policy.md`

## Recommended synthetic document categories

- 1 handbook
- 4 to 5 policy docs
- 8 to 10 notices
- 3 to 5 AGM/resolution docs
- 2 to 3 maintenance/vendor updates

## Synthetic content design rules

- Use realistic dates
- Include role-neutral public rules
- Include some updated notices that supersede older ones
- Include building names and flat references only if needed for demo metadata
- Avoid storing private resident account values in document text

## Example test user accounts

### Resident account
- email: resident1@example.com
- role: resident
- flat: A-101

### Admin account
- email: admin1@example.com
- role: admin

### Staff account
- email: staff1@example.com
- role: staff

## Baseline test scenarios

### Authentication tests
- User can register
- User can log in with valid credentials
- Invalid credentials are rejected
- Protected endpoint rejects missing token

### Public retrieval tests
- Visitor timings question returns a document-backed answer
- Parking policy question returns a cited answer
- Unknown public question returns safe fallback

### Private SQL tests
- Resident can fetch own dues
- Resident can fetch own payments
- Resident can fetch own complaints
- Resident cannot fetch another resident's records

### Hybrid tests
- Resident asks for late fee and related rule
- System uses SQL for the account fact and RAG for the policy explanation

### Refusal tests
- Resident asks for neighbor's dues -> refused
- Resident asks for another flat's payment history -> refused
- Anonymous user asks for private info -> rejected or refused

### Admin ingestion tests
- Admin uploads a document
- Ingestion job status is visible
- Failed ingestion is recorded

### Logging tests
- Login attempt creates log event
- Private query creates audit event
- Refusal creates denial log

## Evaluation query set recommendation

Prepare a local evaluation file in `data/eval_queries/` with:

- 20 public queries
- 20 private authorized queries
- 20 unauthorized private queries
- 10 hybrid queries

## Acceptance criteria for a strong MVP

- seeded local demo works end-to-end
- public answers use retrieved documents
- private answers are restricted to authenticated owner
- unauthorized requests are denied consistently
- ingestion is repeatable
- logs exist for important events

## Coding agent notes

- Create seed scripts for both SQL rows and sample documents
- Make seed generation deterministic where possible
- Keep example credentials clearly documented for demo use
- Add tests that match the scenarios listed above
