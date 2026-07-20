# User Guide — Society Scope AI

A practical, step-by-step guide to logging in and using the demo MVP.

> **Admin (committee) user?** See **[ADMIN.md](ADMIN.md)** for the full admin walkthrough — document upload, ingestion jobs, and audit logs.

---

## What this system does

Society Scope AI is a secure hybrid assistant for a housing society. It answers:

- **Public questions** from society notices, policies, AGM minutes, and circulars (RAG over documents)
- **Private questions** from your own resident account data — dues, fines, profile (SQL lookup)

Access is role-based:
- **Residents** can see only their own private data
- **Admins** (committee: chairperson / secretary) can also upload documents, trigger ingestion, and view audit logs
- **Staff** (optional) sees only public notices + visitor policies

---

## Quickstart — run the backend + open the demo login page

### 1. Make sure the database is built and seeded

```powershell
python scripts/build_database.py --reset
```

This creates `database/society.db` with 108 flats, 12 demo login users, charges, fines, and document metadata.

### 2. Install backend dependencies

```powershell
python -m pip install -r backend/requirements.txt
```

### 3. Set up environment

```powershell
Copy-Item backend\.env.example backend\.env
```

The defaults work for local development. Important dev-only flag: `ALLOW_DEV_PASSWORD_PLACEHOLDERS=true` — this lets you log in with the placeholder password below.

### 4. Start the backend

```powershell
Set-Location backend
python -m uvicorn app.main:app --reload --port 8000
```

You should see: `Uvicorn running on http://127.0.0.1:8000`.

### 5. Open the demo console page

In another terminal / your file browser, open:

```
C:\Users\sandi\Desktop\ML Working Folder\society_scope_ai\demo-login.html
```

in any browser (Edge, Chrome, Firefox — just double-click the file).

The page has two panels: **Sign in** (left) and **Chat** (right).

### 6. Log in

Pick any of the demo accounts below, type the password, click **Sign in**. Residents also get an account summary (outstanding dues + unpaid fines) loaded automatically.

### 7. Chat

Use the chat panel on the right — signed in or not:

- **Public questions** work anonymously: "What are the visitor timings?" — answers include source citations.
- **Private questions** need a resident login: "What are my outstanding dues?" — answers come from your own SQL records only.
- **Hybrid questions** combine both: "What is my late fee and what rule defines it?"
- **Refusals** are shown in red: try "Show my neighbor's dues" — the request is denied and audit-logged.

The colored badge above each answer shows which route the query took (`public` / `private` / `hybrid` / `refused`).

---

## Demo credentials

| Role | Email | Linked flat |
|---|---|---|
| **Admin** | `admin1@society.in` | — |
| **Admin** | `admin2@society.in` | — |
| **Resident** | `resident1@society.in` | A-101 |
| **Resident** | `resident2@society.in` | A-202 |
| **Resident** | `resident3@society.in` | A-304 |
| **Resident** | `resident4@society.in` | A-405 |
| **Resident** | `resident5@society.in` | B-101 |
| **Resident** | `resident6@society.in` | B-203 |
| **Resident** | `resident7@society.in` | B-306 |
| **Resident** | `resident8@society.in` | B-404 |
| **Resident** | `resident9@society.in` | A-505 |
| **Resident** | `resident10@society.in` | B-606 |

**Password for every account above**: `replace-on-first-login`

> ⚠️ This is a **dev-only placeholder**. When real authentication is wired, each user will have their own unique password. The placeholder works only because `ALLOW_DEV_PASSWORD_PLACEHOLDERS=true` in `backend/.env`.

Each **resident** account is linked to exactly one flat — and that link is what the `/me/*` endpoints use to decide which data you can see. Admins have no flat link (they manage the society, not a household). See "Resident self-service endpoints" below for the per-account data breakdown.

---

## What each role can do

| Action | Resident | Admin | Staff |
|---|---|---|---|
| Ask public questions (visitor timings, pet policy, etc.) | ✔ | ✔ | ✔ |
| View **own** monthly charges / dues | ✔ | — | — |
| View **own** fines | ✔ | — | — |
| View **own** profile (flat, phone, email) | ✔ | — | — |
| View **another resident's** dues or fines | ✘ refused | ✘ refused | ✘ refused |
| Upload documents | — | ✔ | — |
| Trigger ingestion | — | ✔ | — |
| View audit logs | — | ✔ | — |
| View query logs | — | ✔ | — |

> "Committee member" is modeled as **admin** in this MVP. If you want a separate `committee` role with narrower permissions than admin, that requires a one-line change to the role enum.

---

## Login flow — how it works

```text
Browser / CLI
   │
   │  POST /auth/login  { "email": "...", "password": "..." }
   ▼
FastAPI backend
   │
   ├── verify_password() ── bcrypt hash check (or DEV placeholder in dev mode)
   ├── create_access_token() ── signed JWT with email + roles
   │
   ▼
Returns { access_token, token_type: "bearer", roles: [...] }
   │
   │  Client stores the token (in memory for the demo page).
   │
   │  GET /auth/me  with header  Authorization: Bearer <token>
   ▼
Backend resolves token → looks up user → returns profile + flat
```

The JWT is **signed** with `JWT_SECRET_KEY` from `backend/.env`. In production, change this to a long random string.

---

## Using the API directly (curl / PowerShell)

### Login

```powershell
$resp = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" `
  -Method Post -ContentType "application/json" `
  -Body '{"email":"resident1@society.in","password":"replace-on-first-login"}'

$token = $resp.access_token
$token
```

### Fetch your profile

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/auth/me" `
  -Headers @{ Authorization = "Bearer $token" }
```

Expected response:

```json
{
  "user_id": 3,
  "email": "resident1@society.in",
  "roles": ["resident"],
  "flat_no": "A-101"
}
```

### Resident self-service endpoints

Once logged in as a resident, these endpoints return **only your own data**:

```powershell
$headers = @{ Authorization = "Bearer $token" }

Invoke-RestMethod -Uri "http://localhost:8000/me/profile"  -Headers $headers
Invoke-RestMethod -Uri "http://localhost:8000/me/dues"     -Headers $headers   # unpaid/partial charges + total_due
Invoke-RestMethod -Uri "http://localhost:8000/me/payments" -Headers $headers   # paid charge history
Invoke-RestMethod -Uri "http://localhost:8000/me/fines"    -Headers $headers   # fines + total_unpaid_fines
```

Key behaviors:

- All four require a valid JWT — anonymous calls get `401`.
- Data is scoped server-side to your linked resident record. There is **no way** to pass another resident's id — the API doesn't accept one.
- Every call writes a `query_private` entry to `audit_logs`.
- Admin accounts (not linked to a flat) get `404` on `/me/*` — they use admin endpoints instead.

### What each demo resident will actually see

The seeded data is deterministic, so each account returns a known result:

| Account | Flat | Dues (unpaid/partial) | Total due | Paid months | Fines |
|---|---|---|---|---|---|
| `resident1@society.in` | A-101 | 3 (sep partial, nov, dec) | ₹7,800 | 9 | 1 (wrong_parking, unpaid, ₹500) |
| `resident2@society.in` | A-202 | 1 | ₹2,800 | 11 | 1 (unpaid) |
| `resident3@society.in` | A-304 | 1 | ₹2,800 | 11 | 0 |
| `resident4@society.in` | A-405 | 2 | ₹5,600 | 10 | 0 |
| `resident5@society.in` | B-101 | 2 | ₹5,600 | 10 | 0 |
| `resident6@society.in` | B-203 | 2 | ₹5,300 | 10 | 0 |
| `resident7@society.in` | B-306 | 2 | ₹5,000 | 10 | 0 |
| `resident8@society.in` | B-404 | 0 | ₹0 | 12 | 0 |
| `resident9@society.in` | A-505 | 1 | ₹2,500 | 11 | 0 |
| `resident10@society.in` | B-606 | 2 | ₹4,400 | 10 | 0 |

Example — `/me/dues` as `resident1@society.in` returns:

```json
{
  "flat_no": "A-101",
  "total_due": 7800.0,
  "items": [
    { "charge_year": 2026, "charge_month": "sep", "amount": 2800.0, "status": "partial", "paid_date": "2026-09-11", "remarks": "Partial: 1400 received" },
    { "charge_year": 2026, "charge_month": "nov", "amount": 2500.0, "status": "unpaid", "paid_date": null, "remarks": "Pending payment" },
    { "charge_year": 2026, "charge_month": "dec", "amount": 2500.0, "status": "unpaid", "paid_date": null, "remarks": "Pending payment" }
  ]
}
```

> Log in as `resident8@society.in` to demo the "all paid, nothing due" case (empty dues list, `total_due: 0`).

### Admin endpoints

Log in as `admin1@society.in` and use the token for these:

```powershell
$headers = @{ Authorization = "Bearer $token" }

# List all society documents
Invoke-RestMethod -Uri "http://localhost:8000/admin/documents" -Headers $headers

# Upload a new document (multipart form)
$form = @{
  file          = Get-Item ".\notice.txt"
  title         = "Water Supply Notice"
  document_type = "notice"          # notice | policy | agm_minutes | circular
  issue_date    = "2026-07-19"
}
Invoke-RestMethod -Uri "http://localhost:8000/admin/documents/upload" `
  -Method Post -Headers $headers -Form $form

# Ingestion job status (every upload creates a pending job)
Invoke-RestMethod -Uri "http://localhost:8000/admin/ingestion-jobs" -Headers $headers

# Audit trail (logins, private queries, uploads, deletions)
Invoke-RestMethod -Uri "http://localhost:8000/admin/audit-logs" -Headers $headers
```

Rules:

- All `/admin/*` endpoints require the **admin** role — residents get `403`, anonymous gets `401`.
- Accepted file types: `.pdf`, `.txt`, `.md`.
- Every upload stores the file in `data/uploads/` and creates a `pending` ingestion job automatically.

### What fails (by design)

```powershell
# No token → 401
Invoke-RestMethod -Uri "http://localhost:8000/auth/me"

# Wrong password → 401
Invoke-RestMethod -Uri "http://localhost:8000/auth/login" -Method Post `
  -ContentType "application/json" `
  -Body '{"email":"resident1@society.in","password":"wrong"}'
```

---

## Where things are stored

| What | Where |
|---|---|
| User accounts | `database/society.db` → `users` table |
| Resident profiles (flat, phone) | `database/society.db` → `residents` table |
| Monthly charges / fines | `database/society.db` → `monthly_charges`, `fines` |
| Society documents (metadata) | `database/society.db` → `documents` table |
| Audit trail (logins, denials) | `database/society.db` → `audit_logs` table |
| Backend config | `backend/.env` |
| Demo console (login + chat) | `demo-login.html` (this repo root) |
| Tests | `backend/tests/` |

---

## Privacy rules (enforced in code, not just prompts)

- A resident can query **only their own** `resident_id` rows.
- Asking "show me flat B-302's dues" returns a **refusal** + an audit log entry.
- Passwords are stored as **bcrypt hashes**, never plaintext.
- The `DEV_PASSWORD_HASH:replace-on-first-login` placeholder exists only for demo seeding; production users get real hashes.
- Unauthorized attempts are logged in `audit_logs`.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `401 Unauthorized` on `/auth/me` | Token missing, expired (60 min default), or invalid. Re-login. |
| `403 Forbidden` on admin endpoints | You're logged in as a resident, not admin. Use `admin1@society.in`. |
| `Login fails with correct password` | Check `ALLOW_DEV_PASSWORD_PLACEHOLDERS=true` in `backend/.env` if using seeded accounts. |
| `Cannot reach http://localhost:8000` | Backend not running. Start it with `uvicorn app.main:app --reload --port 8000` from `backend/`. |
| `Demo page shows CORS error` | FastAPI CORS is open (`allow_origins=["*"]`) — if you see this, the backend isn't running. |

---

## Next steps (not built yet)

- ~~`/me/profile`, `/me/dues`, `/me/fines`~~ ✅ built
- ~~`/admin/documents/upload`~~ ✅ built
- ~~Ingestion pipeline~~ ✅ built — docs are chunked + embedded into a local Chroma store
- ~~`/chat/query`~~ ✅ built — natural-language Q&A with routing (public/private/hybrid/refused) and citations
- ~~Chat UI~~ ✅ built — chat panel in `demo-login.html`
- React frontend (the demo HTML page is a placeholder)
- Admin upload page in the demo console (the API works — see `ADMIN.md`)
