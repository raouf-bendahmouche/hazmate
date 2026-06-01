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
        Rule 1: Cannot add driver without a license number (already in Pydantic)
        Rule 2: Cannot create contract without vehicle registration.
        Rule 3: Record number must be unique (checked in DB, but can be here too).
        """
        import json
        has_vehicle = False
        if data.get("vehicle_reg"):
            has_vehicle = True
        elif data.get("vehicles_list"):
            try:
                v_list = json.loads(data["vehicles_list"]) if isinstance(data["vehicles_list"], str) else data["vehicles_list"]
                if v_list and len(v_list) > 0 and v_list[0].get("registration_number"):
                    has_vehicle = True
            except Exception:
                pass
        
        if not has_vehicle:
            raise ValueError("Business Rule Violation: Vehicle registration is mandatory for any contract.")

        # Date Validation: End Date (expiration_date) must not be earlier than Start Date (signature_date)
        sig_date = data.get("signature_date")
        exp_date = data.get("expiration_date")
        if sig_date and exp_date:
            if str(exp_date) < str(sig_date):
                raise ValueError("Validation Error: Expiration date (End Date) cannot be earlier than signature date (Start Date).")

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
            
        # Check company
        company = self.db.get_company_by_id(vehicle["company_id"])
        if not company or company["is_deleted"]:
            return False
            
        return True
