"""
Business Rules Engine — Hazardous Material Transport System
Enforces critical domain constraints and validation logic.
"""

from typing import Dict, Any, Optional
from database.connection_handler import Database

class BusinessRules:
    def __init__(self, db: Database):
        self.db = db

    def validate_license_creation(self, data: Dict[str, Any]):
        """
        Enforce business rules for creating a new license.
        Rule 1: Cannot create contract without vehicle registration.
        Rule 2: Record number is mandatory.
        """
        if not data.get("vehicle_reg"):
            raise ValueError("Business Rule Violation: Vehicle registration is mandatory for any contract.")
        
        if not data.get("license_number"):
            raise ValueError("Business Rule Violation: Registration number is mandatory.")

    def can_restore_license(self, license_id: int) -> bool:
        """Rule: A license can only be restored if the associated vehicle and company are not permanently deleted."""
        license_data = self.db.get_license_by_id(license_id)
        if not license_data:
            # Check if it's in deleted licenses
            conn = self.db._get_connection()
            row = conn.execute("SELECT * FROM licenses WHERE id=?", (license_id,)).fetchone()
            conn.close()
            if not row:
                return False
            license_data = dict(row)
        
        # Check vehicle
        vehicle = self.db.get_vehicle_by_id(license_data["vehicle_id"])
        if not vehicle or vehicle["is_deleted"]:
            return False
            
        return True
