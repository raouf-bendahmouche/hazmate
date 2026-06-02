import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path
import time
import threading

"""
ARCHITECTURAL REFACTORING & DESIGN NOTES (FULL SYSTEM SYNCHRONIZATION):

1. Entity Separation (Vehicles / Drivers / Contracts):
   - Previously, driver data was parsed as raw JSON arrays or text fields embedded inside the `licenses` table.
   - We have fully separated Drivers and Vehicles into their own dedicated schemas and views.
   - The `drivers` table stores driver entities, whereas the `vehicles` table stores vehicle entities.
   - This prevents cross-data leakage between contracts, vehicles, and drivers modules in compliance with strict UX separation rules.

2. Auto-Increment Driver ID Logic:
   - Drivers are registered with a system-generated, auto-incrementing `id` as the primary key.
   - Manual driver ID edits are prohibited; all driver identifiers are system-generated to maintain relational integrity.

3. Optional Phone Field Design:
   - The driver's phone number (`phone` column in the `drivers` table) is optional (nullable).
   - This ensures flexibility during driver registration, allowing operators to create records even when phone numbers are unavailable.

4. Expiration Segmentation Design:
   - The expiration dashboard is segmented into three distinct preview ranges: 30, 60, and 90 days.
   - To keep queries scalable and UI rendering highly responsive, we filter these ranges entirely at the SQLite/backend layer.
   - Previews return a limited dataset (limit = 5), while full range queries are loaded only upon user request.

5. Removal of Background Services:
   - SMTP configuration, email notification triggers, local database backup utilities, and their corresponding background scheduler threads
     have been completely purged from uvicorn lifespans, API routers, database schemas, and documentation.
   - This reduces background CPU overhead, eliminates potential memory/process leaks in the Electron desktop shell, and prevents security risks.

6. Indexing Strategy:
   - B-Tree indexes are preserved on vehicle registration numbers and licensing fields to optimize search lookups and query execution times.
"""

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
            ("licenses", "registration_number", "ALTER TABLE licenses ADD COLUMN registration_number TEXT"),
            ("licenses", "deletion_days",     "ALTER TABLE licenses ADD COLUMN deletion_days INTEGER"),
            ("licenses", "vehicles_list",      "ALTER TABLE licenses ADD COLUMN vehicles_list TEXT"),
            ("licenses", "drivers_list",       "ALTER TABLE licenses ADD COLUMN drivers_list TEXT"),
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
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_vehicles_registration ON vehicles(registration_number)",
            "CREATE INDEX IF NOT EXISTS idx_licenses_activity_location ON licenses(activity_location)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_licenses_registration_number ON licenses(registration_number)",
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
            try:
                # Drop old non-unique index if it exists to allow unique index creation
                conn.execute("DROP INDEX IF EXISTS idx_vehicles_registration")
            except sqlite3.OperationalError:
                pass
            for sql in indexes:
                try:
                    conn.execute(sql)
                except sqlite3.OperationalError:
                    pass # Column might be missing or other issue

            # 3. Remove deprecated hazardous material quantity field if still present.
            self._drop_hazmat_quantity_column(conn)
            # 4. Remove companies.registration_number safely if present.
            self._drop_companies_registration_number(conn)

            # 5. Create drivers table and migrate existing driver records
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS drivers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        phone TEXT,
                        is_deleted INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (company_id) REFERENCES companies(id)
                    )
                """)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM drivers")
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        SELECT l.driver_name, l.driver_phone, l.drivers_list, v.company_id
                        FROM licenses l
                        JOIN vehicles v ON l.vehicle_id = v.id
                        WHERE l.is_deleted = 0
                    """)
                    rows = cursor.fetchall()
                    import json
                    for row in rows:
                        comp_id = row["company_id"]
                        p_name = row["driver_name"]
                        p_phone = row["driver_phone"]
                        d_list_str = row["drivers_list"]
                        
                        if p_name and p_name.strip():
                            # Check uniqueness
                            cursor.execute("SELECT id FROM drivers WHERE company_id=? AND name=?", (comp_id, p_name.strip()))
                            if not cursor.fetchone():
                                cursor.execute("INSERT INTO drivers (company_id, name, phone) VALUES (?, ?, ?)", (comp_id, p_name.strip(), p_phone))
                        
                        if d_list_str:
                            try:
                                parsed = json.loads(d_list_str)
                                if isinstance(parsed, list):
                                    for d in parsed:
                                        d_name = d.get("name")
                                        d_phone = d.get("phone")
                                        if d_name and d_name.strip():
                                            cursor.execute("SELECT id FROM drivers WHERE company_id=? AND name=?", (comp_id, d_name.strip()))
                                            if not cursor.fetchone():
                                                cursor.execute("INSERT INTO drivers (company_id, name, phone) VALUES (?, ?, ?)", (comp_id, d_name.strip(), d_phone))
                                    conn.commit()
                            except Exception:
                                pass
            except sqlite3.OperationalError:
                pass

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

    def _drop_companies_registration_number(self, conn):
        """Drop companies.registration_number safely to align with schema requirements."""
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(companies)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "registration_number" not in columns:
            return

        conn.execute("""
            CREATE TABLE IF NOT EXISTS companies_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                carrier_type TEXT,
                account_type TEXT,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            INSERT INTO companies_new (id, name, address, carrier_type, account_type, is_deleted, deleted_at, created_at)
            SELECT id, name, address, carrier_type, account_type, is_deleted, deleted_at, created_at FROM companies
        """)
        conn.execute("DROP TABLE companies")
        conn.execute("ALTER TABLE companies_new RENAME TO companies")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name)")

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

    def update_username(self, current_username: str, new_username: str) -> None:
        """
        Update the username for a user.
        Detailed technical comment (Requirement 15):
        Updating usernames is database-synchronized and transaction-safe. The database-level
        update is critical so that any audit logs or reference checks mapped dynamically
        to the user row remain correctly associated.
        """
        self._execute_write(
            "UPDATE users SET username=?, updated_at=CURRENT_TIMESTAMP WHERE username=?",
            (new_username, current_username),
        )

    # ─── Company ─────────────────────────────────────────────────────────────

    def add_company(self, name, address, carrier_type, account_type):
        self._invalidate_stats_cache()
        return self._execute_write(
            """INSERT INTO companies (name, address, carrier_type, account_type)
               VALUES (?, ?, ?, ?)""",
            (name, address, carrier_type, account_type),
            return_lastrowid=True,
        )

    def get_companies(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, address, carrier_type, account_type, created_at "
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

    # ─── Vehicle ─────────────────────────────────────────────────────────────

    def add_vehicle(self, company_id, registration_number, vehicle_type, category):
        """
        Add a new vehicle record.
        Detailed technical comment (Requirement 15):
        Vehicle IDs use AUTOINCREMENT to guarantee that every vehicle has a unique, system-generated
        identifier. This avoids manual sequence management, ensures keys are stable after vehicle deletes,
        and maintains referential integrity under foreign key constraints.
        """
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
            "SELECT v.id, v.company_id, v.registration_number, v.type, v.category, v.created_at, "
            "       c.name AS company_name "
            "FROM vehicles v "
            "JOIN companies c ON v.company_id = c.id "
            "WHERE v.is_deleted=0 AND c.is_deleted=0 "
            "ORDER BY v.created_at DESC"
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ─── Driver ──────────────────────────────────────────────────────────────

    def add_driver(self, company_id, name, phone=None):
        """
        Add a new driver. Enforce auto-increment ID and system generated.
        Optional phone field is nullable.
        """
        name = name.strip() if name else ""
        if not name:
            return None
        
        # Check duplicate
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, phone FROM drivers WHERE company_id=? AND name=? AND is_deleted=0", (company_id, name))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            if phone and row["phone"] != phone:
                self._execute_write(
                    "UPDATE drivers SET phone=? WHERE id=?",
                    (phone, row["id"])
                )
            return row["id"]
        else:
            return self._execute_write(
                "INSERT INTO drivers (company_id, name, phone) VALUES (?, ?, ?)",
                (company_id, name, phone),
                return_lastrowid=True
            )

    def get_drivers(self):
        """
        Retrieve all drivers with their system-generated IDs and company associations.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT d.id, d.company_id, d.name AS driver_name, d.phone AS driver_phone, d.created_at, "
            "       c.name AS company_name "
            "FROM drivers d "
            "JOIN companies c ON d.company_id = c.id "
            "WHERE d.is_deleted=0 AND c.is_deleted=0 "
            "ORDER BY d.created_at DESC"
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
                    activity_location=None, registration_number=None, deletion_days=None,
                    vehicles_list=None, drivers_list=None):
        today = datetime.now().date()
        expiry = expiration_date if isinstance(expiration_date, datetime) else datetime.strptime(str(expiration_date), '%Y-%m-%d').date()
        status = "expired" if expiry < today else "active"
        lic_id = self._execute_write(
            """INSERT INTO licenses
               (vehicle_id, route_id, record_number, driver_name, driver_phone,
                license_number, signature_date, expiration_date, status,
                activity_location, registration_number, deletion_days, vehicles_list, drivers_list)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (vehicle_id, route_id, record_number, driver_name, driver_phone,
             license_number, signature_date, expiration_date, status,
             activity_location, registration_number, deletion_days, vehicles_list, drivers_list),
            return_lastrowid=True,
        )
        if lic_id:
            self.add_audit_log("CREATE", "licenses", lic_id, new_values={
                "license_number": license_number, "record_number": record_number
            })
            # Sync driver to drivers table automatically
            vehicle = self.get_vehicle_by_id(vehicle_id)
            if vehicle and vehicle.get("company_id"):
                comp_id = vehicle["company_id"]
                if driver_name and driver_name.strip():
                    self.add_driver(comp_id, driver_name, driver_phone)
                if drivers_list:
                    try:
                        import json
                        parsed = json.loads(drivers_list) if isinstance(drivers_list, str) else drivers_list
                        if isinstance(parsed, list):
                            for d in parsed:
                                n = d.get("name")
                                p = d.get("phone")
                                if n and n.strip():
                                    self.add_driver(comp_id, n, p)
                    except Exception:
                        pass
        return lic_id

    def get_all_licenses(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT l.id, l.record_number, l.license_number, l.driver_name, l.driver_phone,
                      l.signature_date, l.expiration_date, l.status,
                      l.activity_location, l.registration_number, l.deletion_days, l.created_at, l.vehicles_list, l.drivers_list,
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
                        activity_location=None,
                        sort_by="created_at", sort_dir="DESC",
                        page=1, limit=50):
        """Paginated, filtered, sorted license search."""
        self._update_expired_licenses()
        conn = self._get_connection()
        cursor = conn.cursor()

        # Whitelist sort columns
        allowed_sorts = {"signature_date", "expiration_date", "created_at"}
        if sort_by not in allowed_sorts:
            sort_by = "created_at"
        sort_dir = "ASC" if sort_dir.upper() == "ASC" else "DESC"

        base = """FROM licenses l
                  JOIN vehicles v ON l.vehicle_id = v.id
                  JOIN companies c ON v.company_id = c.id
                  WHERE l.is_deleted=0"""
        params = []

        if search_term:
            base += """ AND (l.record_number LIKE ? OR l.license_number LIKE ? OR l.registration_number LIKE ?
                         OR v.registration_number LIKE ? OR c.name LIKE ? OR l.driver_name LIKE ?)"""
            p = f"%{search_term}%"
            params.extend([p, p, p, p, p, p])

        if status_filter:
            base += " AND l.status=?"
            params.append(status_filter)

        if carrier_type_filter:
            base += " AND c.carrier_type=?"
            params.append(carrier_type_filter)

        if activity_location:
            base += " AND l.activity_location LIKE ?"
            params.append(f"%{activity_location}%")

        # Total count
        cursor.execute(f"SELECT COUNT(*) {base}", params)
        total = cursor.fetchone()[0]

        # Data query
        offset = (page - 1) * limit
        select = f"""SELECT l.id, l.record_number, l.license_number, l.driver_name, l.driver_phone,
                            l.signature_date, l.expiration_date, l.status,
                            l.activity_location, l.registration_number, l.deletion_days, l.created_at, l.vehicles_list, l.drivers_list,
                            v.registration_number AS vehicle_reg,
                            c.name AS company_name, c.carrier_type
                     {base}
                     ORDER BY l.{sort_by} {sort_dir}
                     LIMIT ? OFFSET ?"""
        cursor.execute(select, params + [limit, offset])
        rows = cursor.fetchall()
        conn.close()
        return {"total": total, "page": page, "limit": limit, "records": [dict(r) for r in rows]}

    def search_deleted_licenses(self, search_term="", status_filter=None, activity_location=None,
                               page=1, limit=50):
        """Paginated search over deleted contracts only."""
        conn = self._get_connection()
        cursor = conn.cursor()

        base = """FROM licenses l
                  JOIN vehicles v ON l.vehicle_id = v.id
                  JOIN companies c ON v.company_id = c.id
                  WHERE l.is_deleted=1"""
        params = []

        if search_term:
            base += """ AND (CAST(l.id AS TEXT) LIKE ? OR l.record_number LIKE ? OR l.license_number LIKE ? OR l.registration_number LIKE ?
                         OR v.registration_number LIKE ? OR c.name LIKE ? OR l.driver_name LIKE ?)"""
            p = f"%{search_term}%"
            params.extend([p, p, p, p, p, p, p])

        if status_filter:
            base += " AND l.status=?"
            params.append(status_filter)

        if activity_location:
            base += " AND l.activity_location LIKE ?"
            params.append(f"%{activity_location}%")

        cursor.execute(f"SELECT COUNT(*) {base}", params)
        total = cursor.fetchone()[0]

        offset = (page - 1) * limit
        query = f"""SELECT l.id, l.record_number, l.license_number, l.driver_name, l.driver_phone,
                           l.signature_date, l.expiration_date, l.status,
                           l.activity_location, l.registration_number, l.deletion_days, l.created_at, l.vehicles_list, l.drivers_list,
                           v.registration_number AS vehicle_reg,
                           c.name AS company_name, c.carrier_type
                    {base}
                    ORDER BY l.created_at DESC
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
                      c.name AS company_name, c.carrier_type,
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

    def get_license_by_registration_number(self, registration_number):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM licenses WHERE registration_number=? AND is_deleted=0", (registration_number,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_license(self, license_id, **fields):
        if not fields:
            return None
        allowed = {"record_number","driver_name","driver_phone","license_number",
                   "signature_date","expiration_date","status","activity_location",
                   "registration_number","deletion_days", "vehicles_list", "drivers_list"}
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
            
            # Sync driver to drivers table automatically
            company_id = old_data.get("company_id")
            if company_id:
                d_name = fields.get("driver_name", old_data.get("driver_name"))
                d_phone = fields.get("driver_phone", old_data.get("driver_phone"))
                if d_name and d_name.strip():
                    self.add_driver(company_id, d_name, d_phone)
                
                d_list_str = fields.get("drivers_list", old_data.get("drivers_list"))
                if d_list_str:
                    try:
                        import json
                        parsed = json.loads(d_list_str) if isinstance(d_list_str, str) else d_list_str
                        if isinstance(parsed, list):
                            for d in parsed:
                                n = d.get("name")
                                p = d.get("phone")
                                if n and n.strip():
                                    self.add_driver(company_id, n, p)
                    except Exception:
                        pass
        
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

    def get_expiring_licenses(self, start_days=0, end_days=30, limit=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        start_date = (datetime.now() + timedelta(days=start_days)).date()
        end_date = (datetime.now() + timedelta(days=end_days)).date()
        
        limit_clause = ""
        if limit is not None:
            try:
                limit_clause = f" LIMIT {int(limit)}"
            except ValueError:
                pass
                
        cursor.execute(
            f"""SELECT l.id, l.record_number, l.license_number, l.driver_name, l.expiration_date,
                      v.registration_number AS vehicle_reg, c.name AS company_name
               FROM licenses l
               JOIN vehicles v ON l.vehicle_id=v.id
               JOIN companies c ON v.company_id=c.id
               WHERE l.expiration_date BETWEEN ? AND ? AND l.status='active' AND l.is_deleted=0
               ORDER BY l.expiration_date ASC{limit_clause}""",
            (start_date, end_date)
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
        cursor.execute("SELECT COUNT(*) FROM vehicles WHERE is_deleted=0")
        total_vehicles = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT driver_name) FROM licenses WHERE driver_name IS NOT NULL AND is_deleted=0")
        total_drivers = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM licenses WHERE status='active' AND is_deleted=0")
        active_licenses = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM licenses WHERE status='expired' AND is_deleted=0")
        expired_licenses = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM companies WHERE is_deleted=0")
        total_companies = cursor.fetchone()[0]
        conn.close()
        result = {
            "total_vehicles": total_vehicles,
            "total_drivers": total_drivers,
            "active_licenses": active_licenses,
            "expired_licenses": expired_licenses,
            "total_companies": total_companies,
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
        # Contract type statistics are removed because the field is replaced by registration_number

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

        conn.close()
        result = {
            "by_carrier": by_carrier,
            "by_status": by_status,
            "expiring_soon": expiring_soon,
            "by_company": by_company,
            "by_location": by_location,
            "carrier_totals": {
                "total": total_carriers,
                "public": carriers_by_type.get("Public", 0),
                "private": carriers_by_type.get("Private", 0),
                "active": active_carriers,
                "inactive": inactive_carriers,
            }
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

    def get_max_record_number(self) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT record_number FROM licenses")
        rows = cursor.fetchall()
        conn.close()
        max_num = 0
        for (val,) in rows:
            if not val:
                continue
            digits = "".join(c for c in str(val) if c.isdigit())
            if digits:
                try:
                    num = int(digits)
                    if num > max_num:
                        max_num = num
                except (ValueError, TypeError):
                    pass
        return max_num


