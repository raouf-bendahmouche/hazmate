from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)
from datetime import datetime

class SearchRecordsWindow(QDialog):
    """Search and view license records with filtering."""

    def __init__(self, database, language="en", translations=None):
        super().__init__()
        self.db = database
        self.current_language = language
        self.translations = translations or {}
        self.setWindowTitle("Search & Records")
        self.resize(1200, 700)
        # Enable minimize and maximize buttons
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self._build_ui()
        self._apply_language()
        self.load_records()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        self.title = QLabel("Search License Records")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title.setFont(title_font)
        layout.addWidget(self.title)

        # Search Bar
        search_layout = QHBoxLayout()
        self.search_label = QLabel("Search:")
        search_layout.addWidget(self.search_label)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("إبحث بالإسم السائق، رقم الرخصة، الشركة، أو رقم المركبة... ")
        search_layout.addWidget(self.search_input)

        self.status_label = QLabel("Status:")
        search_layout.addWidget(self.status_label)
        self.status_filter = QComboBox()
        self.status_filter.addItem("All", None)
        self.status_filter.addItem("Active", "active")
        self.status_filter.addItem("Expired", "expired")
        search_layout.addWidget(self.status_filter)

        self.carrier_label = QLabel("Carrier Type:")
        search_layout.addWidget(self.carrier_label)
        self.carrier_filter = QComboBox()
        self.carrier_filter.addItem("All", None)
        self.carrier_filter.addItem("Public", "Public")
        self.carrier_filter.addItem("Private", "Private")
        search_layout.addWidget(self.carrier_filter)

        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_records)
        search_layout.addWidget(self.search_btn)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_records)
        search_layout.addWidget(self.refresh_btn)

        layout.addLayout(search_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Record #", "License #", "Driver", "Phone", 
            "Vehicle Reg", "Company", "Carrier", "Expiration", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.table)

        # Action Buttons
        action_layout = QHBoxLayout()
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.edit_record)
        action_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_record)
        action_layout.addWidget(self.delete_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)

        # Info label
        self.info_label = QLabel("Loading records...")
        layout.addWidget(self.info_label)

    def load_records(self):
        """Load all records into table."""
        try:
            records = self.db.get_all_licenses()
            self._populate_table(records)
        except Exception as e:
            self.info_label.setText(f"Error loading records: {str(e)}")

    def search_records(self):
        """Search records based on filters."""
        try:
            search_term = self.search_input.text()
            status = self.status_filter.currentData()
            carrier = self.carrier_filter.currentData()

            records = self.db.search_licenses(search_term, status, carrier)
            self._populate_table(records)
        except Exception as e:
            self.info_label.setText(f"Error searching records: {str(e)}")

    def _populate_table(self, records):
        """Populate table with records."""
        self.table.setRowCount(0)

        for idx, record in enumerate(records):
            self.table.insertRow(idx)

            items = [
                str(record["record_number"] or ""),
                str(record["license_number"] or ""),
                str(record["driver_name"] or ""),
                str(record["driver_phone"] or ""),
                str(record["vehicle_reg"] or ""),
                str(record["company_name"] or ""),
                str(record["carrier_type"] or ""),
                str(record["expiration_date"] or ""),
                str(record["status"] or ""),
            ]

            for col, item_text in enumerate(items):
                item = QTableWidgetItem(item_text)
                self.table.setItem(idx, col, item)

        self.info_label.setText(f"Showing {len(records)} records")

    def edit_record(self):
        """Edit selected record."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Error", "Please select a record to edit.")
            return
        
        # Get license_id from the hidden data (we'll need to store it)
        # For now, get it from record number
        record_number = self.table.item(selected_row, 0).text()
        
        try:
            # Find the license with this record number
            records = self.db.search_licenses(record_number, None, None)
            if records:
                license_data = records[0]
                # TODO: Open edit dialog with license_data
                QMessageBox.information(self, "Edit", f"Editing record: {record_number}\nFeature coming soon!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit record: {str(e)}")

    def delete_record(self):
        """Delete selected record."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Error", "Please select a record to delete.")
            return
        
        record_number = self.table.item(selected_row, 0).text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete record {record_number}?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                records = self.db.search_licenses(record_number, None, None)
                if records:
                    license_id = records[0]["id"]
                    self.db.delete_license(license_id)
                    QMessageBox.information(self, "Success", f"Record {record_number} deleted successfully!")
                    self.load_records()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete record: {str(e)}")

    def _populate_combo_items(self):
        """Update combo box items with translated text."""
        t = self.translations.get(self.current_language, {})
        
        # Clear and repopulate status filter
        self.status_filter.blockSignals(True)
        current_status = self.status_filter.currentData()
        self.status_filter.clear()
        self.status_filter.addItem(t.get("all_status", "All"), None)
        self.status_filter.addItem(t.get("active_status", "Active"), "active")
        self.status_filter.addItem(t.get("expired_status", "Expired"), "expired")
        # Restore previous selection
        index = self.status_filter.findData(current_status)
        if index >= 0:
            self.status_filter.setCurrentIndex(index)
        self.status_filter.blockSignals(False)

        # Clear and repopulate carrier filter
        self.carrier_filter.blockSignals(True)
        current_carrier = self.carrier_filter.currentData()
        self.carrier_filter.clear()
        self.carrier_filter.addItem(t.get("all_carrier", "All"), None)
        self.carrier_filter.addItem(t.get("public_carrier", "Public"), "Public")
        self.carrier_filter.addItem(t.get("private_carrier", "Private"), "Private")
        # Restore previous selection
        index = self.carrier_filter.findData(current_carrier)
        if index >= 0:
            self.carrier_filter.setCurrentIndex(index)
        self.carrier_filter.blockSignals(False)

    def _apply_language(self):
        """Apply language translations and RTL layout."""
        t = self.translations.get(self.current_language, {})
        self.setWindowTitle(t.get("window_title_search", "Search & Records"))
        self.title.setText(t.get("main_title_search", "Search License Records"))
        self.search_label.setText(t.get("search", "Search:"))
        self.status_label.setText(t.get("status", "Status:"))
        self.carrier_label.setText(t.get("carrier_type", "Carrier Type:"))
        self.search_btn.setText(t.get("search_records", "Search"))
        self.refresh_btn.setText(t.get("refresh", "Refresh"))
        self.edit_btn.setText(t.get("edit", "Edit"))
        self.delete_btn.setText(t.get("delete", "Delete"))

        # Update table headers
        self.table.setHorizontalHeaderLabels([
            t.get("record_number", "Record #"),
            t.get("license_number", "License #"),
            t.get("driver", "Driver"),
            t.get("phone", "Phone"),
            t.get("vehicle_reg", "Vehicle Reg"),
            t.get("company", "Company"),
            t.get("carrier", "Carrier"),
            t.get("expiration", "Expiration"),
            t.get("status_col", "Status")
        ])

        # Update combo box items
        self._populate_combo_items()

        is_arabic = self.current_language == "ar"
        self.setLayoutDirection(Qt.RightToLeft if is_arabic else Qt.LeftToRight)
