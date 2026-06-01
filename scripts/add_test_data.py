"""
Test data script to populate the database with sample records (~500 records).
Run this script to add comprehensive test data for checking if the application works.
"""

from datetime import datetime, timedelta
from database.connection_handler import Database
import random
import sqlite3
import json
from pathlib import Path

def add_test_data():
    """Add test data to the database."""
    db = Database()
    db_file = db.db_file
    
    print(f"Connecting to database at {db_file}...")
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys=ON")
    cursor = conn.cursor()
    
    print("Adding test data (approximately 500 records)...")
    
    # Load Setif communes for realistic local addresses and activity locations
    communes_path = Path(__file__).parent.parent / "frontend" / "data" / "setif_communes.json"
    try:
        with open(communes_path, "r", encoding="utf-8") as f:
            communes_data = json.load(f)
        setif_communes = communes_data["communes"]
        wilaya_name = communes_data["wilaya"]
    except Exception as e:
        print(f"Warning: Could not load setif_communes.json: {e}")
        setif_communes = ["Setif", "Ain El Kebira", "El Eulma", "Ain Oulmene", "Bougaa", "Ain Azel"]
        wilaya_name = "Setif"

    # Pools of data matching generate_mock_data.py
    companies_pool = [
        {"name": "Algeria Petro-Logistics", "reg_prefix": "APL", "type": "Private"},
        {"name": "Societe Nationale de Transport Routier (SNTR)", "reg_prefix": "SNTR", "type": "Public"},
        {"name": "Naftal Trans-Fuel", "reg_prefix": "NAF", "type": "Public"},
        {"name": "Sahara Chem-Transport", "reg_prefix": "SCT", "type": "Private"},
        {"name": "Oran Gas Delivery", "reg_prefix": "OGD", "type": "Private"},
        {"name": "East Chemical Carrier", "reg_prefix": "ECC", "type": "Private"},
        {"name": "Mediterra Cargo", "reg_prefix": "MC", "type": "Private"},
        {"name": "Mitidja Agri-Chem", "reg_prefix": "MAC", "type": "Private"},
        {"name": "Annaba Steel & Acid Logistics", "reg_prefix": "ASAL", "type": "Private"},
        {"name": "Atlas Hazmat Transports", "reg_prefix": "AHT", "type": "Private"},
        {"name": "Tassili Transport Hydrocarbures", "reg_prefix": "TTH", "type": "Public"},
        {"name": "Djezair Cargo Express", "reg_prefix": "DCE", "type": "Private"},
        {"name": "Biskra Sulfur Delivery", "reg_prefix": "BSD", "type": "Private"},
        {"name": "Tlemcen Gaz & Acid", "reg_prefix": "TGA", "type": "Private"},
        {"name": "Kabylie Petro Services", "reg_prefix": "KPS", "type": "Private"},
        {"name": "Chlef Chemical Trans", "reg_prefix": "CCT", "type": "Private"},
        {"name": "Aures Transit & Transport", "reg_prefix": "ATT", "type": "Private"},
        {"name": "Ghardaia Gas Transport", "reg_prefix": "GGT", "type": "Private"},
        {"name": "Hodna Logistique", "reg_prefix": "HL", "type": "Private"},
        {"name": "Saoura Transporters", "reg_prefix": "ST", "type": "Private"}
    ]

    first_names = ["Mohamed", "Ahmed", "Karim", "Yacine", "Mustapha", "Sofiane", "Rachid", "Amine", "Fouad", "Ali", 
                   "Omar", "Samir", "Reda", "Hamza", "Khaled", "Bilal", "Walid", "Mourad", "Nabil", "Tarek",
                   "Abdelkader", "Djamel", "Farid", "Hichem", "Oussama", "Ryad", "Zouhir", "Salim", "Tewfik", "Youssef"]

    last_names = ["Benali", "Brahimi", "Mansouri", "Khelifi", "Ghezali", "Belaid", "Saidi", "Ould", "Haddad", "Laribi", 
                  "Ziane", "Bouaziz", "Hamidi", "Madani", "Soltani", "Abdi", "Cherif", "Amrani", "Slimani", "Rahmani",
                  "Messaoudi", "Kacimi", "Saadaoui", "Benyahia", "Merbah", "Guergour", "Tahri", "Lounis", "Zekri", "Kebir"]

    vehicle_types = ["Heavy Truck", "Semi-Trailer Tanker", "Rigid Tanker", "Cargo Van", "Flatbed Truck"]
    vehicle_categories = ["Class A (Heavy Hazmat)", "Class B (Medium Hazmat)", "Class C (Light Hazmat)"]

    hazmat_materials = [
        "Class 3 (Flammable Liquids)",
        "Class 1 (Explosives)",
        "Class 2.1 (Flammable Gases)",
        "Class 2.2 (Non-Flammable/Non-Toxic Gases)",
        "Class 2.3 (Toxic Gases)",
        "Class 4.1 (Flammable Solids)",
        "Class 5.1 (Oxidizing Substances)",
        "Class 6.1 (Toxic Substances)",
        "Class 8 (Corrosive Substances)",
        "Class 9 (Miscellaneous Dangerous Substances)"
    ]
    
    today = datetime.now().date()
    license_counter = 1
    total_licenses = 0
    total_vehicles = 0
    
    try:
        # Clear existing data first
        print("Clearing old data...")
        cursor.execute("DELETE FROM audit_logs")
        cursor.execute("DELETE FROM notifications_log")
        cursor.execute("DELETE FROM licenses")
        cursor.execute("DELETE FROM hazardous_materials")
        cursor.execute("DELETE FROM routes")
        cursor.execute("DELETE FROM vehicles")
        cursor.execute("DELETE FROM companies")

        # Create routes first
        routes = []
        for i in range(20):
            start = setif_communes[i % len(setif_communes)]
            end = setif_communes[(i + 5) % len(setif_communes)]
            checkpoint = setif_communes[(i + 10) % len(setif_communes)]
            cursor.execute(
                "INSERT INTO routes (origin, destination, checkpoints) VALUES (?, ?, ?)",
                (start, end, checkpoint)
            )
            routes.append(cursor.lastrowid)
        print(f"Added {len(routes)} Routes")
        
        # Create companies and vehicles
        companies = []
        vehicles = []
        
        for comp_idx, c in enumerate(companies_pool):
            company_name = c["name"]
            company_type = c["type"]
            address_commune = random.choice(setif_communes)
            
            cursor.execute(
                """INSERT INTO companies (name, address, carrier_type, account_type) 
                   VALUES (?, ?, ?, ?)""",
                (company_name, f"{address_commune}, {wilaya_name}", company_type, company_type)
            )
            company_id = cursor.lastrowid
            companies.append(company_id)
            
            # Scale up vehicles per company
            num_vehicles = random.randint(10, 12)
            for veh_idx in range(num_vehicles):
                plate = f"{random.randint(10000, 99999)}-{random.randint(100, 199)}-19"
                cursor.execute(
                    "INSERT INTO vehicles (company_id, registration_number, type, category) VALUES (?, ?, ?, ?)",
                    (company_id, plate, random.choice(vehicle_types), random.choice(vehicle_categories))
                )
                vehicle_id = cursor.lastrowid
                vehicles.append((vehicle_id, company_id))
                total_vehicles += 1
        
        print(f"Added {len(companies)} Companies")
        print(f"Added {total_vehicles} Vehicles")
        
        # Add licenses for each vehicle
        for vehicle_id, company_id in vehicles:
            # Scale up licenses/drivers to reach ~1000 total licenses
            num_licenses = random.randint(4, 5)
            for lic_idx in range(num_licenses):
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                driver_name = f"{first_name} {last_name}"
                phone = f"0{random.choice([5, 6, 7])}{random.randint(10000000, 99999999)}"
                
                # Digit-only record number
                record_num = f"{license_counter:06d}"
                license_num = f"LIC{license_counter:05d}"
                
                # Distribute signature date over the past 3 years to generate realistic trends
                sig_offset = random.randint(0, 1100)
                sig_date = today - timedelta(days=sig_offset)
                
                # Expiration date (1 or 2 years duration)
                duration = random.choice([365, 730])
                expiry = sig_date + timedelta(days=duration)
                status = "expired" if expiry < today else "active"
                
                activity_location = random.choice(setif_communes)
                registration_number = f"{1000000 + license_counter}"
                
                cursor.execute(
                    """INSERT INTO licenses
                       (vehicle_id, route_id, record_number, driver_name, driver_phone, license_number,
                        signature_date, expiration_date, status, activity_location, registration_number, deletion_days)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (vehicle_id, random.choice(routes), record_num, driver_name, phone, license_num,
                     sig_date.strftime("%Y-%m-%d"), expiry.strftime("%Y-%m-%d"), status, activity_location, registration_number, random.choice([30, 60, 90]))
                )
                license_id = cursor.lastrowid
                total_licenses += 1
                license_counter += 1
                
                # Occasionally add hazmat
                if random.random() < 0.2:
                    haz_mat = random.choice(hazmat_materials)
                    cursor.execute(
                        "INSERT INTO hazardous_materials (vehicle_id, material_type) VALUES (?, ?)",
                        (vehicle_id, haz_mat)
                    )
                    
                    # Create audit log
                    cursor.execute(
                        "INSERT INTO audit_logs (action, table_name, record_id, old_values, new_values, user_id) VALUES (?, ?, ?, ?, ?, ?)",
                        ("CREATE", "licenses", license_id, None, json.dumps({
                            "license_number": license_num, "record_number": record_num, "hazmat_type": haz_mat
                        }), "system")
                    )
 
        conn.commit()
        print(f"Added {total_licenses} Licenses/Drivers")
        print(f"Added Hazardous Materials")
        
        print("\n" + "="*60)
        print("Test data added successfully!")
        print("="*60)
        print(f"\nSummary:")
        print(f"  - {len(companies)} Companies added")
        print(f"  - {total_vehicles} Vehicles added")
        print(f"  - {len(routes)} Routes added")
        print(f"  - {total_licenses} Licenses/Drivers added")
        print(f"  - Hazardous Materials added to ~20% of vehicles")
        print("="*60)
        
    except Exception as e:
        conn.rollback()
        print(f"Error during database write: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        add_test_data()
    except Exception as e:
        print(f"Error adding test data: {str(e)}")
        import traceback
        traceback.print_exc()
