-- License Management Database Schema

CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    carrier_type TEXT,
    account_type TEXT,
    is_deleted INTEGER DEFAULT 0,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    registration_number TEXT UNIQUE NOT NULL,
    type TEXT,
    category TEXT,
    is_deleted INTEGER DEFAULT 0,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    checkpoints TEXT,
    is_deleted INTEGER DEFAULT 0,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS licenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    route_id INTEGER,
    record_number TEXT UNIQUE NOT NULL,
    driver_name TEXT,
    driver_phone TEXT,
    license_number TEXT UNIQUE NOT NULL,
    signature_date DATE,
    expiration_date DATE,
    status TEXT DEFAULT 'active',
    activity_location TEXT,
    registration_number TEXT UNIQUE NOT NULL,
    deletion_days INTEGER,
    vehicles_list TEXT,
    drivers_list TEXT,
    is_deleted INTEGER DEFAULT 0,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
    FOREIGN KEY (route_id) REFERENCES routes(id)
);

CREATE TABLE IF NOT EXISTS hazardous_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    material_type TEXT NOT NULL,
    is_deleted INTEGER DEFAULT 0,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    old_values TEXT,
    new_values TEXT,
    user_id TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS drivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    phone TEXT,
    is_deleted INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);


-- Indexes for performance (Section 4.2 & 6)
CREATE INDEX IF NOT EXISTS idx_licenses_number ON licenses(license_number);
CREATE INDEX IF NOT EXISTS idx_licenses_expiration ON licenses(expiration_date);
CREATE INDEX IF NOT EXISTS idx_licenses_status ON licenses(status);
CREATE INDEX IF NOT EXISTS idx_licenses_municipality ON licenses(activity_location);
CREATE UNIQUE INDEX IF NOT EXISTS idx_vehicles_registration ON vehicles(registration_number);
CREATE UNIQUE INDEX IF NOT EXISTS idx_licenses_registration_number ON licenses(registration_number);
CREATE INDEX IF NOT EXISTS idx_licenses_driver ON licenses(driver_name);
CREATE INDEX IF NOT EXISTS idx_vehicles_company ON vehicles(company_id);
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
CREATE INDEX IF NOT EXISTS idx_hazmat_vehicle ON hazardous_materials(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_audit_record ON audit_logs(table_name, record_id);
