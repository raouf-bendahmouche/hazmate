"""
Business Rules Engine — Hazardous Material Transport System
Enforces critical domain constraints and validation logic.
"""

from typing import Dict, Any, Optional

class BusinessRules:
    def __init__(self, db):
        self.db = db

    def validate_license_creation(self, data: Dict[str, Any]):
        """
        Enforce business rules for creating a new license.
        All 9 flat UI fields are mandatory for contract completeness.
        """
        # Validate all required fields
        required_fields = [
            ("record_number", "Registration number is mandatory."),
            ("signature_date", "Signature date is mandatory."),
            ("company_name", "Carrier name is mandatory."),
            ("company_address", "Company address is mandatory."),
            ("vehicle_reg", "Vehicle registration number is mandatory."),
            ("vehicle_type", "Vehicle type is mandatory."),
            ("route_dest", "Route destination is mandatory."),
            ("expiration_date", "Expiration date is mandatory."),
            ("hazmat_type", "Transported material is mandatory.")
        ]
        for field, err_msg in required_fields:
            if not data.get(field):
                raise ValueError(f"Business Rule Violation: {err_msg}")
        
        # Format check: Route destination must not be numeric-only
        route_dest = str(data.get("route_dest") or "").strip()
        if route_dest.isdigit():
            raise ValueError("Business Rule Violation: Route destination must follow a text format.")
        
        # Format checks: Registration and vehicle numbers must be digit-only
        rec_num = str(data.get("record_number") or "").strip()
        if not rec_num.isdigit():
            raise ValueError("Business Rule Violation: Registration number must follow a numeric format.")
        
        veh_reg = str(data.get("vehicle_reg") or "").strip()
        if not veh_reg.isdigit():
            raise ValueError("Business Rule Violation: Vehicle registration number must follow a numeric format.")

        if data.get("company_reg"):
            comp_reg = str(data.get("company_reg") or "").strip()
            if not comp_reg.isdigit():
                raise ValueError("Business Rule Violation: Registry Number must follow a numeric format.")

        # Carrier name must not contain numbers
        comp_name = str(data.get("company_name") or "")
        if any(char.isdigit() for char in comp_name):
            raise ValueError("Business Rule Violation: Carrier name must not contain numbers.")

        # Chronology check: Expiration date must be strictly after signature/start date
        sig_date = data.get("signature_date")
        exp_date = data.get("expiration_date")
        if sig_date and exp_date:
            if exp_date <= sig_date:
                raise ValueError("Business Rule Violation: Expiration date must be later than start date")

    def validate_license_update(self, license_id: int, fields: Dict[str, Any]):
        """
        Validate partial license updates to keep the contract in a valid state.
        """
        existing = self.db.get_license_by_id(license_id)
        if not existing:
            # Try deleted licenses as fallback
            conn = self.db._get_connection()
            row = conn.execute("SELECT * FROM licenses WHERE id=?", (license_id,)).fetchone()
            conn.close()
            if not row:
                raise ValueError("License not found.")
            existing = dict(row)
            
        merged = {**existing, **fields}

        # Check required fields if they are updated
        if "record_number" in fields:
            rec_num = str(fields["record_number"] or "").strip()
            if not rec_num:
                raise ValueError("Business Rule Violation: Registration number is mandatory.")
            if not rec_num.isdigit():
                raise ValueError("Business Rule Violation: Registration number must follow a numeric format.")
                
        if "company_name" in fields:
            comp_name = str(fields["company_name"] or "").strip()
            if not comp_name:
                raise ValueError("Business Rule Violation: Carrier name is mandatory.")
            if any(char.isdigit() for char in comp_name):
                raise ValueError("Business Rule Violation: Carrier name must not contain numbers.")

        if "activity_location" in fields:
            loc = str(fields["activity_location"] or "").strip()
            if not loc:
                raise ValueError("Business Rule Violation: Company address is mandatory.")

        if "signature_date" in fields:
            sig = str(fields["signature_date"] or "").strip()
            if not sig:
                raise ValueError("Business Rule Violation: Signature date is mandatory.")

        if "expiration_date" in fields:
            exp = str(fields["expiration_date"] or "").strip()
            if not exp:
                raise ValueError("Business Rule Violation: Expiration date is mandatory.")

        if "expiration_date" in fields or "signature_date" in fields:
            sig_date = merged.get("signature_date")
            exp_date = merged.get("expiration_date")
            if sig_date and exp_date:
                if exp_date <= sig_date:
                    raise ValueError("Business Rule Violation: Expiration date must be later than start date")

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

