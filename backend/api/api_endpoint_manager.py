"""
FastAPI REST API — Hazardous Material Transport License Management
All heavy logic stays here. Electron UI is display-only.
"""

import sys
import os
import re

# Ensure project root is on path when launched as subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
import uvicorn

from database.connection_handler import Database
from backend.notifications.license_expiry_scheduler import LicenseScheduler
from services.statistics_service import StatisticsService
from services.license_service import LicenseService
from services.background_job_manager import BackgroundJobManager
from services.auth_service import AuthService
from backend.api.auth_router import create_auth_router

# ==============================================================================
# Lifespan Management (Startup/Shutdown)
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle application startup and shutdown events gracefully.
    This replaces the deprecated @app.on_event handlers.
    
    CRITICAL: Lifespan events ensure background tasks are properly started and stopped
    with the API lifecycle. Without explicit management, the scheduler thread and backup
    manager would continue running after API shutdown, causing resource leaks.
    If removed, compliance monitoring and backup reliability are lost.
    """
    # Startup Logic
    auth_service.ensure_default_admin()
    scheduler.start()
    await bg_manager.start()
    print("Application lifespan started.")
    
    yield
    
    # Shutdown Logic
    scheduler.stop()
    await bg_manager.stop()
    print("Application lifespan ended.")

# Initialize FastAPI application with lifespan
app = FastAPI(
    title="License Management System API",
    lifespan=lifespan
)

# This endpoint handles 404 cleanly like Flask did
@app.exception_handler(404)
async def custom_404_handler(request, __):
    return JSONResponse(status_code=404, content={"status": "error", "message": "Endpoint not found"})

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail},
    )

@app.exception_handler(Exception)
async def custom_generic_exception_handler(request, exc):
    # Log the exception stack trace here in a real production system
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": str(exc)},
    )

# Add CORS Middleware to allow Electron frontend to connect without issues
# This is intentionally permissive because the renderer runs locally and talks to a
# local API process. If CORS were too strict here, the Electron UI would fail during
# startup and every browser-style fetch from the renderer would be blocked.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()
scheduler = LicenseScheduler(db)
stats_service = StatisticsService()
license_service = LicenseService(db)
bg_manager = BackgroundJobManager(db)
auth_service = AuthService(db)

# Register the authentication router
app.include_router(create_auth_router(auth_service))


def _extract_token_from_header(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def _require_auth(authorization: Optional[str]):
    token = _extract_token_from_header(authorization)
    username = auth_service.validate_token(token) if token else None
    if not username:
        _err("Authentication required", 401)
    return username


def _ok(data=None, message="ok"):
    """Format standard success responses.

    The frontend expects every successful payload to arrive in the same envelope so
    it can unwrap data and errors in one place. Removing this helper would scatter
    response-shape rules across every endpoint and make the UI brittle.
    """
    return {"status": "success", "message": message, "data": data}

def _err(message, code=400):
    """Raise standard HTTP exception for error responses.

    Centralizing error raising keeps status codes and response formatting consistent.
    If individual endpoints emitted ad hoc errors, the renderer would need custom
    parsing logic for each failure mode.
    """
    raise HTTPException(status_code=code, detail=message)

def _is_numbers_only(value):
    return bool(re.fullmatch(r"\d+", value or ""))

def _is_letters_only(value):
    text = value or ""
    return bool(text) and all(ch.isalpha() or ch.isspace() or ch in "-'" for ch in text)

# ==============================================================================
# Pydantic Models for Data Validation (MANDATORY UPGRADE)
# ==============================================================================

class LicenseCreate(BaseModel):
    # The Pydantic BaseModel enforces rigorous type validation
    # preventing bad data from hitting the database engine.
    # This is the first hard validation boundary before any business logic runs, so
    # malformed requests fail early and predictably instead of causing partial writes.
    company_name: str
    vehicle_reg: str
    record_number: str
    license_number: Optional[str] = ""
    company_reg: Optional[str] = ""
    company_address: Optional[str] = ""
    carrier_type: Optional[str] = "Public"
    account_type: Optional[str] = "Public"
    vehicle_type: Optional[str] = ""
    vehicle_category: Optional[str] = ""
    route_origin: Optional[str] = ""
    route_dest: Optional[str] = ""
    route_checkpoints: Optional[str] = ""
    hazmat_type: Optional[str] = ""
    signature_date: Optional[str] = ""
    expiration_date: Optional[str] = ""
    activity_location: Optional[str] = ""
    contract_type: Optional[str] = ""
    deletion_days: Optional[int] = None
    vehicle_type_category: Optional[str] = ""
    route: Optional[str] = ""

class LicenseUpdate(BaseModel):
    license_number: Optional[str] = None
    record_number: Optional[str] = None
    signature_date: Optional[str] = None
    expiration_date: Optional[str] = None
    status: Optional[str] = None
    activity_location: Optional[str] = None
    contract_type: Optional[str] = None
    deletion_days: Optional[int] = None


# ── Health ──────────────────────────────────────────────────────────────────

@app.get("/api/ping")
async def ping():
    """Health check endpoint for Electron to detect when API is ready.

    The desktop shell polls this endpoint before opening the UI. If this endpoint
    vanished, startup synchronization would become guesswork and the renderer could
    issue requests before the server is listening.
    """
    return _ok("pong")


# ── Statistics ──────────────────────────────────────────────────────────────

@app.get("/api/stats")
async def stats():
    return _ok(db.get_statistics())

@app.get("/api/stats/advanced")
async def stats_advanced():
    return _ok(db.get_advanced_statistics())

@app.get("/api/stats/monthly")
async def stats_monthly(months: int = 12):
    return _ok(db.get_monthly_transports(months))

@app.get("/api/statistics/dashboard")
async def dashboard_stats():
    """New combined statistics endpoint for the 3-tier dashboard."""
    return _ok(stats_service.get_dashboard_statistics())


# ── Licenses ────────────────────────────────────────────────────────────────

@app.get("/api/licenses")
async def list_licenses(
    search: str = "",
    status: Optional[str] = None,
    carrier: Optional[str] = None,
    activity_location: Optional[str] = None,
    contract_type: Optional[str] = None,
    sort_by: str = "created_at",
    sort_dir: str = "DESC",
    page: int = 1,
    limit: int = 50
):
    """
    List licenses with pagination, sorting, and advanced filtering.
    Using async def to prevent blocking the main event loop during DB access.
    """
    page_num = max(1, page)
    limit_num = min(50, max(1, limit))

    result = db.search_licenses(
        search_term=search,
        status_filter=status,
        carrier_type_filter=carrier,
        activity_location=activity_location,
        contract_type=contract_type,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page_num,
        limit=limit_num,
    )
    return _ok(result)


@app.post("/api/licenses/{license_id}/renew")
async def renew_license(license_id: int, request: Request, authorization: Optional[str] = Header(None)):
    """Renew an expired license. Accepts either `extend_days` (int) or `new_expiration_date` (YYYY-MM-DD)."""
    _require_auth(authorization)
    d = await request.json()
    extend_days = d.get("extend_days")
    new_date = d.get("new_expiration_date")

    lic = db.get_license_by_id(license_id)
    if not lic:
        _err("License not found", 404)

    if new_date:
        db.update_license(license_id, expiration_date=new_date, status="active")
        return _ok(message="License renewed")

    if extend_days:
        try:
            days = int(extend_days)
        except Exception:
            _err("extend_days must be an integer")
        # compute new date based on existing expiration_date
        from datetime import datetime, timedelta
        try:
            cur = lic.get("expiration_date")
            cur_dt = datetime.strptime(str(cur), "%Y-%m-%d")
        except Exception:
            cur_dt = datetime.now()
        new_dt = cur_dt + timedelta(days=days)
        db.update_license(license_id, expiration_date=new_dt.strftime("%Y-%m-%d"), status="active")
        return _ok(message="License renewed")

    _err("Either extend_days or new_expiration_date is required")


@app.post("/api/licenses/{license_id}/suspend")
async def suspend_license(license_id: int, request: Request, authorization: Optional[str] = Header(None)):
    """Suspend or stop a license. Body: { action: 'suspend'|'stop' }"""
    _require_auth(authorization)
    d = await request.json()
    action = (d.get("action") or "").strip().lower()
    if action not in ("suspend", "stop"):
        _err("Action must be 'suspend' or 'stop'")

    lic = db.get_license_by_id(license_id)
    if not lic:
        _err("License not found", 404)

    status = "suspended" if action == "suspend" else "stopped"
    db.update_license(license_id, status=status)
    return _ok(message=f"License {status}")

@app.get("/api/licenses/deleted")
async def list_deleted_licenses(
    search: str = "",
    status: Optional[str] = None,
    activity_location: Optional[str] = None,
    contract_type: Optional[str] = None,
    page: int = 1,
    limit: int = 50
):
    """Return only soft-deleted contracts with dedicated filters/search."""
    page_num = max(1, page)
    limit_num = min(50, max(1, limit))

    result = db.search_deleted_licenses(
        search_term=search,
        status_filter=status,
        activity_location=activity_location,
        contract_type=contract_type,
        page=page_num,
        limit=limit_num,
    )
    return _ok(result)

@app.get("/api/licenses/expiring")
async def expiring(days: int = 30):
    """Get licenses expiring within the provided number of days."""
    return _ok(db.get_expiring_licenses(days))


@app.get("/api/licenses/{license_id}")
async def get_license(license_id: int):
    """Get full details of a specific license/contract."""
    row = db.get_license_by_id(license_id)
    if not row:
        _err("License not found", 404)
    return _ok(row)

def map_clean_to_legacy_dict(data: dict) -> dict:
    # Auto-generate license_number if missing
    if not data.get("license_number") and data.get("record_number"):
        data["license_number"] = f"LIC-{data['record_number']}"
        
    # Split vehicle_type_category if present
    if data.get("vehicle_type_category"):
        type_cat = data.pop("vehicle_type_category").strip()
        parts = type_cat.split(None, 1)
        data["vehicle_type"] = parts[0]
        data["vehicle_category"] = parts[1] if len(parts) > 1 else ""
    elif "vehicle_type_category" in data:
        data.pop("vehicle_type_category")
            
    # Split route if present
    if data.get("route"):
        route = data.pop("route").strip()
        parts = re.split(r"→|->", route)
        data["route_origin"] = parts[0].strip()
        data["route_dest"] = parts[1].strip() if len(parts) > 1 else ""
    elif "route" in data:
        data.pop("route")
            
    return data

@app.post("/api/licenses", status_code=201)
async def create_license(d: LicenseCreate, authorization: Optional[str] = Header(None)):
    """
    Create a complete license entity using the LicenseService.
    All business logic and orchestration is handled in the service layer.
    """
    try:
        _require_auth(authorization)
        
        # Map clean properties to legacy model format
        data = d.dict()
        data = map_clean_to_legacy_dict(data)

        # These duplicate checks stay close to the HTTP boundary because they fail
        # fast and avoid the cost of building the whole dependency graph for records
        # we already know are invalid.
        lic_num = data.get("license_number")
        rec_num = data.get("record_number")
        if db.get_license_by_number(lic_num):
            _err(f"License number '{lic_num}' already exists.")
        if db.get_license_by_record_number(rec_num):
            _err(f"Record number '{rec_num}' already exists.")

        lic_id = license_service.create_complete_license(data)
        return _ok({"id": lic_id}, "License created successfully")
    except ValueError as e:
        _err(str(e))
    except Exception as e:
        _err(f"Unexpected error: {str(e)}", 500)

@app.put("/api/licenses/{license_id}")
async def update_license(license_id: int, d: LicenseUpdate, authorization: Optional[str] = Header(None)):
    """Partially update a license.

    Only provided fields are passed through, which prevents accidental overwrites of
    untouched columns. That behavior matters because the UI often submits edit forms
    with only a subset of fields.
    """
    _require_auth(authorization)
    fields = {k: v for k, v in d.dict(exclude_unset=True).items() if v is not None}
    if not fields:
        _err("No updatable fields provided.")
    db.update_license(license_id, **fields)
    return _ok(message="License updated")

@app.delete("/api/licenses/{license_id}")
async def delete_license(license_id: int, authorization: Optional[str] = Header(None)):
    """Soft-delete a license contract via service layer.

    This endpoint never hard-deletes because the system needs audit history and
    restore support. Removing the service indirection here would make that policy
    much easier to bypass.
    """
    _require_auth(authorization)
    license_service.soft_delete_license(license_id)
    return _ok(message="License deleted (soft)")

@app.post("/api/licenses/{license_id}/restore")
async def restore_license(license_id: int, authorization: Optional[str] = Header(None)):
    """Restore a soft-deleted contract via service layer with validation.

    The service performs the business-rule check before the mutation, so the API
    stays thin while still rejecting invalid restores cleanly.
    """
    try:
        _require_auth(authorization)
        license_service.restore_license(license_id)
        return _ok(message="License restored")
    except ValueError as e:
        _err(str(e))


# ── Companies ───────────────────────────────────────────────────────────────

@app.get("/api/companies")
async def list_companies():
    """List all registered companies."""
    return _ok(db.get_companies())


@app.post("/api/companies", status_code=201)
async def create_company(request: Request, authorization: Optional[str] = Header(None)):
    """Create a new company. Prevent duplicates by registration number or exact name."""
    _require_auth(authorization)
    d = await request.json()
    name = (d.get("name") or "").strip()
    reg = (d.get("registration_number") or "").strip()
    address = d.get("address", "")
    carrier_type = d.get("carrier_type", "Public")
    account_type = d.get("account_type", "Public")

    if not name:
        _err("Company name is required.")

    # Check by registration first (strong uniqueness)
    if reg:
        existing = db.get_company_by_registration(reg)
        if existing:
            _err("Company with this registration already exists.")

    # Also check for exact name match to avoid duplicates
    companies = db.get_companies()
    for c in companies:
        if c.get("name", "").strip().lower() == name.lower():
            _err("Company with this name already exists.")

    new_id = db.add_company(name, reg or None, address, carrier_type, account_type)
    return _ok({"id": new_id}, "Company created")


# ── Vehicles ────────────────────────────────────────────────────────────────

@app.get("/api/vehicles")
async def list_vehicles():
    """List all registered vehicles."""
    return _ok(db.get_vehicles())


# ── Settings ────────────────────────────────────────────────────────────────

@app.get("/api/settings")
async def get_settings():
    """Retrieve global application settings.

    The UI treats settings as a runtime configuration source, so this endpoint keeps
    the desktop shell decoupled from storage details.
    """
    return _ok(db.get_all_settings())

@app.put("/api/settings")
async def save_settings(request: Request, authorization: Optional[str] = Header(None)):
    """Save application settings from key-value pairs.

    Settings are stored individually so the app can persist small configuration
    changes without requiring a dedicated settings table schema migration every time.
    """
    _require_auth(authorization)
    d = await request.json()
    for key, value in d.items():
        db.set_setting(key, str(value))
    return _ok(message="Settings saved")


# ── Entry point ──────────────────────────────────────────────────────────────

def run_server(port=5757):
    # Run uvicorn programmatically when executed as a script
    uvicorn.run("backend.api.api_endpoint_manager:app", host="127.0.0.1", port=port, reload=False)

if __name__ == "__main__":
    run_server()
