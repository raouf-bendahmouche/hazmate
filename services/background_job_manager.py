"""
Background Job Manager — Handles non-blocking tasks.
- Database Backups
- Email Notifications (Simulated for local desktop)
"""

import asyncio
import shutil
import os
from datetime import datetime
from database.connection_handler import Database

class BackgroundJobManager:
    def __init__(self, db: Database):
        self.db = db
        self._running = False

    async def start(self):
        """Starts the background loop."""
        self._running = True
        asyncio.create_task(self._backup_loop())
        print("Background jobs started.")

    async def stop(self):
        self._running = False
        print("Background jobs stopped.")

    async def _backup_loop(self):
        """Perform database backup every 24 hours."""
        while self._running:
            try:
                self.perform_backup()
            except Exception as e:
                print(f"Backup failed: {e}")
            await asyncio.sleep(86400) # 24 hours

    def perform_backup(self):
        """Creates a timestamped copy of the database file."""
        db_file = self.db.db_file
        backup_dir = os.path.join(os.path.dirname(db_file), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"licenses_backup_{timestamp}.db")
        
        shutil.copy2(db_file, backup_file)
        print(f"Database backup created: {backup_file}")

    async def send_expiry_notification(self, license_id: int, recipient: str):
        """Simulates sending an email notification."""
        # In a real local app, this might trigger a system notification or log to a file
        print(f"Sending expiry notification for License {license_id} to {recipient}...")
        await asyncio.sleep(2) # Simulate network delay
        self.db.log_notification(license_id, recipient)
        print("Notification sent successfully.")
