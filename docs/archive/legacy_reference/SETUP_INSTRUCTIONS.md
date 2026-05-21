# Setup & Installation Instructions

This guide provides the necessary steps to set up the Hazardous Material Transport License Management System for development and production on both Windows and Linux.

## Requirements
- Node.js (v16+)
- Python (v3.8+)
- npm (Node Package Manager)
- pip (Python Package Installer)

---

## Windows Installation

Open Command Prompt or PowerShell in the `python-project` directory and run the following commands sequentially:

```cmd
:: 1. Create a virtual environment
python -m venv .venv

:: 2. Activate the virtual environment
.venv\Scripts\activate

:: 3. Install Python backend dependencies
pip install -r requirements.txt

:: 4. Install Node frontend dependencies
npm install

:: 5. Start the application
npm start
```

---

## Linux Installation

Open your terminal in the `python-project` directory and run the following commands sequentially:

```bash
# 1. Create a virtual environment
python3 -m venv .venv

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Install Python backend dependencies
pip install -r requirements.txt

# 4. Install Node frontend dependencies
npm install

# 5. Start the application
npm start
```

---

## Running the Application

Once installed, you only ever need **one command** to run the software, regardless of your OS:

```bash
npm start
```

### What happens when you run `npm start`?
1. The Electron Main Process starts.
2. It intelligently detects if you are on Windows or Linux.
3. It automatically finds your `.venv` and uses the correct Python executable to boot up the Flask API silently in the background.
4. It waits for the API to report as healthy.
5. It opens the desktop application window.

*No manual starting of the Python server is required.*
