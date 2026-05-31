import os
import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from database.connection_handler import Database
from services.business_rules_engine import BusinessRules
from services.license_service import LicenseService

class TestValidationAndDataIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db_path = Path(__file__).parent.parent / "database" / "test_licenses_validation.db"
        # Delete if exists from previous run
        if cls.test_db_path.exists():
            try:
                os.remove(cls.test_db_path)
            except OSError:
                pass
        cls.db = Database(db_file=cls.test_db_path)
        cls.rules = BusinessRules(cls.db)
        cls.service = LicenseService(cls.db)

    @classmethod
    def tearDownClass(cls):
        # Clean up database file and WAL logs
        if cls.test_db_path.exists():
            try:
                os.remove(cls.test_db_path)
                wal_path = cls.test_db_path.with_suffix(".db-wal")
                if wal_path.exists():
                    os.remove(wal_path)
                shm_path = cls.test_db_path.with_suffix(".db-shm")
                if shm_path.exists():
                    os.remove(shm_path)
            except OSError:
                pass

    def get_valid_payload(self, record_number="12345", vehicle_reg="776655"):
        return {
            "record_number": record_number,
            "signature_date": "2026-05-01",
            "company_name": "Safe Transport Inc",
            "company_reg": "98765",
            "company_address": "Setif, Setif",
            "vehicle_reg": vehicle_reg,
            "vehicle_type": "Truck",
            "vehicle_category": "Category A",
            "route_origin": "",
            "route_dest": "Algiers",
            "expiration_date": "2027-05-01",
            "hazmat_type": "Explosive Class 1",
            "license_number": f"LIC-{record_number}",
            "carrier_type": "Public",
            "account_type": "Public",
            "contract_type": "Public"
        }

    def test_valid_payload_success(self):
        """Verify that a valid contract is successfully created."""
        payload = self.get_valid_payload(record_number="10001", vehicle_reg="50001")
        try:
            lic_id = self.service.create_complete_license(payload)
            self.assertIsNotNone(lic_id)
            # Retrieve to confirm
            lic = self.db.get_license_by_id(lic_id)
            self.assertEqual(lic["record_number"], "10001")
        except ValueError as e:
            self.fail(f"Valid payload failed validation: {e}")

    def test_missing_required_fields(self):
        """Verify that leaving any of the required fields empty throws a ValueError."""
        required_keys = [
            "record_number", "signature_date", "company_name", "company_address",
            "vehicle_reg", "vehicle_type", "route_dest",
            "expiration_date", "hazmat_type"
        ]
        
        for key in required_keys:
            payload = self.get_valid_payload()
            # Ensure unique record_number/vehicle_reg to avoid duplicate issues on success cases
            payload["record_number"] = f"99{key[:4]}"
            payload["vehicle_reg"] = f"88{key[:4]}"
            payload[key] = ""
            
            with self.assertRaises(ValueError) as ctx:
                self.service.create_complete_license(payload)
            self.assertIn("mandatory", str(ctx.exception))

    def test_route_destination_format(self):
        """Verify that route_dest must not be numeric-only."""
        payload = self.get_valid_payload()
        payload["route_dest"] = "12345"
        
        with self.assertRaises(ValueError) as ctx:
            self.service.create_complete_license(payload)
        self.assertIn("Route destination must follow a text format", str(ctx.exception))

    def test_registration_number_format(self):
        """Verify that record_number must follow a numeric format (digits-only)."""
        payload = self.get_valid_payload()
        payload["record_number"] = "123A"
        
        with self.assertRaises(ValueError) as ctx:
            self.service.create_complete_license(payload)
        self.assertIn("Registration number must follow a numeric format", str(ctx.exception))

    def test_vehicle_registration_format(self):
        """Verify that vehicle registration must follow a numeric format (digits-only)."""
        payload = self.get_valid_payload()
        payload["record_number"] = "22334"
        payload["vehicle_reg"] = "77A66"
        
        with self.assertRaises(ValueError) as ctx:
            self.service.create_complete_license(payload)
        self.assertIn("Vehicle registration number must follow a numeric format", str(ctx.exception))

    def test_company_registration_format(self):
        """Verify that company registration (Registry Number) must be numeric if provided."""
        payload = self.get_valid_payload()
        payload["record_number"] = "33445"
        payload["vehicle_reg"] = "998877"
        payload["company_reg"] = "REG123"
        
        with self.assertRaises(ValueError) as ctx:
            self.service.create_complete_license(payload)
        self.assertIn("Registry Number must follow a numeric format", str(ctx.exception))

    def test_carrier_name_contains_numbers(self):
        """Verify that carrier name must reject numbers."""
        payload = self.get_valid_payload()
        payload["record_number"] = "44556"
        payload["vehicle_reg"] = "112233"
        payload["company_name"] = "Carrier 123 Ltd"
        
        with self.assertRaises(ValueError) as ctx:
            self.service.create_complete_license(payload)
        self.assertIn("Carrier name must not contain numbers", str(ctx.exception))

    def test_date_chronology(self):
        """Verify that license expiration date must be after signature date."""
        payload = self.get_valid_payload()
        payload["record_number"] = "55667"
        payload["vehicle_reg"] = "445566"
        
        # Test expiration earlier than signature
        payload["signature_date"] = "2026-05-31"
        payload["expiration_date"] = "2026-05-15"
        with self.assertRaises(ValueError) as ctx:
            self.service.create_complete_license(payload)
        self.assertIn("Expiration date must be later than start date", str(ctx.exception))

        # Test expiration equal to signature
        payload["expiration_date"] = "2026-05-31"
        with self.assertRaises(ValueError) as ctx:
            self.service.create_complete_license(payload)
        self.assertIn("Expiration date must be later than start date", str(ctx.exception))

    def test_update_validations(self):
        """Verify that updates enforce format, presence, and chronology constraints."""
        # 1. Create a valid initial license
        payload = self.get_valid_payload()
        payload["record_number"] = "77889"
        payload["vehicle_reg"] = "667788"
        lic_id = self.service.create_complete_license(payload)

        # 2. Update with invalid chronology (expected to fail)
        with self.assertRaises(ValueError) as ctx:
            self.service.rules.validate_license_update(lic_id, {"expiration_date": "2025-01-01"})
        self.assertIn("Expiration date must be later than start date", str(ctx.exception))

        # 3. Update with empty record number (expected to fail)
        with self.assertRaises(ValueError) as ctx:
            self.service.rules.validate_license_update(lic_id, {"record_number": ""})
        self.assertIn("Registration number is mandatory", str(ctx.exception))

        # 4. Update with letters in record number (expected to fail)
        with self.assertRaises(ValueError) as ctx:
            self.service.rules.validate_license_update(lic_id, {"record_number": "123B"})
        self.assertIn("Registration number must follow a numeric format", str(ctx.exception))

        # 5. Update with empty activity_location (expected to fail)
        with self.assertRaises(ValueError) as ctx:
            self.service.rules.validate_license_update(lic_id, {"activity_location": ""})
        self.assertIn("Company address is mandatory", str(ctx.exception))

        # 6. Valid updates (expected to pass)
        try:
            self.service.rules.validate_license_update(lic_id, {
                "record_number": "77890",
                "expiration_date": "2028-12-31",
                "activity_location": "Algiers, Algiers"
            })
        except ValueError as e:
            self.fail(f"Valid update failed validation: {e}")

if __name__ == "__main__":
    unittest.main()
