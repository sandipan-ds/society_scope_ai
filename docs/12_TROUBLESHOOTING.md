# 12_TROUBLESHOOTING.md

## Purpose

This document records real issues found while building the project, how they
were diagnosed, and how they were fixed. It exists so the same mistakes are
not re-made and so debugging decisions stay visible.

Format per entry: symptom → root cause → fix → lesson.

---

## 2026-07-19 — Query router misclassified private/hybrid chat queries

### Symptom

4 of 18 chat tests failed (`backend/tests/test_chat.py`):

- `Was I fined for wrong parking?` routed to **hybrid** instead of **private**
- `What is my late fee and what rule defines it?` routed to **public** instead of **hybrid**
- `Do my unpaid dues break any payment policy?` routed to **public** instead of **hybrid**
- `Do I have any pending fines?` routed to **public** instead of **private**

Public misroutes were worse than cosmetic: the private flow never ran, so the
user got a document-retrieval answer (or safe fallback) instead of their own
account data.

### Root cause

Three separate weaknesses in `backend/app/chat/router.py`:

1. **Private patterns too strict.** `\bmy\s+(dues?|...)\b` required the account
   keyword directly after "my", so "my *late* fee" and "my *unpaid* dues" did
   not match. `fee` was also missing from the keyword list.
2. **Missing first-person forms.** "Do I have any pending fines?" had no
   matching private pattern at all.
3. **Topical words treated as public intent.** Any public-list word (e.g.
   "parking") in a private question forced the hybrid route, even when the
   word appeared in an account context ("fined for wrong parking").

### Fix

In `backend/app/chat/router.py`:

- Private patterns now allow up to two words between "my" and the keyword:
  `\bmy\s+(\w+\s+){0,2}(dues?|charges?|payments?|fines?|fees?|...|balance)\b`,
  and a first-person pattern was added:
  `\bdo\s+i\s+have\s+(any\s+)?(\w+\s+){0,2}(fines?|dues?|charges?|payments?)\b`.
- The old broad `_PUBLIC_PATTERNS` (topical words like parking, water, lift)
  was replaced by `_STRONG_PUBLIC_PATTERNS` containing only document-seeking
  signals: `policy`, `rule(s)`, `notice(s)`, `circular(s)`, `agm`, `minutes`,
  `handbook`, `timing(s)`, `allowed`, `according to`.
- Routing rule is now: no private signal → public; private + strong public →
  hybrid; private alone → private. Topical-only public questions still reach
  the public route by default, so retrieval behavior is unchanged.

### Verification

- All 61 backend tests pass (`python -m pytest tests/`).
- An 18-case classification matrix (spec examples from
  `docs/05_API_RBAC_SPEC.md` + `docs/08_SYNTHETIC_DATA_AND_TESTS.md`) passes,
  including refusals and the own-flat exception.

### Lesson

Keyword routers need two tiers of intent signals: *topic* words are not
*document-seeking* words. When in doubt, prefer the route with the stricter
security posture (private) and let the public path be the default only when no
private signal exists.

---

## 2026-07-19 — Tests polluted the shared dev database and vector store

### Symptom

While running the new eval harness, the query "What is the lift maintenance
schedule?" returned `'Lift maintenance Friday.'` from a document titled
"Job Check" at 0.260 distance — crowding out the real Lift Maintenance
Notice. `data/uploads/` and the `documents` table held 16 test-created rows
("Job Check", "Test Notice", "Audit Check", "E2E Zebra Notice" × 4 runs).

### Root cause

Two separate leaks:

1. **Tests wrote to shared state without cleanup.** `test_admin.py` and
   `test_ingestion.py` upload documents and trigger ingestion against the
   real seeded DB and persistent Chroma store, and never delete what they
   create. Every test run added another generation of junk chunks.
2. **`DELETE /admin/documents/{id}` left orphan embeddings.** It removed the
   DB row and file but not the vector chunks, so even deleted documents kept
   answering queries.

### Fix

- `admin_routes.delete_document` now also calls
  `vector_store.delete_document_chunks(document_id)` — the store must never
  serve chunks from a document that no longer exists.
- The four polluting tests now delete their uploaded document in a
  `finally` block (which, via the fix above, also removes embeddings).
- One-time purge removed the 16 historical test documents, their files, and
  their chunks. Verified: a full pytest run now leaves the store exactly as
  it found it (12 docs, 64 chunks).

### Lesson

Tests that share a mutable dev environment need an explicit cleanup
contract. "The tests passed" is not enough — check what they leave behind.
Any destructive endpoint must clean up *all* derived artifacts of a resource
(DB row, file, embeddings, jobs), not just the primary row.

---

## 2026-07-19 — Chunk dilution hid the handbook from focused queries

### Symptom

Eval case "What are the gym timings?" was answered from the AGM minutes
("members requested longer gym hours") instead of the Society Handbook,
which actually states gym hours (6 AM–10 PM). Distance ranking showed the
handbook at 0.821 — *farther* than an off-topic junk query (0.762).

### Root cause

Every document was being embedded as exactly one chunk. The handbook covers
seven topics (office, charges, facilities, water, waste, security...), so
its single embedding was a blurry average that matched no focused query
well. Retrieval precision collapsed on the largest, most important document.

### Fix

- `app/ingestion/chunker.py` is now section-aware: markdown
  heading-delimited sections are never merged, so each chunk stays one
  topic. Store rebuilt: 64 topical chunks instead of 12 monolithic ones.
- Composer now scores sentences across ALL retrieved chunks (not just the
  nearest 1–2) with prefix-stem matching ("lift" ↔ "lifts").
- `MAX_DISTANCE` re-measured on the new profile: on-topic queries land at
  ~0.33–0.72, off-topic at ~0.73+; threshold set to 0.73 (was 0.65, then
  0.75 which broke the fallback). `data/eval_queries` guards this boundary.

### Verification

- Eval: 70/70 (public 20/20 incl. fallback case, private 20/20,
  unauthorized 20/20, hybrid 10/10).
- Pytest: 61/61.

### Lesson

Embedding quality problems are often chunking problems. Measure the
distance distribution of good vs junk queries before and after changing
chunk size or boundaries — and keep a permanent eval set so threshold tuning
is evidence, not guesswork.

---

## 2026-07-19 — Corpus growth silently shifted the retrieval threshold

### Symptom

After ingesting the Maharashtra Co-operative Societies Act (358 new chunks,
6× corpus growth), the junk-query fallback case (`pub-19`, "lunar mining
rights") started returning an answer with citations instead of the
safe-fallback message. Every substantive eval case still passed — the ONLY
signal was the fallback regression.

### Root cause

`MAX_DISTANCE` is an absolute threshold over a moving target. The Act's
legal prose ("rights", "policy"-adjacent language) gave the junk query a
closest match of 0.674 — under the then-current 0.73 threshold. Thresholds
tuned on one corpus do not transfer to a bigger corpus.

### Fix

Re-measured the best-chunk distance for every public/hybrid eval query on
the new corpus: answerable queries land at ≤ 0.599, the junk query at
≥ 0.674 — a 0.075 gap. Set `MAX_DISTANCE = 0.64` (mid-gap) and expanded the
eval set with 3 Act-based cases so the new corpus has its own coverage.

### Verification

- Eval: 73/73 with the full 422-chunk corpus. Pytest: 61/61.
- Act questions answer from real provisions with citations (e.g. member
  expulsion → three-fourths majority at a general meeting).

### Lesson

Any absolute retrieval threshold must be re-measured on corpus, chunking,
or embedding-model change. The workflow is now established and cheap:
ingest → measure best-distances for eval queries → pick mid-gap → re-run
`scripts/run_eval.py`. The eval set is what makes a one-number change safe.

---

## 2026-07-22 — Switched private data layer from SQLite to Excel workbook

### Symptom

The project direction changed: residents and their financial data should be
maintained in the existing `Housing_Society_Charges_and_Fines_Template_108_Residents.xlsx`
workbook instead of `database/society.db`. The backend needed to keep working
without requiring users to run SQL scripts or database seeds.

### Root cause

The original MVP used SQLAlchemy + SQLite for residents, charges, and fines,
with an Excel workbook only as an editing bridge. The new direction makes the
workbook the runtime source of truth, matching the documented architecture.

### Fix

- Added `backend/app/workbook/store.py` — mtime-cached reader for the workbook;
  exposes residents, monthly charges, fines, payments, and user resolution.
- Added `backend/app/statestore.py` — JSON-backed stores for users, documents,
  ingestion jobs, and audit logs (app-managed, not member-edited).
- Added `scripts/normalize_workbook.py` to add formula-driven `Maintenance Charges`
  and a zero-filled `Payments` sheet.
- Added `scripts/migrate_to_statestore.py` to one-off migrate admin accounts,
  document metadata, ingestion jobs, and audit logs from the legacy SQLite DB.
- Rewired auth, `/me/*`, chat private/hybrid flows, admin routes, and the
  ingestion pipeline to use the workbook + state store.
- Updated `backend/app/chat/router.py` to recognize plain 3-4 digit flat numbers
  (e.g. "flat 101", "flat 302") instead of wing-prefixed patterns.
- Updated tests and the 73-case eval set to use real workbook emails and flat
  numbers, and adjusted expected financial figures to the template data.

### Verification

- `python -m pytest tests/` → 60/60 passing.
- `python scripts/run_eval.py --quiet` → 73/73 passing.
- `/health/data` reports workbook + state store reachable.

### Lesson

When the source of truth changes, migrate metadata you need to keep
(documents, jobs, audit logs, admin users) but do not migrate resident data
that now belongs in the new source of truth. Keep the old files on disk until
migration is verified, then archive them.
