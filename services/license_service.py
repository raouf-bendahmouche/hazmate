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
        company_reg = str(data.get("company_reg") or "").strip() or None
        if company_reg:
            existing_company = self.db.get_company_by_registration(company_reg)
            if existing_company:
                company_id = existing_company["id"]
            else:
                company_id = self.db.add_company(
                    data["company_name"], company_reg,
                    data.get("company_address", ""),
                    data.get("carrier_type", "Public"),
                    data.get("account_type", "Public")
                )
        else:
            company_id = self.db.add_company(
                data["company_name"], None,
                data.get("company_address", ""),
                data.get("carrier_type", "Public"),
                data.get("account_type", "Public")
            )

        # 3. Vehicle Management
        existing_vehicle = self.db.get_vehicle_by_registration(data["vehicle_reg"])
        if existing_vehicle:
            vehicle_id = existing_vehicle["id"]
        else:
            vehicle_id = self.db.add_vehicle(
                company_id,
                data["vehicle_reg"],
                data.get("vehicle_type", ""),
                data.get("vehicle_category", "")
            )

        # 4. Route Management
        route_id = self.db.add_route(
            data.get("route_origin", ""),
            data.get("route_dest", ""),
            data.get("route_checkpoints", "")
        )

        # 5. Hazmat (Optional)
        if str(data.get("hazmat_type") or "").strip():
            self.db.add_hazmat(vehicle_id, data["hazmat_type"])

        # 6. License Registration
        license_id = self.db.add_license(
            vehicle_id=vehicle_id,
            route_id=route_id,
            record_number=data["record_number"],
            driver_name=data.get("driver_name", ""),
            driver_phone=data.get("driver_phone", ""),
            license_number=data["license_number"],
            signature_date=data.get("signature_date", ""),
            expiration_date=data.get("expiration_date", ""),
            activity_location=data.get("activity_location"),
            contract_type=data.get("contract_type"),
            deletion_days=data.get("deletion_days")
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
