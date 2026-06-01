"""
License Service — Orchestrates complex operations for license management.
Implements the Service Layer pattern to decouple API from Database logic.
"""

from typing import Dict, Any
from database.connection_handler import Database
from services.business_rules_engine import BusinessRules

class LicenseService:
    def __init__(self, db: Database):
        self.db = db
        self.rules = BusinessRules(db)

    def create_complete_license(self, data: Dict[str, Any]) -> int:
        """
        Orchestrates the creation of a license, including its dependencies.
        1. Validates Business Rules.
        2. Finds or creates Company.
        3. Finds or creates Vehicle.
        4. Creates Route.
        5. Registers License.
        6. Logs Audit Entry.
        """
        # This method is intentionally the only place that composes the full license
        # workflow. Keeping the orchestration here prevents the API layer from having
        # to know about company, vehicle, route, hazmat, and audit sequencing.
        # If this were split across controllers, the create flow would become brittle
        # and inconsistent because each caller would have to reimplement the same order.
        # 1. Validation
        self.rules.validate_license_creation(data)

        # 2. Company Management
        company_name = str(data.get("company_name") or "").strip()
        existing_companies = self.db.get_companies()
        existing_company = next(
            (c for c in existing_companies if c["name"].strip().lower() == company_name.lower()),
            None
        )
        if existing_company:
            company_id = existing_company["id"]
        else:
            company_id = self.db.add_company(
                company_name,
                data.get("company_address", ""),
                data.get("carrier_type", "Public"),
                data.get("account_type", "Public")
            )

        # 3. Vehicle Management
        import json
        vehicles_list = data.get("vehicles_list")
        drivers_list = data.get("drivers_list")
        
        vehicles_list_str = json.dumps(vehicles_list) if isinstance(vehicles_list, (list, dict)) else (vehicles_list or None)
        drivers_list_str = json.dumps(drivers_list) if isinstance(drivers_list, (list, dict)) else (drivers_list or None)
        
        v_list = []
        if vehicles_list:
            try:
                v_list = json.loads(vehicles_list) if isinstance(vehicles_list, str) else vehicles_list
            except Exception:
                pass
                
        d_list = []
        if drivers_list:
            try:
                d_list = json.loads(drivers_list) if isinstance(drivers_list, str) else drivers_list
            except Exception:
                pass

        primary_vehicle_reg = None
        primary_vehicle_type = ""
        primary_vehicle_category = ""
        if v_list and len(v_list) > 0:
            primary_vehicle_reg = v_list[0].get("registration_number")
            primary_vehicle_type = v_list[0].get("type", "")
            primary_vehicle_category = v_list[0].get("category", "")
        else:
            primary_vehicle_reg = data.get("vehicle_reg")
            primary_vehicle_type = data.get("vehicle_type", "")
            primary_vehicle_category = data.get("vehicle_category", "")

        if not primary_vehicle_reg:
            primary_vehicle_reg = "UNKNOWN-VEHICLE"

        existing_vehicle = self.db.get_vehicle_by_registration(primary_vehicle_reg)
        if existing_vehicle:
            vehicle_id = existing_vehicle["id"]
        else:
            vehicle_id = self.db.add_vehicle(
                company_id,
                primary_vehicle_reg,
                primary_vehicle_type,
                primary_vehicle_category
            )

        if v_list and len(v_list) > 1:
            for veh in v_list[1:]:
                vr = veh.get("registration_number")
                vt = veh.get("type", "")
                vc = veh.get("category", "")
                if vr and not self.db.get_vehicle_by_registration(vr):
                    self.db.add_vehicle(company_id, vr, vt, vc)

        primary_driver_name = ""
        primary_driver_phone = ""
        if d_list and len(d_list) > 0:
            primary_driver_name = d_list[0].get("name", "")
            primary_driver_phone = d_list[0].get("phone", "")
        else:
            primary_driver_name = data.get("driver_name", "")
            primary_driver_phone = data.get("driver_phone", "")

        # 4. Route Management
        route_id = self.db.add_route(
            data.get("route_origin", ""),
            data.get("route_dest", ""),
            data.get("route_checkpoints", "")
        )

        # 5. Hazmat (Optional)
        if str(data.get("hazmat_type") or "").strip():
            self.db.add_hazmat(vehicle_id, data["hazmat_type"])

        license_num = data.get("license_number") or f"LIC-{data['record_number']}"

        # 6. License Registration
        license_id = self.db.add_license(
            vehicle_id=vehicle_id,
            route_id=route_id,
            record_number=data["record_number"],
            driver_name=primary_driver_name,
            driver_phone=primary_driver_phone,
            license_number=license_num,
            signature_date=data.get("signature_date", ""),
            expiration_date=data.get("expiration_date", ""),
            activity_location=data.get("activity_location"),
            registration_number=data.get("registration_number"),
            deletion_days=data.get("deletion_days"),
            vehicles_list=vehicles_list_str,
            drivers_list=drivers_list_str
        )

        # 7. Audit Log
        self.db.add_audit_log("CREATE", "licenses", license_id, new_values=data)

        return license_id

    def soft_delete_license(self, license_id: int):
        """Service wrapper for soft delete with audit.

        Keeping this wrapper in the service layer means callers always go through the
        same deletion policy. If removed, the API could bypass audit logging or later
        add hard-delete behavior by accident.
        """
        self.db.soft_delete_license(license_id)

    def restore_license(self, license_id: int):
        """Service wrapper for restore with business rule check.

        Restoration is guarded here so the business rule check happens before the
        database mutation. That protects the integrity of restored records because a
        deleted company or vehicle would make the restored license invalid.
        """
        if not self.rules.can_restore_license(license_id):
            raise ValueError("Cannot restore license: Associated vehicle or company is missing or deleted.")
        self.db.restore_license(license_id)

    def get_next_record_number(self) -> int:
        """Calculates next_record_number = max(record_number) + 1 from the database."""
        return self.db.get_max_record_number() + 1
