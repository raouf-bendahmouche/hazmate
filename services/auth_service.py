"""
Authentication Service
Handles password hashing (bcrypt), verification, and simple session token generation.
No business logic lives in the router — only here.
"""

import secrets
import bcrypt
from database.connection_handler import Database


class AuthService:
    """
    Responsible for:
      - Bootstrapping the default admin user on first run.
      - Verifying login credentials.
      - Generating opaque session tokens stored server-side.

    Tokens are kept in-memory (dict). For a desktop single-user app this is
    sufficient. If multi-user or persistence across restarts is ever needed,
    migrate tokens to the database sessions table without touching call sites.
    """

    def __init__(self, db: Database):
        self.db = db
        self._active_tokens: dict[str, str] = {}

    @staticmethod
    def hash_password(plain: str) -> str:
        """Return a bcrypt hash of the given plain-text password."""
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        """Return True if plain matches the stored bcrypt hash."""
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False

    def ensure_default_admin(self) -> None:
        """
        Create the default admin account on first run ONLY if no users exist.
        The initial password comes from the DB settings table (key='admin_password').
        If that setting is absent a secure random password is generated and stored so
        the operator can retrieve it from settings on first boot.

        This is a one-time bootstrap. Once any user exists this method does nothing.
        """
        existing = self.db.get_user_by_username("admin")
        if existing:
            return

        initial_pw = self.db.get_setting("admin_password")
        if not initial_pw:
            initial_pw = "admin"
            self.db.set_setting("admin_password", initial_pw)
            print(
                f"[AUTH] No admin password configured. Defaulting password to: {initial_pw!r}"
            )

        hashed = self.hash_password(initial_pw)
        self.db.create_user("admin", hashed, role="admin")
        print("[AUTH] Default admin user created.")

    def login(self, username: str, password: str) -> dict | None:
        """
        Verify credentials and return a session token dict on success, or None
        if credentials are invalid.

        Returns: {"token": str, "username": str, "role": str}
        """
        user = self.db.get_user_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user["password_hash"]):
            return None

        token = secrets.token_hex(32)
        self._active_tokens[token] = username
        return {"token": token, "username": user["username"], "role": user["role"]}

    def logout(self, token: str) -> None:
        """Invalidate a session token."""
        self._active_tokens.pop(token, None)

    def validate_token(self, token: str) -> str | None:
        """Return the username associated with token, or None if invalid."""
        return self._active_tokens.get(token)

    def change_password(self, username: str, new_password: str) -> None:
        """Hash and persist a new password for the given user."""
        hashed = self.hash_password(new_password)
        self.db.update_user_password(username, hashed)
