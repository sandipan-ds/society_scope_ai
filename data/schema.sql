-- Housing Society AI Assistant — SQLite database schema
-- Based on docs/04_DB_SCHEMA.md (simplified 6-table MVP version)
-- Notes:
--   * Uses INTEGER PRIMARY KEY AUTOINCREMENT instead of UUID/SERIAL for SQLite simplicity.
--   * Private resident data stays in SQL (not in vector embeddings).
--   * documents table stores metadata only; actual chunks/embeddings live in the vector store.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS residents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flat_no VARCHAR(10) NOT NULL UNIQUE,
    resident_name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    email VARCHAR(100) NOT NULL,
    is_owner BOOLEAN NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('resident', 'admin', 'staff')),
    resident_id INTEGER UNIQUE REFERENCES residents(id) ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS monthly_charges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resident_id INTEGER NOT NULL REFERENCES residents(id) ON DELETE CASCADE,
    charge_year INTEGER NOT NULL,
    charge_month VARCHAR(10) NOT NULL CHECK (
        charge_month IN ('jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec')
    ),
    amount NUMERIC(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('paid','unpaid','partial')),
    paid_date DATE,
    remarks TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resident_id INTEGER NOT NULL REFERENCES residents(id) ON DELETE CASCADE,
    fine_type VARCHAR(30) NOT NULL CHECK (fine_type IN ('parking','waste','pet','noise','property_damage','miscellaneous')),
    description TEXT NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    fine_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('paid','unpaid','waived')),
    remarks TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    document_type VARCHAR(30) NOT NULL CHECK (document_type IN ('notice','policy','agm_minutes','circular')),
    file_name VARCHAR(200) NOT NULL,
    issue_date DATE NOT NULL,
    uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    details TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending','processing','completed','failed')),
    error_message TEXT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Helpful indexes for the most common query paths
CREATE INDEX IF NOT EXISTS idx_residents_flat_no ON residents(flat_no);
CREATE INDEX IF NOT EXISTS idx_monthly_charges_resident_id ON monthly_charges(resident_id);
CREATE INDEX IF NOT EXISTS idx_fines_resident_id ON fines(resident_id);
CREATE INDEX IF NOT EXISTS idx_documents_issue_date ON documents(issue_date);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_document_id ON ingestion_jobs(document_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status ON ingestion_jobs(status);
