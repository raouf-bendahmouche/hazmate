from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QHeaderView,
    QMessageBox,
)


class ManagementWindow(QDialog):
    """Window for managing (deleting) companies, vehicles, and drivers."""

    def __init__(self, database, language="en", translations=None):
        super().__init__()
        self.db = database
        self.current_language = language
        self.translations = translations or {}
        self.setWindowTitle("Manage Data")
        self.resize(1200, 700)
        # Enable minimize and maximize buttons
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self._build_ui()
        self._apply_language()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.title = QLabel("Manage Data - Delete Records")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title.setFont(title_font)
        layout.addWidget(self.title)

        # Create tabs
        self.tabs = QTabWidget()

        # Companies tab
        self.companies_table = self._create_table(5, ["ID", "Name", "Registration", "Type", "Address"])
        self._populate_companies_table()
        companies_layout = QVBoxLayout()
        companies_layout.addWidget(self.companies_table)
        
        companies_btn_layout = QHBoxLayout()
        self.delete_company_btn = QPushButton("Delete Selected Company")
        self.delete_company_btn.clicked.connect(self.delete_company)
        companies_btn_layout.addStretch()
        companies_btn_layout.addWidget(self.delete_company_btn)
        companies_layout.addLayout(companies_btn_layout)
        
        companies_widget = QDialog(self)
        companies_widget.setLayout(companies_layout)
        self.tabs.addTab(companies_widget, "Companies")

        # Vehicles tab
        self.vehicles_table = self._create_table(5, ["ID", "Reg #", "Type", "Category", "Company"])
        self._populate_vehicles_table()
        vehicles_layout = QVBoxLayout()
        vehicles_layout.addWidget(self.vehicles_table)
        
        vehicles_btn_layout = QHBoxLayout()
        self.delete_vehicle_btn = QPushButton("Delete Selected Vehicle")
        self.delete_vehicle_btn.clicked.connect(self.delete_vehicle)
        vehicles_btn_layout.addStretch()
        vehicles_btn_layout.addWidget(self.delete_vehicle_btn)
        vehicles_layout.addLayout(vehicles_btn_layout)
        
        vehicles_widget = QDialog(self)
        vehicles_widget.setLayout(vehicles_layout)
        self.tabs.addTab(vehicles_widget, "Vehicles")

        # Drivers tab (via licenses)
        self.drivers_table = self._create_table(5, ["License ID", "Driver Name", "Phone", "Company", "Vehicle Reg"])
        self._populate_drivers_table()
        drivers_layout = QVBoxLayout()
        drivers_layout.addWidget(self.drivers_table)
        
        drivers_btn_layout = QHBoxLayout()
        self.delete_driver_btn = QPushButton("Delete Selected Driver License")
        self.delete_driver_btn.clicked.connect(self.delete_driver)
        drivers_btn_layout.addStretch()
        drivers_btn_layout.addWidget(self.delete_driver_btn)
        drivers_layout.addLayout(drivers_btn_layout)
        
        drivers_widget = QDialog(self)
        drivers_widget.setLayout(drivers_layout)
        self.tabs.addTab(drivers_widget, "Drivers")

        layout.addWidget(self.tabs)

        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        close_layout.addWidget(self.close_btn)
        layout.addLayout(close_layout)

    def _create_table(self, columns, headers):
        """Create a table widget."""
        table = QTableWidget()
        table.setColumnCount(columns)
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        return table

    def _populate_companies_table(self):
        """Populate companies table."""
        try:
            companies = self.db.get_companies()
            self.companies_table.setRowCount(len(companies))

            for idx, company in enumerate(companies):
                # Convert sqlite3.Row to dict for easier access
                company_dict = dict(company) if hasattr(company, 'keys') else company
                items = [
                    str(company_dict.get("id", "")),
                    str(company_dict.get("name", "")),
                    str(company_dict.get("registration_number", "")),
                    str(company_dict.get("carrier_type", "")),
                    str(company_dict.get("address", "")),
                ]
                for col, item_text in enumerate(items):
                    self.companies_table.setItem(idx, col, QTableWidgetItem(item_text))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load companies: {str(e)}")

    def _populate_vehicles_table(self):
        """Populate vehicles table."""
        try:
            vehicles = self.db.get_vehicles()
            self.vehicles_table.setRowCount(len(vehicles))

            for idx, vehicle in enumerate(vehicles):
                # Convert sqlite3.Row to dict for easier access
                vehicle_dict = dict(vehicle) if hasattr(vehicle, 'keys') else vehicle
                company = self.db.get_company_by_id(vehicle_dict["company_id"])
                company_dict = dict(company) if hasattr(company, 'keys') else company
                company_name = company_dict.get("name", "Unknown") if company else "Unknown"
                
                items = [
                    str(vehicle_dict.get("id", "")),
                    str(vehicle_dict.get("registration_number", "")),
                    str(vehicle_dict.get("type", "")),
                    str(vehicle_dict.get("category", "")),
                    company_name,
                ]
                for col, item_text in enumerate(items):
                    self.vehicles_table.setItem(idx, col, QTableWidgetItem(item_text))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load vehicles: {str(e)}")

    def _populate_drivers_table(self):
        """Populate drivers table."""
        try:
            licenses = self.db.get_all_licenses()
            self.drivers_table.setRowCount(len(licenses))

            for idx, license_data in enumerate(licenses):
                # Convert sqlite3.Row to dict for easier access
                license_dict = dict(license_data) if hasattr(license_data, 'keys') else license_data
                items = [
                    str(license_dict.get("id", "")),
                    str(license_dict.get("driver_name", "")),
                    str(license_dict.get("driver_phone", "")),
                    str(license_dict.get("company_name", "")),
                    str(license_dict.get("vehicle_reg", "")),
                ]
                for col, item_text in enumerate(items):
                    self.drivers_table.setItem(idx, col, QTableWidgetItem(item_text))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load drivers: {str(e)}")

    def delete_company(self):
        """Delete selected company."""
        row = self.companies_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select a company to delete.")
            return

        company_id = int(self.companies_table.item(row, 0).text())
        company_name = self.companies_table.item(row, 1).text()

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete company '{company_name}'?\n\nThis will also delete all associated vehicles and licenses.\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.delete_company(company_id)
                QMessageBox.information(self, "Success", f"Company '{company_name}' deleted successfully!")
                self._populate_companies_table()
                self._populate_vehicles_table()
                self._populate_drivers_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete company: {str(e)}")

    def delete_vehicle(self):
        """Delete selected vehicle."""
        row = self.vehicles_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select a vehicle to delete.")
            return

        vehicle_id = int(self.vehicles_table.item(row, 0).text())
        vehicle_reg = self.vehicles_table.item(row, 1).text()

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete vehicle '{vehicle_reg}'?\n\nThis will also delete all associated licenses.\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.delete_vehicle(vehicle_id)
                QMessageBox.information(self, "Success", f"Vehicle '{vehicle_reg}' deleted successfully!")
                self._populate_vehicles_table()
                self._populate_drivers_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete vehicle: {str(e)}")

    def delete_driver(self):
        """Delete selected driver license."""
        row = self.drivers_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select a driver to delete.")
            return

        license_id = int(self.drivers_table.item(row, 0).text())
        driver_name = self.drivers_table.item(row, 1).text()

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete driver license for '{driver_name}'?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.delete_license(license_id)
                QMessageBox.information(self, "Success", f"Driver license for '{driver_name}' deleted successfully!")
                self._populate_drivers_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete driver: {str(e)}")

    def _apply_language(self):
        """Apply language translations."""
        t = self.translations.get(self.current_language, {})
        self.setWindowTitle(t.get("window_title_management", "Manage Data"))
        self.title.setText(t.get("manage_data", "Manage Data - Delete Records"))

        is_arabic = self.current_language == "ar"
        self.setLayoutDirection(Qt.RightToLeft if is_arabic else Qt.LeftToRight)
