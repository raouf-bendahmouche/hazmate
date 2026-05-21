import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class EmailNotifier:
    """Handles email notifications for license expiration alerts."""

    def __init__(self, database):
        self.db = database

    def send_expiration_alert(self, license_data, recipient_email):
        """Send expiration alert email for a license."""
        try:
            settings = self.db.get_all_settings()
            smtp_server = settings.get("smtp_server")
            smtp_port = int(settings.get("smtp_port", "587"))
            sender_email = settings.get("smtp_email")
            sender_password = settings.get("smtp_password")

            if not all([smtp_server, sender_email, sender_password]):
                print("SMTP settings not configured. Email not sent.")
                return False

            # Calculate days until expiration
            expiration_date = datetime.strptime(license_data["expiration_date"], "%Y-%m-%d").date()
            days_left = (expiration_date - datetime.now().date()).days

            # Compose email
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = recipient_email
            msg["Subject"] = f"License Expiration Alert - {license_data['record_number']}"

            body = f"""
License Expiration Alert

This is an automated notification from the License Management System.

=== License Details ===
Record Number: {license_data.get('record_number', 'N/A')}
License Number: {license_data.get('license_number', 'N/A')}
Driver Name: {license_data.get('driver_name', 'N/A')}
Vehicle Registration: {license_data.get('vehicle_reg', 'N/A')}
Company Name: {license_data.get('company_name', 'N/A')}

=== Expiration Information ===
Expiration Date: {license_data.get('expiration_date', 'N/A')}
Days Until Expiration: {days_left}

ALERT: This license will expire in {days_left} days!

Please take necessary action to renew this license.

---
This is an automated message. Please do not reply.
"""
            msg.attach(MIMEText(body, "plain"))

            # Send email
            with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as smtp:
                smtp.starttls()
                smtp.login(sender_email, sender_password)
                smtp.send_message(msg)

            # Log notification
            self.db.log_notification(license_data["id"], recipient_email)
            print(f"Email sent to {recipient_email} for license {license_data['record_number']}")
            return True

        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False

    def send_batch_expiration_alerts(self, days_ahead=30):
        """Send alerts for all licenses expiring within X days."""
        try:
            settings = self.db.get_all_settings()
            recipient_email = settings.get("smtp_recipient")

            if not recipient_email:
                print("No recipient email configured.")
                return

            expiring_licenses = self.db.get_expiring_licenses(days_ahead)

            if not expiring_licenses:
                print(f"No licenses expiring within {days_ahead} days.")
                return

            sent_count = 0
            for license_data in expiring_licenses:
                if self.send_expiration_alert(dict(license_data), recipient_email):
                    sent_count += 1

            print(f"Sent {sent_count}/{len(expiring_licenses)} expiration alerts.")

        except Exception as e:
            print(f"Error in batch notifications: {str(e)}")
