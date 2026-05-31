from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from datetime import datetime

class DataEntryWindow(QDialog):
    """Data Entry Form for adding licenses, vehicles, and companies."""

    def __init__(self, database, language="en", translations=None):
        super().__init__()
        self.db = database
        self.current_language = language
        self.translations = translations or {}
        self.setWindowTitle("Add New License Record")
        self.resize(700, 900)
        # Enable minimize and maximize buttons
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self._build_ui()
        self._apply_language()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        self.title = QLabel("New License Record")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title.setFont(title_font)
        layout.addWidget(self.title)

        # Subtitle explaining multiple records support
        self.subtitle = QLabel("Add license records for vehicles and drivers. One company can have multiple vehicles, and each vehicle can have multiple drivers.")
        self.subtitle.setStyleSheet("color: #6b7280; font-size: 10pt; font-style: italic;")
        layout.addWidget(self.subtitle)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        grid = QGridLayout(scroll_widget)
        grid.setSpacing(10)
        row = 0

        # Company Section
        self.company_title = QLabel("Company Information")
        self.company_title.setStyleSheet("font-weight: 600; color: #0f766e;")
        grid.addWidget(self.company_title, row, 0, 1, 2)
        row += 1

        self.company_name_label = QLabel("Company Name:")
        grid.addWidget(self.company_name_label, row, 0)
        self.company_name = QLineEdit()
        grid.addWidget(self.company_name, row, 1)
        row += 1

        self.company_reg_label = QLabel("Registration Number:")
        grid.addWidget(self.company_reg_label, row, 0)
        self.company_reg = QLineEdit()
        grid.addWidget(self.company_reg, row, 1)
        row += 1

        self.company_address_label = QLabel("Address:")
        grid.addWidget(self.company_address_label, row, 0)
        self.company_address = QTextEdit()
        self.company_address.setMaximumHeight(60)
        grid.addWidget(self.company_address, row, 1)
        row += 1

        self.carrier_type_label = QLabel("Carrier Type:")
        grid.addWidget(self.carrier_type_label, row, 0)
        self.carrier_type = QComboBox()
        self.carrier_type.addItems(["Public", "Private"])
        grid.addWidget(self.carrier_type, row, 1)
        row += 1

        self.account_type_label = QLabel("Account Type:")
        grid.addWidget(self.account_type_label, row, 0)
        self.account_type = QComboBox()
        self.account_type.addItems(["Public", "Private"])
        grid.addWidget(self.account_type, row, 1)
        row += 1

        # Vehicle Section
        self.vehicle_title = QLabel("Vehicle Information")
        self.vehicle_title.setStyleSheet("font-weight: 600; color: #0f766e;")
        grid.addWidget(self.vehicle_title, row, 0, 1, 2)
        row += 1

        self.vehicle_reg_label = QLabel("Vehicle Registration:")
        grid.addWidget(self.vehicle_reg_label, row, 0)
        self.vehicle_reg = QLineEdit()
        grid.addWidget(self.vehicle_reg, row, 1)
        row += 1

        self.vehicle_type_label = QLabel("Vehicle Type:")
        grid.addWidget(self.vehicle_type_label, row, 0)
        self.vehicle_type = QLineEdit()
        grid.addWidget(self.vehicle_type, row, 1)
        row += 1

        self.vehicle_category_label = QLabel("Vehicle Category:")
        grid.addWidget(self.vehicle_category_label, row, 0)
        self.vehicle_category = QLineEdit()
        grid.addWidget(self.vehicle_category, row, 1)
        row += 1

        # Route Section
        self.route_title = QLabel("Route Information")
        self.route_title.setStyleSheet("font-weight: 600; color: #0f766e;")
        grid.addWidget(self.route_title, row, 0, 1, 2)
        row += 1



        self.route_dest_label = QLabel("Destination:")
        grid.addWidget(self.route_dest_label, row, 0)
        self.route_dest = QLineEdit()
        grid.addWidget(self.route_dest, row, 1)
        row += 1

        self.route_checkpoints_label = QLabel("Checkpoints (optional):")
        grid.addWidget(self.route_checkpoints_label, row, 0)
        self.route_checkpoints = QTextEdit()
        self.route_checkpoints.setMaximumHeight(60)
        grid.addWidget(self.route_checkpoints, row, 1)
        row += 1

        # License Section
        self.license_title = QLabel("License Information")
        self.license_title.setStyleSheet("font-weight: 600; color: #0f766e;")
        grid.addWidget(self.license_title, row, 0, 1, 2)
        row += 1

        self.record_number_label = QLabel("Record Number:")
        grid.addWidget(self.record_number_label, row, 0)
        self.record_number = QLineEdit()
        grid.addWidget(self.record_number, row, 1)
        row += 1

        self.license_number_label = QLabel("License Number:")
        grid.addWidget(self.license_number_label, row, 0)
        self.license_number = QLineEdit()
        grid.addWidget(self.license_number, row, 1)
        row += 1

        self.driver_name_label = QLabel("Driver Name:")
        grid.addWidget(self.driver_name_label, row, 0)
        self.driver_name = QLineEdit()
        grid.addWidget(self.driver_name, row, 1)
        row += 1

        self.driver_phone_label = QLabel("Driver Phone:")
        grid.addWidget(self.driver_phone_label, row, 0)
        self.driver_phone = QLineEdit()
        grid.addWidget(self.driver_phone, row, 1)
        row += 1

        self.signature_date_label = QLabel("Signature Date:")
        grid.addWidget(self.signature_date_label, row, 0)
        self.signature_date = QDateEdit()
        self.signature_date.setDate(datetime.now())
        grid.addWidget(self.signature_date, row, 1)
        row += 1

        self.expiry_date_label = QLabel("Expiration Date:")
        grid.addWidget(self.expiry_date_label, row, 0)
        self.expiration_date = QDateEdit()
        self.expiration_date.setDate(datetime.now())
        grid.addWidget(self.expiration_date, row, 1)
        row += 1

        # Hazmat Section
        self.hazmat_title = QLabel("Hazardous Materials")
        self.hazmat_title.setStyleSheet("font-weight: 600; color: #0f766e;")
        grid.addWidget(self.hazmat_title, row, 0, 1, 2)
        row += 1

        self.hazmat_type_label = QLabel("Material Type (optional):")
        grid.addWidget(self.hazmat_type_label, row, 0)
        self.hazmat_type = QLineEdit()
        grid.addWidget(self.hazmat_type, row, 1)
        row += 1

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        layout.addStretch()

        # Buttons
        button_layout = QVBoxLayout()
        self.save_btn = QPushButton("Save Record")
        self.clear_btn = QPushButton("Clear Form")
        self.close_btn = QPushButton("Close")

        self.save_btn.clicked.connect(self.save_record)
        self.clear_btn.clicked.connect(self.clear_form)
        self.close_btn.clicked.connect(self.close)

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)

    def save_record(self):
        """Save the entire record to database."""
        val_errors = {
            "en": {
                "err_required": "Please fill all required fields.",
                "err_rec_num": "Registration number must follow a numeric format.",
                "err_veh_reg": "Vehicle registration number must follow a numeric format.",
                "err_comp_reg": "Registry Number must follow a numeric format.",
                "err_name_nums": "Carrier name must not contain numbers.",
                "err_chronology": "Expiration date must be later than start date",
                "err_dest_format": "Destination must follow a text format.",
                "title_error": "Validation Error",
            },
            "fr": {
                "err_required": "Veuillez remplir tous les champs obligatoires.",
                "err_rec_num": "Le numéro d'enregistrement doit être au format numérique.",
                "err_veh_reg": "Le numéro d'immatriculation du véhicule doit être au format numérique.",
                "err_comp_reg": "Le numéro de registre doit être au format numérique.",
                "err_name_nums": "Le nom du transporteur ne doit pas contenir de chiffres.",
                "err_chronology": "La date d'expiration doit être ultérieure à la date de début",
                "err_dest_format": "La destination doit être au format texte.",
                "title_error": "Erreur de validation",
            },
            "ar": {
                "err_required": "يرجى ملء جميع الحقول المطلوبة.",
                "err_rec_num": "رقم التسجيل يجب أن يكون بصيغة رقمية.",
                "err_veh_reg": "رقم تسجيل المركبة يجب أن يكون بصيغة رقمية.",
                "err_comp_reg": "رقم القيد يجب أن يكون بصيغة رقمية.",
                "err_name_nums": "اسم الناقل يجب ألا يحتوي على أرقام.",
                "err_chronology": "يجب أن يكون تاريخ انتهاء الصلاحية بعد تاريخ البدء",
                "err_dest_format": "يجب أن تكون الوجهة بصيغة نصية.",
                "title_error": "خطأ في التحقق",
            }
        }
        try:
            lang = self.current_language if self.current_language in ["en", "fr", "ar"] else "en"
            t_err = val_errors[lang]

            # Validate all required fields
            if not all([
                self.company_name.text().strip(),
                self.company_address.toPlainText().strip(),
                self.vehicle_reg.text().strip(),
                self.vehicle_type.text().strip(),
                self.vehicle_category.text().strip(),
                self.route_dest.text().strip(),
                self.record_number.text().strip(),
                self.license_number.text().strip(),
                self.hazmat_type.text().strip(),
            ]):
                QMessageBox.warning(self, t_err["title_error"], t_err["err_required"])
                return

            company_reg = self.company_reg.text().strip()
            vehicle_reg = self.vehicle_reg.text().strip()
            license_num = self.license_number.text().strip()
            record_num = self.record_number.text().strip()
            company_name = self.company_name.text().strip()

            # Format check: Registration/Record number must be numeric
            if not record_num.isdigit():
                QMessageBox.warning(self, t_err["title_error"], t_err["err_rec_num"])
                return

            # Format check: Vehicle registration must be numeric
            if not vehicle_reg.isdigit():
                QMessageBox.warning(self, t_err["title_error"], t_err["err_veh_reg"])
                return

            # Format check: Company registration must be numeric if provided
            if company_reg and not company_reg.isdigit():
                QMessageBox.warning(self, t_err["title_error"], t_err["err_comp_reg"])
                return

            # Format check: Company name must not contain digits
            if any(char.isdigit() for char in company_name):
                QMessageBox.warning(self, t_err["title_error"], t_err["err_name_nums"])
                return

            # Format check: Destination must follow a text format (not numeric-only)
            if route_dest.isdigit():
                QMessageBox.warning(self, t_err["title_error"], t_err["err_dest_format"])
                return

            # Chronology check: Expiration date must be later than signature date
            sig_date = self.signature_date.date()
            exp_date = self.expiration_date.date()
            if exp_date <= sig_date:
                QMessageBox.warning(self, t_err["title_error"], t_err["err_chronology"])
                return

            # Check if license already exists
            if self.db.get_license_by_number(license_num):
                QMessageBox.warning(self, "Error", f"License number {license_num} already exists.")
                return

            if self.db.get_license_by_record_number(record_num):
                QMessageBox.warning(self, "Error", f"Record number {record_num} already exists.")
                return

            # Check if company exists, or create it
            company_id = None
            if company_reg:
                existing_company = self.db.get_company_by_registration(company_reg)
                if existing_company:
                    company_id = existing_company["id"]
                else:
                    company_id = self.db.add_company(
                        self.company_name.text(),
                        company_reg,
                        self.company_address.toPlainText(),
                        self.carrier_type.currentText(),
                        self.account_type.currentText(),
                    )
            else:
                # Create company without registration number
                company_id = self.db.add_company(
                    self.company_name.text(),
                    None,
                    self.company_address.toPlainText(),
                    self.carrier_type.currentText(),
                    self.account_type.currentText(),
                )

            # Check if vehicle exists, or create it
            vehicle_id = None
            existing_vehicle = self.db.get_vehicle_by_registration(vehicle_reg)
            if existing_vehicle:
                vehicle_id = existing_vehicle["id"]
            else:
                vehicle_id = self.db.add_vehicle(
                    company_id,
                    vehicle_reg,
                    self.vehicle_type.text(),
                    self.vehicle_category.text(),
                )

            # Add route
            route_id = self.db.add_route(
                "",
                self.route_dest.text().strip(),
                self.route_checkpoints.toPlainText(),
            )

            # Add license
            self.db.add_license(
                vehicle_id,
                route_id,
                record_num,
                self.driver_name.text(),
                self.driver_phone.text(),
                license_num,
                self.signature_date.date().toString("yyyy-MM-dd"),
                self.expiration_date.date().toString("yyyy-MM-dd"),
            )

            # Add hazmat if provided
            if self.hazmat_type.text():
                self.db.add_hazmat(
                    vehicle_id,
                    self.hazmat_type.text(),
                )

            QMessageBox.information(self, "Success", "Record saved successfully!")
            self.clear_form()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save record: {str(e)}")

    def clear_form(self):
        """Clear all form fields."""
        self.company_name.clear()
        self.company_reg.clear()
        self.company_address.clear()
        self.vehicle_reg.clear()
        self.vehicle_type.clear()
        self.vehicle_category.clear()
        self.route_dest.clear()
        self.route_checkpoints.clear()
        self.record_number.clear()
        self.license_number.clear()
        self.driver_name.clear()
        self.driver_phone.clear()
        self.hazmat_type.clear()
        self.signature_date.setDate(datetime.now())
        self.expiration_date.setDate(datetime.now())

    def _apply_language(self):
        """Apply language translations and RTL layout."""
        t = self.translations.get(self.current_language, {})
        self.setWindowTitle(t.get("window_title_data_entry", "Add New License Record"))
        self.title.setText(t.get("main_title_data_entry", "New License Record"))
        self.subtitle.setText(t.get("data_entry_subtitle", "Add license records for vehicles and drivers. One company can have multiple vehicles, and each vehicle can have multiple drivers."))
        
        # Section titles
        self.company_title.setText(t.get("company_section", "Company Information"))
        self.vehicle_title.setText(t.get("vehicle_section", "Vehicle Information"))
        self.route_title.setText(t.get("route_section", "Route Information"))
        self.license_title.setText(t.get("licence_section", "License Information"))
        self.hazmat_title.setText(t.get("hazmat_section", "Hazardous Materials"))
        
        # Company labels
        self.company_name_label.setText(t.get("company_name", "Company Name:"))
        self.company_reg_label.setText(t.get("registration_number", "Registration Number:"))
        self.company_address_label.setText(t.get("address", "Address:"))
        self.carrier_type_label.setText(t.get("carrier_type", "Carrier Type:"))
        self.account_type_label.setText(t.get("account_type", "Account Type:"))
        
        # Vehicle labels
        self.vehicle_reg_label.setText(t.get("vehicle_registration", "Vehicle Registration:"))
        self.vehicle_type_label.setText(t.get("vehicle_type", "Vehicle Type:"))
        self.vehicle_category_label.setText(t.get("vehicle_category", "Vehicle Category:"))
        
        # Route labels
        self.route_dest_label.setText(t.get("destination", "Destination:"))
        self.route_checkpoints_label.setText(t.get("checkpoints", "Checkpoints (optional):"))
        
        # License labels
        self.record_number_label.setText(t.get("record_number_label", "Record Number:"))
        self.license_number_label.setText(t.get("licence_number", "License Number:"))
        self.driver_name_label.setText(t.get("driver_name", "Driver Name:"))
        self.driver_phone_label.setText(t.get("driver_phone_label", "Driver Phone:"))
        self.signature_date_label.setText(t.get("signature_date", "Signature Date:"))
        self.expiry_date_label.setText(t.get("expiry_date", "Expiration Date:"))
        
        # Hazmat labels
        self.hazmat_type_label.setText(t.get("hazmat_type", "Material Type (optional):"))
        
        # Buttons
        self.save_btn.setText(t.get("save_record", "Save Record"))
        self.clear_btn.setText(t.get("clear_form", "Clear Form"))
        self.close_btn.setText(t.get("close", "Close"))
        
        # Update combo box items
        public_text = t.get("public", "Public")
        private_text = t.get("private", "Private")
        self.carrier_type.blockSignals(True)
        self.account_type.blockSignals(True)
        
        current_carrier = self.carrier_type.currentText()
        current_account = self.account_type.currentText()
        
        self.carrier_type.clear()
        self.carrier_type.addItems([public_text, private_text])
        self.account_type.clear()
        self.account_type.addItems([public_text, private_text])
        
        self.carrier_type.blockSignals(False)
        self.account_type.blockSignals(False)

        is_arabic = self.current_language == "ar"
        self.setLayoutDirection(Qt.RightToLeft if is_arabic else Qt.LeftToRight)
