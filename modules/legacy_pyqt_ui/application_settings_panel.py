from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)
import os

class SettingsWindow(QDialog):
    """Settings window for SMTP configuration and backup."""

    def __init__(self, database, language="en", translations=None):
        super().__init__()
        self.db = database
        self.current_language = language
        self.translations = translations or {}
        self.setWindowTitle("Settings")
        self.resize(600, 500)
        # Enable minimize and maximize buttons
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self._build_ui()
        self._load_settings()
        self._apply_language()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        self.title = QLabel("Application Settings")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title.setFont(title_font)
        layout.addWidget(self.title)

        grid = QGridLayout()
        grid.setSpacing(10)
        row = 0

        # SMTP Section
        self.smtp_title = QLabel("Email Notifications (SMTP)")
        self.smtp_title.setStyleSheet("font-weight: 600; color: #0f766e;")
        grid.addWidget(self.smtp_title, row, 0, 1, 2)
        row += 1

        self.smtp_server_label = QLabel("SMTP Server:")
        grid.addWidget(self.smtp_server_label, row, 0)
        self.smtp_server = QLineEdit()
        self.smtp_server.setPlaceholderText("e.g., smtp.gmail.com")
        grid.addWidget(self.smtp_server, row, 1)
        row += 1

        self.smtp_port_label = QLabel("SMTP Port:")
        grid.addWidget(self.smtp_port_label, row, 0)
        self.smtp_port = QSpinBox()
        self.smtp_port.setValue(587)
        self.smtp_port.setRange(1, 65535)
        grid.addWidget(self.smtp_port, row, 1)
        row += 1

        self.smtp_email_label = QLabel("Email Address:")
        grid.addWidget(self.smtp_email_label, row, 0)
        self.smtp_email = QLineEdit()
        self.smtp_email.setPlaceholderText("e.g., admin@example.com")
        grid.addWidget(self.smtp_email, row, 1)
        row += 1

        self.smtp_password_label = QLabel("Password:")
        grid.addWidget(self.smtp_password_label, row, 0)
        self.smtp_password = QLineEdit()
        self.smtp_password.setEchoMode(QLineEdit.Password)
        grid.addWidget(self.smtp_password, row, 1)
        row += 1

        self.smtp_recipient_label = QLabel("Recipient Email:")
        grid.addWidget(self.smtp_recipient_label, row, 0)
        self.smtp_recipient = QLineEdit()
        self.smtp_recipient.setPlaceholderText("Notifications will be sent here")
        grid.addWidget(self.smtp_recipient, row, 1)
        row += 1

        # Test Email
        self.test_btn = QPushButton("Test Email Configuration")
        self.test_btn.clicked.connect(self.test_email)
        grid.addWidget(self.test_btn, row, 0, 1, 2)
        row += 1

        # Backup Section
        self.backup_title = QLabel("Backup Settings")
        self.backup_title.setStyleSheet("font-weight: 600; color: #0f766e;")
        grid.addWidget(self.backup_title, row, 0, 1, 2)
        row += 1

        self.backup_label = QLabel("Backup Folder:")
        grid.addWidget(self.backup_label, row, 0)
        self.backup_folder = QLineEdit()
        self.backup_folder.setReadOnly(True)
        grid.addWidget(self.backup_folder, row, 1)
        row += 1

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.choose_backup_folder)
        grid.addWidget(self.browse_btn, row, 0, 1, 2)
        row += 1

        self.check_days_label = QLabel("Daily Expiration Check (Days):")
        grid.addWidget(self.check_days_label, row, 0)
        self.check_days = QSpinBox()
        self.check_days.setValue(30)
        self.check_days.setRange(1, 365)
        grid.addWidget(self.check_days, row, 1)
        row += 1

        layout.addLayout(grid)
        layout.addStretch()

        # Buttons
        button_layout = QVBoxLayout()
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def _load_settings(self):
        """Load settings from database."""
        try:
            all_settings = self.db.get_all_settings()

            self.smtp_server.setText(all_settings.get("smtp_server", ""))
            self.smtp_port.setValue(int(all_settings.get("smtp_port", "587")))
            self.smtp_email.setText(all_settings.get("smtp_email", ""))
            self.smtp_password.setText(all_settings.get("smtp_password", ""))
            self.smtp_recipient.setText(all_settings.get("smtp_recipient", ""))
            self.backup_folder.setText(all_settings.get("backup_folder", ""))
            self.check_days.setValue(int(all_settings.get("expiration_check_days", "30")))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load settings: {str(e)}")

    def save_settings(self):
        """Save settings to database."""
        try:
            self.db.set_setting("smtp_server", self.smtp_server.text())
            self.db.set_setting("smtp_port", str(self.smtp_port.value()))
            self.db.set_setting("smtp_email", self.smtp_email.text())
            self.db.set_setting("smtp_password", self.smtp_password.text())
            self.db.set_setting("smtp_recipient", self.smtp_recipient.text())
            self.db.set_setting("backup_folder", self.backup_folder.text())
            self.db.set_setting("expiration_check_days", str(self.check_days.value()))

            QMessageBox.information(self, "Success", "Settings saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def choose_backup_folder(self):
        """Choose backup folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Backup Folder")
        if folder:
            self.backup_folder.setText(folder)

    def test_email(self):
        """Test email configuration."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            server = self.smtp_server.text()
            port = self.smtp_port.value()
            email = self.smtp_email.text()
            password = self.smtp_password.text()
            recipient = self.smtp_recipient.text()

            if not all([server, email, password, recipient]):
                QMessageBox.warning(self, "Error", "Please fill all SMTP fields.")
                return

            msg = MIMEMultipart()
            msg["From"] = email
            msg["To"] = recipient
            msg["Subject"] = "Test Email - License Management System"
            body = "This is a test email from the License Management System.\n\nIf you received this, email notifications are working!"
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(server, port) as smtp:
                smtp.starttls()
                smtp.login(email, password)
                smtp.send_message(msg)

            QMessageBox.information(self, "Success", f"Test email sent to {recipient}!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to send test email: {str(e)}")

    def _apply_language(self):
        """Apply language translations and RTL layout."""
        t = self.translations.get(self.current_language, {})
        self.setWindowTitle(t.get("window_title_settings", "Settings"))
        self.title.setText(t.get("main_title_settings", "Application Settings"))
        self.smtp_title.setText(t.get("smtp_section", "Email Notifications (SMTP)"))
        self.smtp_server_label.setText(t.get("smtp_server", "SMTP Server:"))
        self.smtp_port_label.setText(t.get("smtp_port", "SMTP Port:"))
        self.smtp_email_label.setText(t.get("smtp_email", "Email Address:"))
        self.smtp_password_label.setText(t.get("smtp_password", "Password:"))
        self.smtp_recipient_label.setText(t.get("smtp_recipient", "Recipient Email:"))
        self.test_btn.setText(t.get("test_email", "Test Email Configuration"))
        self.backup_title.setText(t.get("backup_section", "Backup Settings"))
        self.backup_label.setText(t.get("backup_folder", "Backup Folder:"))
        self.browse_btn.setText(t.get("browse", "Browse..."))
        self.check_days_label.setText(t.get("expiration_check_days", "Daily Expiration Check (Days):"))
        self.save_btn.setText(t.get("save_settings", "Save Settings"))
        self.close_btn.setText(t.get("close", "Close"))

        is_arabic = self.current_language == "ar"
        self.setLayoutDirection(Qt.RightToLeft if is_arabic else Qt.LeftToRight)
