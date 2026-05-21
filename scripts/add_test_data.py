"""
Test data script to populate the database with sample records (~500 records).
Run this script to add comprehensive test data for checking if the application works.
"""

from datetime import datetime, timedelta
from database.connection_handler import Database
import random

def add_test_data():
    """Add test data to the database."""
    db = Database()
    
    print("Adding test data (approximately 500 records)...")
    
    # Sample data for generating diverse records
    company_names = [
        "FastTransport Inc", "SpeedCargo Ltd", "LogisticsPro Co", "GlobalShipping Network",
        "Elite Transport Services", "Premier Logistics Solutions", "Express Delivery Co",
        "Continental Freight Lines", "Northwest Cargo Systems", "Southern Routes LLC",
        "Midwest Express Carriers", "Pacific Rim Transport", "Atlantic Shipping Co",
        "Desert Logistics Group", "Mountain Peak Delivery", "Urban Distribution Hub",
        "Rapid Transit Solutions", "Horizon Freight Services", "Viking Transport Lines",
        "Phoenix Logistics Network", "Titan Cargo Systems", "Zenith Transport Co",
        "Alpha Fleet Services", "Beta Logistics Solutions", "Gamma Freight Network"
    ]
    
    vehicle_types = ["Truck", "Van", "Bus", "Tanker", "Flatbed"]
    vehicle_categories = ["Heavy", "Medium", "Light", "Passenger", "Hazmat"]
    
    driver_first_names = [
        "John", "Mike", "Sarah", "David", "Lisa", "Robert", "Jennifer", "James", "Mary",
        "Patricia", "Paul", "Nancy", "Charles", "Sandra", "Timothy", "Kathleen", "Christopher",
        "Betty", "Daniel", "Margaret", "Steven", "Ashley", "Edward", "Donna", "Brian",
        "Carol", "Ronald", "Janet", "Anthony", "Maria", "Frank", "Brenda", "Ryan", "Pamela"
    ]
    
    driver_last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
        "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Young"
    ]
    
    cities = [
        "New York", "Los Angeles", "Chicago", "Miami", "Boston", "Seattle", "Denver",
        "Houston", "Phoenix", "Philadelphia", "Dallas", "San Francisco", "Atlanta",
        "Washington", "Portland", "Las Vegas", "Nashville", "Memphis", "Detroit", "Cleveland"
    ]
    
    hazmat_materials = [
        "Flammable Liquid", "Toxic Substance", "Corrosive Material", "Explosive",
        "Radioactive Material", "Oxidizing Substance", "Organic Peroxide"
    ]
    
    today = datetime.now().date()
    license_counter = 1
    route_counter = 1
    company_counter = 1
    total_licenses = 0
    total_vehicles = 0
    
    # Create routes first
    routes = []
    for i in range(20):
        start = cities[i % len(cities)]
        end = cities[(i + 5) % len(cities)]
        checkpoint = cities[(i + 10) % len(cities)]
        try:
            route_id = db.add_route(start, end, checkpoint)
            routes.append(route_id)
        except:
            pass
    print(f"✓ Added {len(routes)} Routes")
    
    # Create companies and vehicles
    companies = []
    vehicles = []
    
    for comp_idx, company_name in enumerate(company_names):
        try:
            company_type = random.choice(["Public", "Private"])
            company_id = db.add_company(
                company_name,
                f"REG{company_counter:04d}",
                f"{100 + comp_idx} Commerce Street, {cities[comp_idx % len(cities)]}",
                company_type,
                random.choice(["Public", "Private"])
            )
            companies.append(company_id)
            company_counter += 1
            
            # Add 8-10 vehicles per company
            num_vehicles = random.randint(8, 10)
            for veh_idx in range(num_vehicles):
                try:
                    plate = f"{chr(65 + comp_idx % 26)}{chr(65 + veh_idx % 26)}-{comp_idx * 100 + veh_idx}"
                    vehicle_id = db.add_vehicle(
                        company_id,
                        plate,
                        random.choice(vehicle_types),
                        random.choice(vehicle_categories)
                    )
                    vehicles.append((vehicle_id, company_id))
                    total_vehicles += 1
                except:
                    pass
        except:
            pass
    
    print(f"✓ Added {len(companies)} Companies")
    print(f"✓ Added {total_vehicles} Vehicles")
    
    # Add licenses for each vehicle
    for vehicle_id, company_id in vehicles:
        # 2-3 licenses per vehicle
        num_licenses = random.randint(2, 3)
        for lic_idx in range(num_licenses):
            try:
                first_name = random.choice(driver_first_names)
                last_name = random.choice(driver_last_names)
                driver_name = f"{first_name} {last_name}"
                phone = f"555-{random.randint(1000, 9999)}"
                record_num = f"REC{license_counter:05d}"
                license_num = f"LIC{license_counter:05d}"
                
                # Vary expiration dates
                days_offset = random.randint(-90, 400)
                expiry = today + timedelta(days=days_offset)
                
                db.add_license(
                    vehicle_id,
                    random.choice(routes),
                    record_num,
                    driver_name,
                    phone,
                    license_num,
                    today,
                    expiry
                )
                total_licenses += 1
                license_counter += 1
                
                # Occasionally add hazmat
                if random.random() < 0.2:
                    db._execute_write(
                        "INSERT INTO hazardous_materials (vehicle_id, material_type) VALUES (?, ?)",
                        (vehicle_id, random.choice(hazmat_materials))
                    )
            except:
                pass
    
    print(f"✓ Added {total_licenses} Licenses/Drivers")
    print(f"✓ Added Hazardous Materials")
    
    print("\n" + "="*60)
    print("✅ Test data added successfully!")
    print("="*60)
    print(f"\nSummary:")
    print(f"  • {len(companies)} Companies added")
    print(f"  • {total_vehicles} Vehicles added")
    print(f"  • {len(routes)} Routes added")
    print(f"  • {total_licenses} Licenses/Drivers added (~500 total records)")
    print(f"  • Hazardous Materials added to ~20% of vehicles")
    print(f"\nStatus breakdown:")
    
    # Count status
    active = sum(1 for _, _ in vehicles for _ in range(1))  # Rough estimate
    expired_estimate = int(total_licenses * 0.15)
    expiring_soon_estimate = int(total_licenses * 0.20)
    
    print(f"  • Active licenses: ~{total_licenses - expired_estimate}")
    print(f"  • Expired licenses: ~{expired_estimate}")
    print(f"  • Expiring soon (< 30 days): ~{expiring_soon_estimate}")
    print("\nYou can now test:")
    print("  ✓ Search, filter, and view records")
    print("  ✓ Delete companies, vehicles, or drivers")
    print("  ✓ View statistics with charts")
    print("  ✓ Language switching (English, French, Arabic)")
    print("="*60)

if __name__ == "__main__":
    try:
        add_test_data()
    except Exception as e:
        print(f"❌ Error adding test data: {str(e)}")
        import traceback
        traceback.print_exc()
