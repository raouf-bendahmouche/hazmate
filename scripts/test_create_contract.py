import subprocess
import time
import requests
import sys

def main():
    print("Starting FastAPI server in subprocess...")
    # Port to use
    port = 5759
    server_process = subprocess.Popen(
        [sys.executable, "backend/api/api_endpoint_manager.py"],
        env={"PYTHONUNBUFFERED": "1", **os.environ},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to boot
    time.sleep(3)
    
    api_url = f"http://127.0.0.1:5757"  # Default port used in run_server is 5757 if launched directly
    
    try:
        # 1. Ping
        print("Pinging backend...")
        r = requests.get(f"{api_url}/api/ping")
        print("Ping response:", r.json())
        
        # 2. Login
        print("Logging in...")
        r = requests.post(f"{api_url}/auth/login", json={"username": "admin", "password": "D3Gj_0-Fhq0WB80P"})
        login_data = r.json()
        print("Login response:", login_data)
        token = login_data["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        import random
        rec_num = str(random.randint(100000, 999999))
        veh_reg = str(random.randint(100000, 999999))

        # 3. Duplicate check
        print("Checking duplicate...")
        r = requests.get(f"{api_url}/api/licenses/check-duplicate?record_number={rec_num}", headers=headers)
        print("Duplicate check response:", r.json())
        
        # 4. Create license
        payload = {
            "record_number": rec_num,
            "signature_date": "2026-05-01",
            "company_name": "Safe transport corp",
            "company_reg": "123456",
            "company_address": "Commune, Setif",
            "vehicle_reg": veh_reg,
            "vehicle_type": "Truck",
            "vehicle_category": "A",
            "route_origin": "",
            "route_dest": "Constantine",
            "expiration_date": "2027-05-01",
            "hazmat_type": "Explosive Class 1",
            "carrier_type": "Public",
            "account_type": "Public",
            "contract_type": "Public"
        }
        print("Creating license...")
        r = requests.post(f"{api_url}/api/licenses", json=payload, headers=headers)
        print("Create response:", r.json())
        
        if r.status_code == 201 or (r.status_code == 200 and r.json().get("status") == "success"):
            print("SUCCESS: Contract added successfully!")
        else:
            print("FAILURE: Could not create contract:", r.text)
            
    except Exception as e:
        print("An error occurred during test:", e)
    finally:
        print("Terminating FastAPI server...")
        server_process.terminate()
        server_process.wait()
        print("Server terminated.")

if __name__ == "__main__":
    import os
    main()
