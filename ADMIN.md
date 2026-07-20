# Admin Guide — Society Scope AI

Everything an admin (committee) user needs: how to log in, what your token unlocks, and how to use every `/admin/*` endpoint.

---

## Who is an admin?

Admin accounts represent the society committee (chairperson, secretary). They manage society documents and monitor the system — they do **not** have a household account.

| Account | Role | Linked flat |
|---|---|---|
| `admin1@society.in` | admin | none |
| `admin2@society.in` | admin | none |

**Password (dev placeholder):** `replace-on-first-login`

> ⚠️ Works only while `ALLOW_DEV_PASSWORD_PLACEHOLDERS=true` in `backend/.env`. Real deployments use per-user passwords stored as bcrypt hashes.

---

## Step 0 — Start the backend

```powershell
# From the repo root
python scripts/build_database.py --reset    # only if DB isn't built yet
python -m pip install -r backend/requirements.txt

Set-Location backend
python -m uvicorn app.main:app --reload --port 8000
```

Verify it's up:

```powershell
Invoke-RestMethod http://localhost:8000/health
# => @{ status=ok; app=Society Scope AI; ... }
```

---

## Step 1 — Log in as admin

### Option A — PowerShell (recommended for scripting)

```powershell
$login = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" `
  -Method Post -ContentType "application/json" `
  -Body '{"email":"admin1@society.in","password":"replace-on-first-login"}'

$token   = $login.access_token
$headers = @{ Authorization = "Bearer $token" }

$login.roles    # => admin
```

### Option B — curl

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin1@society.in","password":"replace-on-first-login"}'
```

### Option C — Browser (no terminal)

Open `demo-login.html` in the repo root, pick `admin1@society.in`, click **Sign in**.

### Login response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "roles": ["admin"]
}
```

The token expires after **60 minutes** (configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`). When it expires, log in again.

### What the token contains

```text
{
  "sub":   "admin1@society.in",     ← who you are
  "roles": ["admin"],               ← what you're allowed to do
  "iat":   ...,                     ← issued at
  "exp":   ...                      ← expires at
}
```

Every `/admin/*` endpoint re-validates this token and re-checks the role on **every request** — there is no session to hijack server-side.

---

## Step 2 — Confirm your identity

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/auth/me" -Headers $headers
```

```json
{ "user_id": 1, "email": "admin1@society.in", "roles": ["admin"], "flat_no": null }
```

`flat_no: null` is correct — admins are not residents.

---

## Step 3 — Use the admin endpoints

All examples assume `$headers` from Step 1.

### 3.1 List all documents

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/admin/documents" -Headers $headers
```

Returns every document's metadata (12 seeded rows: handbook, policies, notices, AGM minutes), newest first.

### 3.2 Upload a document

Accepted types: `.pdf`, `.txt`, `.md` · Categories: `notice`, `policy`, `agm_minutes`, `circular`

```powershell
# Create a sample file first
Set-Content -Path ".\water_notice.txt" -Value "Water supply will be off on Tuesday 9 AM - 1 PM for tank cleaning."

$form = @{
  file          = Get-Item ".\water_notice.txt"
  title         = "Water Supply Notice - Tuesday"
  document_type = "notice"
  issue_date    = "2026-07-19"
}

Invoke-RestMethod -Uri "http://localhost:8000/admin/documents/upload" `
  -Method Post -Headers $headers -Form $form
```

Response (`201 Created`):

```json
{
  "id": 13,
  "title": "Water Supply Notice - Tuesday",
  "document_type": "notice",
  "file_name": "13.txt",
  "issue_date": "2026-07-19",
  "uploaded_by": 1
}
```

What happens behind the scenes:

1. File saved to `data/uploads/13.txt` (named by document id)
2. Row added to the `documents` table
3. A `pending` ingestion job created automatically
4. An `upload_document` entry written to `audit_logs` with your user id

### 3.3 Check ingestion job status

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/admin/ingestion-jobs" -Headers $headers
```

```json
[
  {
    "id": 1,
    "document_id": 13,
    "status": "pending",
    "error_message": null,
    "started_at": null,
    "finished_at": null,
    "created_at": "2026-07-19T10:30:00"
  }
]
```

Statuses: `pending` → `processing` → `completed` | `failed`.

### 3.3b Run ingestion

Uploading only stores the file — it becomes searchable after ingestion:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/admin/documents/ingest" `
  -Method Post -Headers $headers
```

This processes every `pending` job: extract text → clean → chunk → embed → store in the local Chroma vector store (`data/chroma/`). The response lists the processed jobs with their final status; failures include an `error_message`. From then on, the document's chunks are retrievable for public Q&A.

### 3.4 View the audit trail

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/admin/audit-logs" -Headers $headers

# Or limit the number of rows (1-500, default 100)
Invoke-RestMethod -Uri "http://localhost:8000/admin/audit-logs?limit=20" -Headers $headers
```

Events you'll see:

| action | meaning |
|---|---|
| `login_success` / `login_failure` | authentication attempts |
| `register` | new resident self-registration |
| `me_view` | someone called `/auth/me` |
| `query_private` | a resident viewed their dues/payments/fines/profile, or asked a private/hybrid chat question |
| `query_public` | a public chat question was answered from documents |
| `upload_document` | an admin uploaded a document |
| `delete_document` | an admin deleted a document |
| `ingest_trigger` / `ingestion_job` | ingestion batch triggered / individual job finished |
| `access_denied` | refused private-data access (e.g. another resident's dues, or anonymous private query) |

### 3.5 Delete a document

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/admin/documents/13" `
  -Method Delete -Headers $headers
# => 204 No Content
```

Removes the DB row **and** the stored file from `data/uploads/`. Logged as `delete_document`.

---

## What admins canNOT do (by design)

| Action | Result | Why |
|---|---|---|
| `GET /me/dues` etc. | `404` | Admins have no linked resident profile — they aren't a household |
| Ask the assistant for a resident's dues | refused | Per RBAC spec, MVP admins get **no open-ended access to private resident data** |
| See resident passwords | impossible | Only bcrypt hashes are stored |

If a real committee workflow needs resident-account visibility later, it must be added as an explicit, policy-scoped feature — not assumed.

---

## Errors you'll hit and what they mean

| Status | When | Fix |
|---|---|---|
| `401 Unauthorized` | No token, expired token, or malformed token | Log in again (tokens last 60 min) |
| `403 Forbidden` | Logged in as a **resident**, calling `/admin/*` | Use an admin account |
| `404 Not Found` | Document id doesn't exist | Check `GET /admin/documents` for valid ids |
| `422 Validation error` | Bad file extension, bad `document_type`, missing form field | Only `.pdf/.txt/.md`; type must be `notice/policy/agm_minutes/circular` |

---

## Quick end-to-end admin demo script

```powershell
Set-Location backend

# 1. Login
$login = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" `
  -Method Post -ContentType "application/json" `
  -Body '{"email":"admin1@society.in","password":"replace-on-first-login"}'
$headers = @{ Authorization = "Bearer $($login.access_token)" }

# 2. Who am I?
Invoke-RestMethod -Uri "http://localhost:8000/auth/me" -Headers $headers

# 3. Upload a notice
Set-Content -Path ".\demo_notice.txt" -Value "Elevator maintenance on Friday 10 AM."
$form = @{ file = Get-Item ".\demo_notice.txt"; title = "Elevator Maintenance"; document_type = "notice"; issue_date = "2026-07-19" }
Invoke-RestMethod -Uri "http://localhost:8000/admin/documents/upload" -Method Post -Headers $headers -Form $form

# 4. Check the job was created
Invoke-RestMethod -Uri "http://localhost:8000/admin/ingestion-jobs" -Headers $headers | Select-Object -First 1

# 5. See yourself in the audit trail
Invoke-RestMethod -Uri "http://localhost:8000/admin/audit-logs?limit=5" -Headers $headers
```

---

## Security notes for admins

- The JWT secret lives in `backend/.env` (`JWT_SECRET_KEY`). Change it before any real deployment.
- Tokens are bearer tokens — anyone holding one can act as you until it expires. Don't paste them into chats, tickets, or screenshots.
- Every sensitive action you take (uploads, deletions, logins) is recorded in `audit_logs` with your user id.
- The demo HTML page (`demo-login.html`) discards your token when you click **Sign out**; the API itself has no logout — tokens simply expire.
