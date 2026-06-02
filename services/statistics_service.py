import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from database.connection_handler import Database


# ---------------------------------------------------------
# In-Memory Cache to prevent heavy re-computations
# Performance requirement: "Statistics must load FAST"
# ---------------------------------------------------------
CACHE_STORE = {
    "data": None,
    "timestamp": 0,
    "date_str": None
}
CACHE_TTL_SECONDS = 300  # Cache lives for 5 minutes

class StatisticsService:
    """
    What it does: Processes and structures raw database records into analytics-ready JSON.
    Why it exists: To offload computation from the SQLite engine and Electron frontend, 
                   ensuring fast, responsive dashboard rendering.
    What data it uses: companies, licenses, and vehicles tables.
    """
    def __init__(self):
        self.db = Database()

    def clear_cache(self):
        """Invalidates the in-memory cache to ensure statistics update in real-time on mutations."""
        global CACHE_STORE
        CACHE_STORE["data"] = None
        CACHE_STORE["timestamp"] = 0
        CACHE_STORE["date_str"] = None

    def get_dashboard_statistics(self, start_date=None, end_date=None):
        """
        Fetches all required data for the 3-tier statistics dashboard.
        Utilizes caching for the default dashboard request to return data instantly.
        If start_date and end_date are provided, caching is bypassed.
        """
        current_time = time.time()
        today_str = datetime.today().strftime('%Y-%m-%d')
        
        # Check if we should clear cache due to date change (Requirement: Cache must invalidate on date changes)
        global CACHE_STORE
        if CACHE_STORE["date_str"] != today_str:
            CACHE_STORE["data"] = None
            CACHE_STORE["date_str"] = today_str
            CACHE_STORE["timestamp"] = 0

        # Return cached data if still valid and no custom range is requested
        if not start_date and not end_date:
            if CACHE_STORE["data"] and (current_time - CACHE_STORE["timestamp"] < CACHE_TTL_SECONDS):
                return CACHE_STORE["data"]

        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            # Helper to validate and convert date strings
            def validate_date(d_str):
                try:
                    return datetime.strptime(d_str, "%Y-%m-%d").date()
                except Exception:
                    raise ValueError(f"Invalid date format: {d_str}. Expected YYYY-MM-DD.")

            # 1. TOP SECTION: KPI CARDS & MUNICIPALITY ANALYSIS
            if start_date and end_date:
                # Recalculate everything based ONLY on the custom date range
                start_dt = validate_date(start_date)
                end_dt = validate_date(end_date)
                if end_dt < start_dt:
                    raise ValueError("End Date cannot be earlier than Start Date.")

                cursor.execute("SELECT COUNT(*) FROM companies WHERE is_deleted=0 AND DATE(created_at) BETWEEN ? AND ?", (start_date, end_date))
                total_carriers = cursor.fetchone()[0]

                cursor.execute("SELECT carrier_type, COUNT(*) FROM companies WHERE is_deleted=0 AND DATE(created_at) BETWEEN ? AND ? GROUP BY carrier_type", (start_date, end_date))
                carrier_types = dict(cursor.fetchall())
                public_carriers = carrier_types.get("Public", 0)
                private_carriers = carrier_types.get("Private", 0)

                cursor.execute("SELECT COUNT(*) FROM licenses WHERE is_deleted=0 AND DATE(signature_date) BETWEEN ? AND ?", (start_date, end_date))
                total_licenses = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM licenses WHERE status='active' AND is_deleted=0 AND DATE(signature_date) BETWEEN ? AND ?", (start_date, end_date))
                active_licenses = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM licenses WHERE status='expired' AND is_deleted=0 AND DATE(signature_date) BETWEEN ? AND ?", (start_date, end_date))
                expired_licenses = cursor.fetchone()[0]

                active_query = """
                    SELECT COUNT(DISTINCT c.id) 
                    FROM companies c
                    JOIN vehicles v ON c.id = v.company_id
                    JOIN licenses l ON v.id = l.vehicle_id
                    WHERE l.status = 'active' AND l.is_deleted=0 AND c.is_deleted=0
                      AND DATE(l.signature_date) BETWEEN ? AND ?
                """
                cursor.execute(active_query, (start_date, end_date))
                active_carriers = cursor.fetchone()[0]
                inactive_carriers = max(0, total_carriers - active_carriers)

                cursor.execute("""
                    SELECT activity_location,
                           CASE WHEN status = 'active' THEN 1 ELSE 0 END as is_active
                    FROM licenses
                    WHERE is_deleted = 0 AND activity_location IS NOT NULL
                      AND DATE(signature_date) BETWEEN ? AND ?
                """, (start_date, end_date))
                license_rows = cursor.fetchall()
            else:
                # Default live counts (KPIs represent overall active/expired and all companies)
                cursor.execute("SELECT COUNT(*) FROM companies WHERE is_deleted=0")
                total_carriers = cursor.fetchone()[0]

                cursor.execute("SELECT carrier_type, COUNT(*) FROM companies WHERE is_deleted=0 GROUP BY carrier_type")
                carrier_types = dict(cursor.fetchall())
                public_carriers = carrier_types.get("Public", 0)
                private_carriers = carrier_types.get("Private", 0)

                cursor.execute("SELECT COUNT(*) FROM licenses WHERE is_deleted=0")
                total_licenses = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM licenses WHERE status='active' AND is_deleted=0")
                active_licenses = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM licenses WHERE status='expired' AND is_deleted=0")
                expired_licenses = cursor.fetchone()[0]

                active_query = """
                    SELECT COUNT(DISTINCT c.id) 
                    FROM companies c
                    JOIN vehicles v ON c.id = v.company_id
                    JOIN licenses l ON v.id = l.vehicle_id
                    WHERE l.status = 'active' AND l.is_deleted=0 AND c.is_deleted=0
                """
                cursor.execute(active_query)
                active_carriers = cursor.fetchone()[0]
                inactive_carriers = max(0, total_carriers - active_carriers)

                cursor.execute("""
                    SELECT activity_location,
                           CASE WHEN status = 'active' THEN 1 ELSE 0 END as is_active
                    FROM licenses
                    WHERE is_deleted = 0 AND activity_location IS NOT NULL
                """)
                license_rows = cursor.fetchall()

            # Load Sétif communes from setif_communes.json (single source of truth)
            communes_file = Path(__file__).parent.parent / "frontend" / "data" / "setif_communes.json"
            setif_communes = []
            if communes_file.exists():
                try:
                    with open(communes_file, "r", encoding="utf-8") as f:
                        setif_communes = json.load(f).get("communes", [])
                except Exception as e:
                    print("Error loading setif communes in stats service:", e)

            municipality_stats = {commune: {"total": 0, "active": 0, "inactive": 0} for commune in setif_communes}
            for row in license_rows:
                loc = row["activity_location"]
                if loc in municipality_stats:
                    municipality_stats[loc]["total"] += 1
                    if row["is_active"] == 1:
                        municipality_stats[loc]["active"] += 1
                    else:
                        municipality_stats[loc]["inactive"] += 1

            # Only include municipalities with total > 0 to keep statistics clean
            municipality_stats = {k: v for k, v in municipality_stats.items() if v["total"] > 0}

            # 2. ACTIVITY ANALYSIS
            activity = {}
            if start_date and end_date:
                # Custom period activity series calculation
                start_dt = validate_date(start_date)
                end_dt = validate_date(end_date)
                delta_days = (end_dt - start_dt).days

                if delta_days <= 30:
                    # Daily granularity (show each day in the range)
                    granularity = "daily"
                    dates = [start_dt + timedelta(days=i) for i in range(delta_days + 1)]
                    timeline_strs = [d.strftime('%Y-%m-%d') for d in dates]

                    cursor.execute("""
                        SELECT DATE(signature_date) AS label, COUNT(*) AS count
                        FROM licenses
                        WHERE is_deleted = 0
                          AND DATE(signature_date) BETWEEN ? AND ?
                        GROUP BY label
                    """, (start_date, end_date))
                    db_results = dict(cursor.fetchall())
                    custom_activity = [{"date": d, "count": db_results.get(d, 0)} for d in timeline_strs]

                elif delta_days <= 180:
                    # Weekly granularity (show W##)
                    granularity = "weekly"
                    dates = [start_dt + timedelta(days=i) for i in range(delta_days + 1)]
                    timeline_strs = sorted(list(set(d.strftime('%Y-W%W') for d in dates)))

                    cursor.execute("""
                        SELECT strftime('%Y-W%W', signature_date) AS label, COUNT(*) AS count
                        FROM licenses
                        WHERE is_deleted = 0
                          AND DATE(signature_date) BETWEEN ? AND ?
                        GROUP BY label
                    """, (start_date, end_date))
                    db_results = dict(cursor.fetchall())
                    custom_activity = [{"week": w, "count": db_results.get(w, 0)} for w in timeline_strs]

                else:
                    # Monthly granularity (show YYYY-MM)
                    granularity = "monthly"
                    dates = [start_dt + timedelta(days=i) for i in range(delta_days + 1)]
                    timeline_strs = sorted(list(set(d.strftime('%Y-%m') for d in dates)))

                    cursor.execute("""
                        SELECT strftime('%Y-%m', signature_date) AS label, COUNT(*) AS count
                        FROM licenses
                        WHERE is_deleted = 0
                          AND DATE(signature_date) BETWEEN ? AND ?
                        GROUP BY label
                    """, (start_date, end_date))
                    db_results = dict(cursor.fetchall())
                    custom_activity = [{"month": m, "count": db_results.get(m, 0)} for m in timeline_strs]

                activity["custom"] = custom_activity
                activity["granularity"] = granularity
            else:
                # Default Live Statistics (Requirement: weekly = last 7 days; monthly = current month; yearly = current year)
                today = datetime.today().date()

                # A. Weekly: Last 7 days day-by-day (e.g. May 27 -> June 2)
                weekly_dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
                weekly_strs = [d.strftime('%Y-%m-%d') for d in weekly_dates]
                cursor.execute("""
                    SELECT DATE(signature_date) AS label, COUNT(*) AS count
                    FROM licenses
                    WHERE is_deleted = 0
                      AND DATE(signature_date) BETWEEN ? AND ?
                    GROUP BY label
                """, (weekly_strs[0], weekly_strs[-1]))
                weekly_results = dict(cursor.fetchall())
                weekly_activity = [{"week": d, "count": weekly_results.get(d, 0)} for d in weekly_strs]

                # B. Monthly: Current month day-by-day (e.g. June 1 -> June 3)
                first_day_of_month = today.replace(day=1)
                monthly_delta = (today - first_day_of_month).days
                monthly_dates = [first_day_of_month + timedelta(days=i) for i in range(monthly_delta + 1)]
                monthly_strs = [d.strftime('%Y-%m-%d') for d in monthly_dates]
                cursor.execute("""
                    SELECT DATE(signature_date) AS label, COUNT(*) AS count
                    FROM licenses
                    WHERE is_deleted = 0
                      AND DATE(signature_date) BETWEEN ? AND ?
                    GROUP BY label
                """, (monthly_strs[0], monthly_strs[-1]))
                monthly_results = dict(cursor.fetchall())
                monthly_activity = [{"month": d, "count": monthly_results.get(d, 0)} for d in monthly_strs]

                # C. Yearly: Current year month-by-month (e.g. Jan -> current month)
                first_day_of_year = today.replace(month=1, day=1)
                yearly_months = [f"{today.year}-{m:02d}" for m in range(1, today.month + 1)]
                cursor.execute("""
                    SELECT strftime('%Y-%m', signature_date) AS label, COUNT(*) AS count
                    FROM licenses
                    WHERE is_deleted = 0
                      AND DATE(signature_date) BETWEEN ? AND ?
                    GROUP BY label
                """, (first_day_of_year.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')))
                yearly_results = dict(cursor.fetchall())
                yearly_activity = [{"year": m, "count": yearly_results.get(m, 0)} for m in yearly_months]

                # D. Daily: Last 30 days day-by-day
                daily_dates = [today - timedelta(days=i) for i in range(29, -1, -1)]
                daily_strs = [d.strftime('%Y-%m-%d') for d in daily_dates]
                cursor.execute("""
                    SELECT DATE(signature_date) AS label, COUNT(*) AS count
                    FROM licenses
                    WHERE is_deleted = 0
                      AND DATE(signature_date) BETWEEN ? AND ?
                    GROUP BY label
                """, (daily_strs[0], daily_strs[-1]))
                daily_results = dict(cursor.fetchall())
                daily_activity = [{"date": d, "count": daily_results.get(d, 0)} for d in daily_strs]

                activity["daily"] = daily_activity
                activity["weekly"] = weekly_activity
                activity["monthly"] = monthly_activity
                activity["yearly"] = yearly_activity

            # Forecast of expiries
            forecast = self._get_expiry_forecast(cursor)
            activity["forecast"] = forecast

            payload = {
                "kpis": {
                    "total": total_carriers,
                    "active": active_carriers,
                    "inactive": inactive_carriers,
                    "public": public_carriers,
                    "private": private_carriers,
                    "total_licenses": total_licenses,
                    "active_licenses": active_licenses,
                    "expired_licenses": expired_licenses
                },
                "municipalities": municipality_stats,
                "activity": activity
            }

            # Cache the default payload
            if not start_date and not end_date:
                CACHE_STORE["data"] = payload
                CACHE_STORE["timestamp"] = current_time
                CACHE_STORE["date_str"] = today_str

            return payload
        finally:
            conn.close()

    def _get_expiry_forecast(self, cursor):
        """Forecast licenses expiring in the next 3 months (30, 60, 90 days)."""
        forecasts = []
        for days in [30, 60, 90]:
            cursor.execute("""
                SELECT COUNT(*) FROM licenses 
                WHERE is_deleted=0 AND status='active'
                AND DATE(expiration_date) <= DATE('now', ?)
            """, (f"+{days} days",))
            count = cursor.fetchone()[0]
            forecasts.append({"label": f"{days} Days", "count": count})
        return forecasts