import os
import subprocess
import sys

def main():
    print("Starting Hazardous Material Transport License Management System...")

    app_path = os.path.dirname(__file__)

    try:
        if sys.platform == "win32":
            subprocess.run(["npm.cmd", "start"], cwd=app_path, check=True)
        else:
            subprocess.run(["npm", "start"], cwd=app_path, check=True)

    except Exception as e:
        print(f"Failed to start application: {e}")

if __name__ == "__main__":
    main()