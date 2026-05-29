import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path
import time
import threading

DB_PATH = Path(__file__).parent / "licenses.db"


class Database:
    def __init__(self, db_file=None):
        self.db_file = db_file or DB_PATH
        self._stats_cache = None
        self._advanced_stats_cache = None
        self._advanced_stats_cached_at = None
        self._stats_cache_lock = threading.Lock()
        self.init_database()
        self._run_migrations()

    # ─── Connection ──────────────────────────────────────────────────────────

    def _get_connection(self):
        # Each operation uses a fresh SQLite connection so the app can safely work
        # across the Electron process, API threads, and background jobs. WAL mode and
        # the busy timeout reduce lock contention for this local multi-reader setup.
        conn = sqlite3.connect(self.db_file, timeout=30)
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _execute_write(self, query, params=(), return_lastrowid=False):
        """Execute a write query with retry on transient SQLite lock errors.

        This retry loop is the main defense against short-lived write contention.
        Without it, the desktop app could fail sporadically whenever the scheduler,
        API, or UI trigger overlapping writes to the same database file.
        """
        retries = 3
        for attempt in range(retries):
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                if return_lastrowid:
                    return cursor.lastrowid
                return None
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < retries - 1:
                    time.sleep(0.2 * (attempt + 1))
                    continue
                raise
            finally:
                if conn:
                    conn.close()

    def add_audit_log(self, action, table_name, record_id, old_values=None, new_values=None, user_id="system"):
        """Record an entry in the audit log for tracking changes."""
        import json
        self._execute_write(
            "INSERT INTO audit_logs (action, table_name, record_id, old_values, new_values, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (action, table_name, record_id, 
             json.dumps(old_values) if old_values else None, 
             json.dumps(new_values) if new_values else None, 
             user_id)
        )

    def _invalidate_stats_cache(self):
        with self._stats_cache_lock:
            self._stats_cache = None
            self._advanced_stats_cache = None
            self._advanced_stats_cached_at = None

    # ─── Init / Schema ───────────────────────────────────────────────────────

    def init_database(self):
        # Bootstrap the schema from a single SQL file so a fresh install can be
        # recreated deterministically. Removing this would make setup depend on a
        # manually provisioned database file, which is fragile for local deployment.
        conn = sqlite3.connect(self.db_file, timeout=30)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA foreign_keys=ON")
        schema_file = Path(__file__).parent / "schema_definitions.sql"
        with open(schema_file, "r") as f:
            cursor.executescript(f.read())
        conn.commit()
        conn.close()

    def _run_migrations(self):
        """Add columns that may be missing from older DB files.

        This keeps older user databases compatible without forcing a destructive
        rebuild. The app can evolve its schema while preserving local data.
        """
        columns = [
            ("licenses", "activity_location", "ALTER TABLE licenses ADD COLUMN activity_location TEXT"),
            ("licenses", "contract_type",     "ALTER TABLE licenses ADD COLUMN contract_type TEXT"),
            ("licenses", "deletion_days",     "ALTER TABLE licenses ADD COLUMN deletion_days INTEGER"),
            ("licenses", "is_deleted",        "ALTER TABLE licenses ADD COLUMN is_deleted INTEGER DEFAULT 0"),
            ("licenses", "deleted_at",        "ALTER TABLE licenses ADD COLUMN deleted_at TIMESTAMP"),
            ("companies", "is_deleted",       "ALTER TABLE companies ADD COLUMN is_deleted INTEGER DEFAULT 0"),
            ("companies", "deleted_at",       "ALTER TABLE companies ADD COLUMN deleted_at TIMESTAMP"),
            ("vehicles",  "is_deleted",       "ALTER TABLE vehicles ADD COLUMN is_deleted INTEGER DEFAULT 0"),
            ("vehicles",  "deleted_at",       "ALTER TABLE vehicles ADD COLUMN deleted_at TIMESTAMP"),
            ("routes",    "is_deleted",       "ALTER TABLE routes ADD COLUMN is_deleted INTEGER DEFAULT 0"),
            ("routes",    "deleted_at",       "ALTER TABLE routes ADD COLUMN deleted_at TIMESTAMP"),
            ("hazardous_materials", "is_deleted", "ALTER TABLE hazardous_materials ADD COLUMN is_deleted INTEGER DEFAULT 0"),
            ("hazardous_materials", "deleted_at", "ALTER TABLE hazardous_materials ADD COLUMN deleted_at TIMESTAMP"),
        ]
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_licenses_number ON licenses(license_number)",
            "CREATE INDEX IF NOT EXISTS idx_licenses_driver ON licenses(driver_name)",
            "CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name)",
            "CREATE INDEX IF NOT EXISTS idx_vehicles_registration ON vehicles(registration_number)",
            "CREATE INDEX IF NOT EXISTS idx_licenses_activity_location ON licenses(activity_location)",
            "CREATE INDEX IF NOT EXISTS idx_licenses_contract_type ON licenses(contract_type)",
        ]

        conn = self._get_connection()
        try:
            # 1. Add Columns
            for table, col, sql in columns:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table})")
                cols = [row["name"] for row in cursor.fetchall()]
                if col not in cols:
                    try:
                        conn.execute(sql)
                    except sqlite3.OperationalError:
                        pass # Column might already exist or table missing
            
            # 2. Add Indexes
            for sql in indexes:
                try:
                    conn.execute(sql)
                except sqlite3.OperationalError:
                    pass # Column might be missing or other issue

            # 3. Remove deprecated hazardous material quantity field if still present.
            self._drop_hazmat_quantity_column(conn)

            conn.commit()
        finally:
            conn.close()

    def _drop_hazmat_quantity_column(self, conn):
        """Drop hazardous_materials.quantity safely to keep schema aligned with current requirements."""
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(hazardous_materials)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "quantity" not in columns:
            return

        conn.execute("""
            CREATE TABLE IF NOT EXISTS hazardous_materials_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                material_type TEXT NOT NULL,
                is_deleted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
            )
        """)
        conn.execute("""
            INSERT INTO hazardous_materials_new (id, vehicle_id, material_type, is_deleted, created_at)
            SELECT id, vehicle_id, material_type, is_deleted, created_at FROM hazardous_materials
        """)
        conn.execute("DROP TABLE hazardous_materials")
        conn.execute("ALTER TABLE hazardous_materials_new RENAME TO hazardous_materials")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hazmat_vehicle ON hazardous_materials(vehicle_id)")

    # ─── Users (Authentication) ───────────────────────────────────────────────

    def create_user(self, username: str, password_hash: str, role: str = "admin") -> int:
        """Insert a new user row. Password must already be hashed by the caller."""
        return self._execute_write(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role),
            return_lastrowid=True,
        )

    def get_user_by_username(self, username: str) -> dict | None:
        """Return the user row for the given username, or None if not found."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash, role, created_at FROM users WHERE username=?",
            (username,)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_user_password(self, username: str, new_password_hash: str) -> None:
        """Replace the stored password hash for a user."""
        self._execute_write(
            "UPDATE users SET password_hash=?, updated_at=CURRENT_TIMESTAMP WHERE username=?",
            (new_password_hash, username),
        )

    # ─── Company ─────────────────────────────────────────────────────────────

    def add_company(self, name, registration_number, address, carrier_type, account_type):
        self._invalidate_stats_cache()
        return self._execute_write(
            """INSERT INTO companies (name, registration_number, address, carrier_type, account_type)
               VALUES (?, ?, ?, ?, ?)""",
            (name, registration_number, address, carrier_type, account_type),
            return_lastrowid=True,
        )

    def get_companies(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, registration_number, address, carrier_type, account_type, created_at "
            "FROM companies WHERE is_deleted=0 ORDER BY created_at DESC"
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_company_by_id(self, company_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM companies WHERE id=? AND is_deleted=0", (company_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_company_by_registration(self, registration_number):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM companies WHERE registration_number=? AND is_deleted=0", (registration_number,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    # ─── Vehicle ─────────────────────────────────────────────────────────────

    def add_vehicle(self, company_id, registration_number, vehicle_type, category):
        self._invalidate_stats_cache()
        return self._execute_write(
            "INSERT INTO vehicles (company_id, registration_number, type, category) VALUES (?, ?, ?, ?)",
            (company_id, registration_number, vehicle_type, category),
            return_lastrowid=True,
        )

    def get_vehicles(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, company_id, registration_number, type, category, created_at "
            "FROM vehicles WHERE is_deleted=0 ORDER BY created_at DESC"
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_vehicles_by_company(self, company_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, registration_number, type, category FROM vehicles WHERE company_id=? AND is_deleted=0",
            (company_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_vehicle_by_id(self, vehicle_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vehicles WHERE id=? AND is_deleted=0", (vehicle_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_vehicle_by_registration(self, registration_number):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vehicles WHERE registration_number=? AND is_deleted=0", (registration_number,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    # ─── Route ───────────────────────────────────────────────────────────────

    def add_route(self, origin, destination, checkpoints=None):
        return self._execute_write(
            "INSERT INTO routes (origin, destination, checkpoints) VALUES (?, ?, ?)",
            (origin, destination, checkpoints),
            return_lastrowid=True,
        )

    def get_routes(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, origin, destination, checkpoints, created_at FROM routes WHERE is_deleted=0 ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ─── License ─────────────────────────────────────────────────────────────

    def add_license(self, vehicle_id, route_id, record_number, driver_name, driver_phone,
                    license_number, signature_date, expiration_date,
                    activity_location=None, contract_type=None, deletion_days=None):
        today = datetime.now().date()
        expiry = expiration_date if isinstance(expiration_date, datetime) else datetime.strptime(str(expiration_date), '%Y-%m-%d').date()
        status = "expired" if expiry < today else "active"
        lic_id = self._execute_write(
            """INSERT INTO licenses
               (vehicle_id, route_id, record_number, driver_name, driver_phone,
                license_number, signature_date, expiration_date, status,
                activity_location, contract_type, deletion_days)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (vehicle_id, route_id, record_number, driver_name, driver_phone,
             license_number, signature_date, expiration_date, status,
             activity_location, contract_type, deletion_days),
            return_lastrowid=True,
        )
        if lic_id:
            self.add_audit_log("CREATE", "licenses", lic_id, new_values={
                "license_number": license_number, "record_number": record_number
            })
        return lic_id

    def get_all_licenses(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT l.id, l.record_number, l.license_number, l.driver_name, l.driver_phone,
                      l.signature_date, l.expiration_date, l.status,
                      l.activity_location, l.contract_type, l.deletion_days, l.created_at,
                      v.registration_number AS vehicle_reg,
                      c.name AS company_name, c.carrier_type
               FROM licenses l
               JOIN vehicles v ON l.vehicle_id = v.id
               JOIN companies c ON v.company_id = c.id
               WHERE l.is_deleted=0
               ORDER BY l.created_at DESC"""
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def search_licenses(self, search_term="", status_filter=None, carrier_type_filter=None,
                        activity_location=None, contract_type=None,
                        sort_by="created_at", sort_dir="DESC",
                        page=1, limit=50):
        """Paginated, filtered, sorted license search."""
        self._update_expired_licenses()
        conn = self._get_connection()
        cursor = conn.cursor()

        # Whitelist sort columns
        allowed_sorts = {"signature_date", "expiration_date", "created_at", "company_name"}
        if sort_by not in allowed_sorts:
            sort_by = "created_at"
        sort_col = f"l.{sort_by}"
        if sort_by == "company_name":
            sort_col = "c.name"
        sort_dir = "ASC" if sort_dir.upper() == "ASC" else "DESC"

        base = """FROM licenses l
                  JOIN vehicles v ON l.vehicle_id = v.id
                  JOIN companies c ON v.company_id = c.id
                  LEFT JOIN routes r ON l.route_id = r.id
                  WHERE l.is_deleted=0"""
        params = []

        if search_term:
            base += """ AND (l.record_number LIKE ? OR l.license_number LIKE ?
                         OR v.registration_number LIKE ? OR c.name LIKE ? OR l.driver_name LIKE ?)"""
            p = f"%{search_term}%"
            params.extend([p, p, p, p, p])

        if status_filter:
            base += " AND l.status=?"
            params.append(status_filter)

        if carrier_type_filter:
            base += " AND c.carrier_type=?"
            params.append(carrier_type_filter)

        if activity_location:
            base += " AND l.activity_location LIKE ?"
            params.append(f"%{activity_location}%")

        if contract_type:
            base += " AND l.contract_type=?"
            params.append(contract_type)

        # Total count
        cursor.execute(f"SELECT COUNT(*) {base}", params)
        total = cursor.fetchone()[0]

        # Data query
        offset = (page - 1) * limit
        select = f"""SELECT l.id, l.record_number, l.license_number,
                            l.signature_date, l.expiration_date, l.status,
                            l.activity_location, l.contract_type, l.deletion_days, l.created_at,
                            v.registration_number AS vehicle_reg, v.type AS vehicle_type, v.category AS vehicle_category,
                            c.name AS company_name, c.carrier_type, c.registration_number AS company_reg, c.address AS company_address,
                            r.origin AS route_origin, r.destination AS route_dest,
                            (SELECT GROUP_CONCAT(material_type, ', ') FROM hazardous_materials WHERE vehicle_id = v.id AND is_deleted = 0) AS hazmat_type
                     {base}
                     ORDER BY {sort_col} {sort_dir}
                     LIMIT ? OFFSET ?"""
        cursor.execute(select, params + [limit, offset])
        rows = cursor.fetchall()
        conn.close()
        return {"total": total, "page": page, "limit": limit, "records": [dict(r) for r in rows]}

    def search_deleted_licenses(self, search_term="", status_filter=None, activity_location=None,
                               contract_type=None, sort_by="created_at", sort_dir="DESC", page=1, limit=50):
        """Paginated search over deleted contracts only."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Whitelist sort columns
        allowed_sorts = {"signature_date", "expiration_date", "created_at", "company_name"}
        if sort_by not in allowed_sorts:
            sort_by = "created_at"
        sort_col = f"l.{sort_by}"
        if sort_by == "company_name":
            sort_col = "c.name"
        sort_dir = "ASC" if sort_dir.upper() == "ASC" else "DESC"

        base = """FROM licenses l
                  JOIN vehicles v ON l.vehicle_id = v.id
                  JOIN companies c ON v.company_id = c.id
                  LEFT JOIN routes r ON l.route_id = r.id
                  WHERE l.is_deleted=1"""
        params = []

        if search_term:
            base += """ AND (CAST(l.id AS TEXT) LIKE ? OR l.record_number LIKE ? OR l.license_number LIKE ?
                         OR v.registration_number LIKE ? OR c.name LIKE ? OR l.driver_name LIKE ?)"""
            p = f"%{search_term}%"
            params.extend([p, p, p, p, p, p])

        if status_filter:
            base += " AND l.status=?"
            params.append(status_filter)

        if activity_location:
            base += " AND l.activity_location LIKE ?"
            params.append(f"%{activity_location}%")

        if contract_type:
            base += " AND l.contract_type=?"
            params.append(contract_type)

        cursor.execute(f"SELECT COUNT(*) {base}", params)
        total = cursor.fetchone()[0]

        offset = (page - 1) * limit
        query = f"""SELECT l.id, l.record_number, l.license_number,
                           l.signature_date, l.expiration_date, l.status,
                           l.activity_location, l.contract_type, l.deletion_days, l.created_at,
                           v.registration_number AS vehicle_reg, v.type AS vehicle_type, v.category AS vehicle_category,
                           c.name AS company_name, c.carrier_type, c.registration_number AS company_reg, c.address AS company_address,
                           r.origin AS route_origin, r.destination AS route_dest,
                           (SELECT GROUP_CONCAT(material_type, ', ') FROM hazardous_materials WHERE vehicle_id = v.id AND is_deleted = 0) AS hazmat_type
                    {base}
                    ORDER BY {sort_col} {sort_dir}
                    LIMIT ? OFFSET ?"""
        cursor.execute(query, params + [limit, offset])
        rows = cursor.fetchall()
        conn.close()
        return {"total": total, "page": page, "limit": limit, "records": [dict(r) for r in rows]}

    def get_license_by_id(self, license_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT l.*, v.registration_number AS vehicle_reg, v.type AS vehicle_type,
                      c.name AS company_name, c.carrier_type, c.registration_number AS company_reg,
                      c.address AS company_address, c.account_type,
                      r.origin, r.destination, r.checkpoints
               FROM licenses l
               JOIN vehicles v ON l.vehicle_id = v.id
               JOIN companies c ON v.company_id = c.id
               LEFT JOIN routes r ON l.route_id = r.id
               WHERE l.id=? AND l.is_deleted=0""",
            (license_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_license_by_number(self, license_number):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM licenses WHERE license_number=? AND is_deleted=0", (license_number,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_license_by_record_number(self, record_number):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM licenses WHERE record_number=? AND is_deleted=0", (record_number,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_license(self, license_id, **fields):
        if not fields:
            return None
        allowed = {"record_number","driver_name","driver_phone","license_number",
                   "signature_date","expiration_date","status","activity_location",
                   "contract_type","deletion_days"}
        fields = {k: v for k, v in fields.items() if k in allowed}
        if not fields:
            return None
        # Get old values for auditing
        old_data = self.get_license_by_id(license_id)
        
        set_clause = ", ".join([f"{k}=?" for k in fields.keys()])
        query = f"UPDATE licenses SET {set_clause} WHERE id=? AND is_deleted=0"
        params = list(fields.values()) + [license_id]
        
        res = self._execute_write(query, params)
        if res is not None or True: # execute_write returns None on success if not lastrowid
            self.add_audit_log("UPDATE", "licenses", license_id, old_values=old_data, new_values=fields)
        
        self._invalidate_stats_cache()
        return res

    def soft_delete_license(self, license_id):
        # Soft delete preserves compliance history while hiding inactive records from
        # normal views. Hard delete would destroy auditability and break restore flows.
        self._invalidate_stats_cache()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.add_audit_log("DELETE", "licenses", license_id)
        return self._execute_write("UPDATE licenses SET is_deleted=1, deleted_at=? WHERE id=?", (now, license_id))

    def restore_license(self, license_id):
        """Restore a previously soft-deleted license back to active listings.

        This reversal exists because the system treats deletion as reversible status
        management, not permanent destruction. If removed, recovery from accidental
        deletion would require manual database surgery.
        """
        self._invalidate_stats_cache()
        self.add_audit_log("RESTORE", "licenses", license_id)
        return self._execute_write("UPDATE licenses SET is_deleted=0, deleted_at=NULL WHERE id=?", (license_id,))

    def update_license_status(self, license_id, status):
        self._execute_write("UPDATE licenses SET status=? WHERE id=?", (status, license_id))

    def _update_expired_licenses(self):
        self._execute_write(
            "UPDATE licenses SET status='expired' WHERE status='active' AND DATE(expiration_date)<DATE('now') AND is_deleted=0"
        )

    def get_expiring_licenses(self, days_ahead=30):
        conn = self._get_connection()
        cursor = conn.cursor()
        today = datetime.now().date()
        expiry_date = (datetime.now() + timedelta(days=days_ahead)).date()
        cursor.execute(
            """SELECT l.id, l.license_number, l.driver_name, l.expiration_date,
                      v.registration_number AS vehicle_reg, c.name AS company_name
               FROM licenses l
               JOIN vehicles v ON l.vehicle_id=v.id
               JOIN companies c ON v.company_id=c.id
               WHERE l.expiration_date BETWEEN ? AND ? AND l.status='active' AND l.is_deleted=0
               ORDER BY l.expiration_date ASC""",
            (today, expiry_date)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ─── Hazmat ──────────────────────────────────────────────────────────────

    def add_hazmat(self, vehicle_id, material_type):
        return self._execute_write(
            "INSERT INTO hazardous_materials (vehicle_id, material_type) VALUES (?, ?)",
            (vehicle_id, material_type),
            return_lastrowid=True,
        )

    def get_hazmats_by_vehicle(self, vehicle_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hazardous_materials WHERE vehicle_id=? AND is_deleted=0", (vehicle_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ─── Settings ────────────────────────────────────────────────────────────

    def get_setting(self, key):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def set_setting(self, key, value):
        self._execute_write("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))

    def get_all_settings(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        rows = cursor.fetchall()
        conn.close()
        return {r["key"]: r["value"] for r in rows}

    # ─── Statistics (cached) ─────────────────────────────────────────────────

    def get_statistics(self):
        with self._stats_cache_lock:
            if self._stats_cache is not None:
                return self._stats_cache
        self._update_expired_licenses()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM licenses WHERE status='active' AND is_deleted=0")
        active_licenses = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM licenses WHERE status='expired' AND is_deleted=0")
        expired_licenses = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM licenses WHERE is_deleted=0")
        total_contracts = cursor.fetchone()[0]
        conn.close()
        result = {
            "active_licenses": active_licenses,
            "expired_licenses": expired_licenses,
            "total_contracts": total_contracts,
        }
        with self._stats_cache_lock:
            self._stats_cache = result
        return result

    def get_advanced_statistics(self):
        """Return advanced metrics used by analytics UI, including carrier activity breakdowns."""
        with self._stats_cache_lock:
            if self._advanced_stats_cache is not None and self._advanced_stats_cached_at is not None:
                if (datetime.now() - self._advanced_stats_cached_at).total_seconds() < 30:
                    return self._advanced_stats_cache

        self._update_expired_licenses()
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""SELECT c.carrier_type, COUNT(*) as count
                          FROM licenses l JOIN vehicles v ON l.vehicle_id=v.id
                          JOIN companies c ON v.company_id=c.id
                          WHERE l.is_deleted=0 GROUP BY c.carrier_type""")
        by_carrier = {r["carrier_type"] or "Unknown": r["count"] for r in cursor.fetchall()}

        cursor.execute("SELECT status, COUNT(*) as count FROM licenses WHERE is_deleted=0 GROUP BY status")
        by_status = {r["status"] or "Unknown": r["count"] for r in cursor.fetchall()}

        cursor.execute("""SELECT COUNT(*) as count FROM licenses
                          WHERE status='active' AND is_deleted=0
                          AND DATE(expiration_date) BETWEEN DATE('now') AND DATE('now','+30 days')""")
        expiring_soon = cursor.fetchone()["count"]

        cursor.execute("""SELECT c.name, COUNT(*) as count
                          FROM licenses l JOIN vehicles v ON l.vehicle_id=v.id
                          JOIN companies c ON v.company_id=c.id
                          WHERE l.is_deleted=0 GROUP BY c.name ORDER BY count DESC LIMIT 10""")
        by_company = {r["name"]: r["count"] for r in cursor.fetchall()}

        cursor.execute("""SELECT l.contract_type, COUNT(*) as count
                          FROM licenses l WHERE l.is_deleted=0 AND l.contract_type IS NOT NULL
                          GROUP BY l.contract_type""")
        by_contract_type = {r["contract_type"]: r["count"] for r in cursor.fetchall()}

        cursor.execute("""SELECT l.activity_location, COUNT(*) as count
                          FROM licenses l WHERE l.is_deleted=0 AND l.activity_location IS NOT NULL
                          GROUP BY l.activity_location ORDER BY count DESC LIMIT 10""")
        by_location = {r["activity_location"]: r["count"] for r in cursor.fetchall()}

        cursor.execute("""SELECT COUNT(*) AS count FROM companies WHERE is_deleted=0""")
        total_carriers = cursor.fetchone()["count"]

        cursor.execute("""SELECT carrier_type, COUNT(*) AS count
                          FROM companies WHERE is_deleted=0 GROUP BY carrier_type""")
        carriers_by_type = {r["carrier_type"] or "Unknown": r["count"] for r in cursor.fetchall()}

        cursor.execute("""
            SELECT c.id,
                   MAX(CASE WHEN l.status='active' AND l.is_deleted=0 THEN 1 ELSE 0 END) AS has_active
            FROM companies c
            LEFT JOIN vehicles v ON v.company_id = c.id AND v.is_deleted=0
            LEFT JOIN licenses l ON l.vehicle_id = v.id
            WHERE c.is_deleted=0
            GROUP BY c.id
        """)
        carrier_activity_rows = cursor.fetchall()
        active_carriers = sum(1 for row in carrier_activity_rows if row["has_active"] == 1)
        inactive_carriers = max(0, total_carriers - active_carriers)

        cursor.execute("""
            SELECT COALESCE(NULLIF(TRIM(l.activity_location), ''), 'Unknown') AS municipality,
                   COUNT(DISTINCT c.id) AS total_carriers,
                   COUNT(DISTINCT CASE WHEN l.status='active' THEN c.id END) AS active_carriers,
                   COUNT(DISTINCT CASE WHEN l.status='expired' THEN c.id END) AS inactive_carriers
            FROM companies c
            LEFT JOIN vehicles v ON v.company_id = c.id AND v.is_deleted=0
            LEFT JOIN licenses l ON l.vehicle_id = v.id AND l.is_deleted=0
            WHERE c.is_deleted=0
            GROUP BY municipality
            ORDER BY total_carriers DESC
            LIMIT 15
        """)
        municipality_rows = cursor.fetchall()
        carriers_by_municipality = {
            row["municipality"]: {
                "total": row["total_carriers"],
                "active": row["active_carriers"],
                "inactive": max(0, row["total_carriers"] - row["active_carriers"]),
            }
            for row in municipality_rows
        }

        conn.close()
        result = {
            "by_carrier": by_carrier,
            "by_status": by_status,
            "expiring_soon": expiring_soon,
            "by_company": by_company,
            "by_contract_type": by_contract_type,
            "by_location": by_location,
            "carrier_totals": {
                "total": total_carriers,
                "public": carriers_by_type.get("Public", 0),
                "private": carriers_by_type.get("Private", 0),
                "active": active_carriers,
                "inactive": inactive_carriers,
            },
            "carriers_by_municipality": carriers_by_municipality,
        }
        with self._stats_cache_lock:
            self._advanced_stats_cache = result
            self._advanced_stats_cached_at = datetime.now()
        return result

    def get_monthly_transports(self, months=12):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT strftime('%Y-%m', signature_date) as month, COUNT(*) as count
                          FROM licenses WHERE is_deleted=0
                          AND signature_date >= DATE('now', '-{} months')
                          GROUP BY month ORDER BY month ASC""".format(months))
        rows = cursor.fetchall()
        conn.close()
        return [{"month": r["month"], "count": r["count"]} for r in rows]

    # ─── Soft Delete (cascade) ───────────────────────────────────────────────

    def delete_company(self, company_id):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM vehicles WHERE company_id=?", (company_id,))
            vehicles = [r["id"] for r in cursor.fetchall()]
            for vid in vehicles:
                conn.execute("UPDATE hazardous_materials SET is_deleted=1 WHERE vehicle_id=?", (vid,))
                conn.execute("UPDATE licenses SET is_deleted=1 WHERE vehicle_id=?", (vid,))
            conn.execute("UPDATE vehicles SET is_deleted=1 WHERE company_id=?", (company_id,))
            conn.execute("UPDATE companies SET is_deleted=1 WHERE id=?", (company_id,))
            conn.commit()
            self._invalidate_stats_cache()
        finally:
            conn.close()

    def delete_vehicle(self, vehicle_id):
        conn = self._get_connection()
        try:
            conn.execute("UPDATE hazardous_materials SET is_deleted=1 WHERE vehicle_id=?", (vehicle_id,))
            conn.execute("UPDATE licenses SET is_deleted=1 WHERE vehicle_id=?", (vehicle_id,))
            conn.execute("UPDATE vehicles SET is_deleted=1 WHERE id=?", (vehicle_id,))
            conn.commit()
            self._invalidate_stats_cache()
        finally:
            conn.close()

    def delete_license(self, license_id):
        """Soft delete – keeps data, marks as deleted."""
        self.soft_delete_license(license_id)

    # ─── Notifications ───────────────────────────────────────────────────────

    def log_notification(self, license_id, email_sent_to):
        self._execute_write(
            "INSERT INTO notifications_log (license_id, email_sent_to) VALUES (?, ?)",
            (license_id, email_sent_to),
        )

    def get_notification_log(self, limit=100):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM notifications_log ORDER BY sent_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
