import threading
import time
from datetime import datetime, timedelta
from backend.notifications.smtp_email_notifier import EmailNotifier

class LicenseScheduler:
    """Background scheduler for periodic license expiration checks and notifications."""

    def __init__(self, database):
        self.db = database
        self.notifier = EmailNotifier(database)
        self.running = False
        self.thread = None
        self.check_interval = 3600  # Default: 1 hour in seconds

    def start(self):
        """Start the background scheduler."""
        if self.running:
            print("Scheduler is already running.")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("License scheduler started.")

    def stop(self):
        """Stop the background scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("License scheduler stopped.")

    def _run(self):
        """Main scheduler loop."""
        while self.running:
            try:
                self._check_and_notify()
                # Wait before next check
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"Scheduler error: {str(e)}")
                time.sleep(60)  # Retry after 1 minute on error

    def _check_and_notify(self):
        """Check for expiring licenses and send notifications."""
        try:
            settings = self.db.get_all_settings()
            check_days = int(settings.get("expiration_check_days", "30"))

            print(f"[{datetime.now()}] Checking for licenses expiring within {check_days} days...")
            self.notifier.send_batch_expiration_alerts(check_days)

        except Exception as e:
            print(f"Error during notification check: {str(e)}")

    def set_check_interval(self, hours=1):
        """Set the interval between checks (in hours)."""
        self.check_interval = hours * 3600
        print(f"Check interval set to {hours} hour(s).")

    def force_check_now(self):
        """Force an immediate check without waiting."""
        print("Forcing immediate expiration check...")
        self._check_and_notify()
