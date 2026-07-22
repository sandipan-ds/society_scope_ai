# User Guide — Society Scope AI

A practical, step-by-step guide to logging in and using the demo MVP.

> **Admin (committee) user?** See **[ADMIN.md](ADMIN.md)** for the full admin walkthrough — document upload, ingestion jobs, and audit logs.

---

## What this system does

Society Scope AI is a secure hybrid assistant for a housing society. It answers:

- **Public questions** from society notices, policies, AGM minutes, and circulars (RAG over documents)
- **Private questions** from your own resident account data — dues, fines, profile (Excel workbook lookup)

Access is role-based:
- **Residents** can see only their own private data
- **Admins** (committee: chairperson / secretary) can also upload documents, trigger ingestion, and view audit logs
- **Staff** (optional) sees only public notices + visitor policies

---

## Quickstart — run the backend + open the demo login page

### 1. Make sure the workbook is present

The runtime source of truth for resident data is:

```
data/members_data/Housing_Society_Charges_and_Fines_Template_108_Residents.xlsx
```

It contains `Residents`, `Maintenance Charges`, 6 fine sheets, and a `Payments` sheet.
No database seeding is required; the app reads the workbook directly.

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
- **Private questions** need a resident login: "What are my outstanding dues?" — answers come from your own workbook records only.
- **Hybrid questions** combine both: "What is my late fee and what rule defines it?"
- **Refusals** are shown in red: try "Show my neighbor's dues" — the request is denied and audit-logged.

The colored badge above each answer shows which route the query took (`public` / `private` / `hybrid` / `refused`).

---

## Demo credentials

All accounts use the same dev placeholder password:

```
replace-on-first-login
```

> ⚠️ This is a **dev-only placeholder**. When real authentication is wired, each user will have their own unique password. The placeholder works only because `ALLOW_DEV_PASSWORD_PLACEHOLDERS=true` in `backend/.env`.

### Admins

| Role | Email |
|---|---|
| **Admin** | `admin1@society.in` |
| **Admin** | `admin2@society.in` |

### Residents (workbook emails)

| Flat | Email |
|---|---|
| 101 | `meera_bhatt@demooutlook.com` |
| 102 | `rohan_gill@demoyahoo.com` |
| 103 | `mansi_khanna@demooutlook.com` |
| 304 | `arjun_nair@demogmail.com` |
| 505 | `tanmay_mhatre@demooutlook.com` |
| 606 | `neha_das@demooutlook.com` |
| 1806 | `nandini_nair@demogmail.com` |

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

> "Committee member" is modeled as **admin** in this MVP.

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
  -Body '{"email":"meera_bhatt@demooutlook.com","password":"replace-on-first-login"}'

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
  "user_id": 10101,
  "email": "meera_bhatt@demooutlook.com",
  "roles": ["resident"],
  "flat_no": "101"
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
- Data is scoped server-side to your linked flat. There is **no way** to pass another resident's id — the API doesn't accept one.
- Every call writes a `query_private` entry to the audit log.
- Admin accounts (not linked to a flat) get `404` on `/me/*` — they use admin endpoints instead.

### What the template workbook shows

The template workbook is fully zero-paid and has no fines, so every resident currently sees the same financial picture:

| Account | Flat | Dues (unpaid/partial) | Total due | Paid months | Fines |
|---|---|---|---|---|---|
| `meera_bhatt@demooutlook.com` | 101 | 12 | ₹42,000 | 0 | 0 |

> The maintenance charge is ₹3,500 per month. Fines are added per fine sheet, and the `Payments` sheet marks how much was paid. Edit the workbook in Excel to change any resident's data.

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
  -Body '{"email":"meera_bhatt@demooutlook.com","password":"wrong"}'
```

---

## Where things are stored

| What | Where |
|---|---|
| Resident profiles, charges, fines, payments | `data/members_data/Housing_Society_Charges_and_Fines_Template_108_Residents.xlsx` |
| Admin accounts | `data/app_state/users.json` |
| Society documents (metadata) | `data/app_state/documents.json` |
| Ingestion jobs | `data/app_state/ingestion_jobs.json` |
| Audit trail (logins, denials, queries) | `data/app_state/audit_logs.json` |
| Uploaded files | `data/uploads/` |
| Vector embeddings | `data/chroma/` |
| Backend config | `backend/.env` |
| Demo console (login + chat) | `demo-login.html` (this repo root) |
| Tests | `backend/tests/` |

---

## Editing data via Excel

Resident data lives in the workbook. Open it in Excel, edit the relevant sheet, and save. The backend reads the workbook on every request and caches it by file modification time, so changes appear without restarting the server.

### Sheets

- `Residents` — flat number, owner/resident names, occupancy type, emails, mobiles
- `Maintenance Charges` — total amount due per month (base ₹3,500 + sum of fines)
- `Parking Violation Fines`, `Waste Management Fines`, `Pet Policy Fines`, `Noise Violation Fines`, `Property Damage Fines`, `Miscellaneous Fines` — month-wise fine amounts per flat
- `Payments` — amount paid per month per flat (0 = unpaid, 3500 = fully paid, partial otherwise)

### Rules

- Do not rename sheets or the `Flat No.` column.
- Keep all financial sheets aligned to the same flat list and order as `Residents`.
- Months are labeled `Jan-26` .. `Dec-26`.
- `Maintenance Charges` values are formula-driven: `3500 + sum of fine sheets`. The app recalculates the same total independently.

---

## Privacy rules (enforced in code, not just prompts)

- A resident can query **only their own** flat's records.
- Asking "show me flat 302's dues" returns a **refusal** + an audit log entry.
- Passwords are stored as **bcrypt hashes**, never plaintext.
- The `DEV_PASSWORD_HASH:replace-on-first-login` placeholder exists only for demo seeding; production users get real hashes.
- Unauthorized attempts are logged in `data/app_state/audit_logs.json`.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `401 Unauthorized` on `/auth/me` | Token missing, expired (60 min default), or invalid. Re-login. |
| `403 Forbidden` on admin endpoints | You're logged in as a resident, not admin. Use `admin1@society.in`. |
| `Login fails with correct password` | Check `ALLOW_DEV_PASSWORD_PLACEHOLDERS=true` in `backend/.env` if using seeded accounts. |
| `Cannot reach http://localhost:8000` | Backend not running. Start it with `uvicorn app.main:app --reload --port 8000` from `backend/`. |
| `Demo page shows CORS error` | FastAPI CORS is open (`allow_origins=["*"]`) — if you see this, the backend isn't running. |
| `FileNotFoundError: Members data workbook not found` | The workbook at `data/members_data/Housing_Society_Charges_and_Fines_Template_108_Residents.xlsx` is missing. |

---

## Next steps (not built yet)

- ~~`/me/profile`, `/me/dues`, `/me/fines`~~ ✅ built
- ~~`/admin/documents/upload`~~ ✅ built
- ~~Ingestion pipeline~~ ✅ built — docs are chunked + embedded into a local Chroma store
- ~~`/chat/query`~~ ✅ built — natural-language Q&A with routing (public/private/hybrid/refused) and citations
- ~~Chat UI~~ ✅ built — chat panel in `demo-login.html`
- React frontend (the demo HTML page is a placeholder)
- Admin upload page in the demo console (the API works — see `ADMIN.md`)
