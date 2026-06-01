import time
import json
from pathlib import Path
from datetime import datetime
from database.connection_handler import Database


# ---------------------------------------------------------
# In-Memory Cache to prevent heavy re-computations
# Performance requirement: "Statistics must load FAST"
# ---------------------------------------------------------
CACHE_STORE = {
    "data": None,
    "timestamp": 0
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

    def get_dashboard_statistics(self):
        """
        Fetches all required data for the 3-tier statistics dashboard.
        Utilizes caching to return data instantly on subsequent loads.
        """
        # The dashboard is read far more often than it is mutated, so a small
        # in-memory cache is a deliberate trade-off. If this cache were removed,
        # every dashboard refresh would recompute the same joins and aggregates.
        current_time = time.time()
        
        # Return cached data if still valid
        if CACHE_STORE["data"] and (current_time - CACHE_STORE["timestamp"] < CACHE_TTL_SECONDS):
            return CACHE_STORE["data"]

        conn = self.db._get_connection()
        cursor = conn.cursor()

        try:
            # 1. TOP SECTION: KPI CARDS
            cursor.execute("SELECT COUNT(*) FROM companies WHERE is_deleted=0")
            total_carriers = cursor.fetchone()[0]

            cursor.execute("SELECT carrier_type, COUNT(*) FROM companies WHERE is_deleted=0 GROUP BY carrier_type")
            carrier_types = dict(cursor.fetchall())
            public_carriers = carrier_types.get("Public", 0)
            private_carriers = carrier_types.get("Private", 0)

            # License counts
            cursor.execute("SELECT COUNT(*) FROM licenses WHERE is_deleted=0")
            total_licenses = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM licenses WHERE status='active' AND is_deleted=0")
            active_licenses = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM licenses WHERE status='expired' AND is_deleted=0")
            expired_licenses = cursor.fetchone()[0]

            # This join is the key business metric for the UI: it counts companies
            # that currently have at least one active license attached through a
            # vehicle. Removing the DISTINCT would overcount companies with multiple
            # vehicles or multiple licenses.
            active_query = """
                SELECT COUNT(DISTINCT c.id) 
                FROM companies c
                JOIN vehicles v ON c.id = v.company_id
                JOIN licenses l ON v.id = l.vehicle_id
                WHERE l.status = 'active' AND l.is_deleted=0 AND c.is_deleted=0
            """
            cursor.execute(active_query)
            active_carriers = cursor.fetchone()[0]
            inactive_carriers = total_carriers - active_carriers

            # 2. MIDDLE SECTION & BOTTOM SECTION: MUNICIPALITY ANALYSIS
            # Load Sétif communes from setif_communes.json (single source of truth)
            communes_file = Path(__file__).parent.parent / "frontend" / "data" / "setif_communes.json"
            setif_communes = []
            if communes_file.exists():
                try:
                    with open(communes_file, "r", encoding="utf-8") as f:
                        setif_communes = json.load(f).get("communes", [])
                except Exception as e:
                    print("Error loading setif communes in stats service:", e)

            # Query active/inactive licenses by activity_location
            cursor.execute("""
                SELECT activity_location,
                       CASE WHEN status = 'active' THEN 1 ELSE 0 END as is_active
                FROM licenses
                WHERE is_deleted = 0 AND activity_location IS NOT NULL
            """)
            license_rows = cursor.fetchall()

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

            # 3. BOTTOM SECTION: ACTIVITY OVER TIME
            weekly_activity = self._get_activity_series(cursor, "strftime('%Y-W%W', signature_date)", "week", 180)
            monthly_activity = self._get_activity_series(cursor, "strftime('%Y-%m', signature_date)", "month", 365)
            yearly_activity = self._get_activity_series(cursor, "strftime('%Y', signature_date)", "year", 3650)
            daily_activity = self._get_activity_series(cursor, "date(signature_date)", "date", 30)
            
            # 4. PREDICTIVE INSIGHTS: Forecasting Expiries
            forecast = self._get_expiry_forecast(cursor)

            activity = {
                "daily": daily_activity,
                "weekly": weekly_activity,
                "monthly": monthly_activity,
                "yearly": yearly_activity,
                "forecast": forecast
            }

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

            CACHE_STORE["data"] = payload
            CACHE_STORE["timestamp"] = current_time
            return payload
        finally:
            conn.close()

    def _get_activity_series(self, cursor, group_expression, label_key, window_days):
        query = f"""
            SELECT {group_expression} AS label, COUNT(*) AS count
            FROM licenses
            WHERE is_deleted = 0
              AND signature_date >= DATE('now', '-{window_days} days')
            GROUP BY label
            ORDER BY label ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        return [{label_key: row["label"], "count": row["count"]} for row in rows]

    def _get_expiry_forecast(self, cursor):
        """Forecast licenses expiring in the next 3 months (30, 60, 90 days).

        This is a lightweight business-facing projection rather than a true model.
        It exists to give operators a near-term workload signal without introducing a
        separate analytics dependency.
        """
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