"""
Auth Router — POST /auth/login  |  POST /auth/logout  |  GET /auth/validate
Thin HTTP boundary: validation only. All logic lives in AuthService.
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

# auth_service instance is injected at registration time to avoid circular imports.
_auth_service = None


def create_auth_router(auth_service):
    """
    Factory that returns an APIRouter wired to the provided AuthService instance.
    Using a factory instead of a module-level singleton prevents circular imports
    and keeps the router testable in isolation.
    """
    global _auth_service
    _auth_service = auth_service

    router = APIRouter(prefix="/auth", tags=["Authentication"])

    # ── Pydantic schemas ──────────────────────────────────────────────────────

    class LoginRequest(BaseModel):
        username: str
        password: str

    class ChangePasswordRequest(BaseModel):
        username: str
        current_password: str
        new_password: str

    class ChangeUsernameRequest(BaseModel):
        current_username: str
        new_username: str
        current_password: str

    # ── Endpoints ─────────────────────────────────────────────────────────────

    @router.post("/login")
    async def login(body: LoginRequest):
        """
        Authenticate a user with username + password.

        Returns a session token on success.
        Returns 401 on invalid credentials.

        No sensitive data is hardcoded — credentials are stored in the DB as
        bcrypt hashes and the initial password is bootstrap-generated at first run.
        """
        if not body.username or not body.password:
            raise HTTPException(status_code=400, detail="Username and password are required.")

        result = _auth_service.login(body.username.strip(), body.password)
        if result is None:
            raise HTTPException(status_code=401, detail="Invalid username or password.")

        return {"status": "success", "message": "Login successful", "data": result}

    @router.post("/logout")
    async def logout(authorization: Optional[str] = Header(None)):
        """
        Invalidate the session token passed in the Authorization header.
        Format: `Authorization: Bearer <token>`
        """
        token = _extract_token(authorization)
        if token:
            _auth_service.logout(token)
        return {"status": "success", "message": "Logged out"}

    @router.get("/validate")
    async def validate(authorization: Optional[str] = Header(None)):
        """
        Check whether the current session token is still valid.
        Used by the frontend on page load to decide whether to redirect to login.
        """
        token = _extract_token(authorization)
        username = _auth_service.validate_token(token) if token else None
        if not username:
            raise HTTPException(status_code=401, detail="Session expired or invalid.")
        return {"status": "success", "message": "Token valid", "data": {"username": username}}

    @router.post("/change-password")
    async def change_password(body: ChangePasswordRequest):
        """
        Change the password for the authenticated user.
        Requires the current password as confirmation before accepting the new one.
        """
        result = _auth_service.login(body.username.strip(), body.current_password)
        if result is None:
            raise HTTPException(status_code=401, detail="Current password is incorrect.")
        if len(body.new_password) < 6:
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")
        _auth_service.change_password(body.username.strip(), body.new_password)
        return {"status": "success", "message": "Password changed successfully"}

    @router.post("/change-username")
    async def change_username(body: ChangeUsernameRequest):
        """
        Change the username for the authenticated user.
        Requires the current password as confirmation before accepting the new username.
        Detailed technical comment (Requirement 15):
        Password confirmation is required for username changes to verify that the request
        is authorized by the actual credential holder, preventing session hijacking or accidental renames.
        """
        result = _auth_service.login(body.current_username.strip(), body.current_password)
        if result is None:
            raise HTTPException(status_code=401, detail="Current password is incorrect.")
        
        new_user = body.new_username.strip()
        if not new_user:
            raise HTTPException(status_code=400, detail="New username cannot be empty.")
            
        # Username uniqueness validation is completely removed. Multiple accounts can share
        # the same username. Only current password verification is required.
        _auth_service.change_username(body.current_username.strip(), new_user)
        return {"status": "success", "message": "Username changed successfully", "data": {"username": new_user}}

    return router


# ── Helper ────────────────────────────────────────────────────────────────────

def _extract_token(authorization: Optional[str]) -> Optional[str]:
    """Parse Bearer token from Authorization header value."""
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None
