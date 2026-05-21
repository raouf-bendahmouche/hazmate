from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLCDNumber,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from ui.data_entry import DataEntryWindow
from ui.search import SearchRecordsWindow
from ui.settings import SettingsWindow


class DashboardWindow(QMainWindow):
    """Main dashboard with database integration, statistics, and window navigation."""

    def __init__(self, database, scheduler):
        super().__init__()
        self.db = database
        self.scheduler = scheduler
        self.resize(1000, 680)
        self.setMinimumSize(820, 560)

        self.current_language = "ar"
        self.translations = {
            "en": {
                "window_title": "License Management - Dashboard",
                "main_title": "Main Dashboard",
                "subtitle": "License Management System",
                "language": "Language",
                "add_record": "Add Record",
                "search_records": "Search Records",
                "settings": "Settings",
                "refresh": "Refresh",
                "total_vehicles": "Total Vehicles",
                "total_drivers": "Total Drivers",
                "active_licenses": "Active Licenses",
                "expired_licenses": "Expired Licenses",
                "window_title_data_entry": "Add New License Record",
                "main_title_data_entry": "New License Record",
                "data_entry_subtitle": "Add license records for vehicles and drivers. One company can have multiple vehicles, and each vehicle can have multiple drivers.",
                "company_section": "Company Information",
                "company_name": "Company Name:",
                "company_type": "Company Type:",
                "vehicle_section": "Vehicle Information",
                "vehicle_plate": "Vehicle Plate:",
                "vehicle_type": "Vehicle Type:",
                "vehicle_model": "Vehicle Model:",
                "chassis_number": "Chassis Number:",
                "route_section": "Route Information",
                "route_name": "Route Name:",
                "driver_section": "Driver Information",
                "driver_name": "Driver Name:",
                "driver_phone": "Phone:",
                "driver_email": "Email:",
                "licence_section": "License Information",
                "licence_number": "License Number:",
                "licence_type": "License Type:",
                "issue_date": "Issue Date:",
                "expiry_date": "Expiry Date:",
                "hazmat_section": "Hazardous Materials",
                "hazmat_categories": "Categories Approved:",
                "save_record": "Save Record",
                "clear_form": "Clear Form",
                "close": "Close",
                "window_title_search": "Search License Records",
                "main_title_search": "Search License Records",
                "search": "Search:",
                "status": "Status:",
                "carrier_type": "Carrier Type:",
                "search_placeholder": "Search by driver name, plate, or license...",
                "results_found": "Results found",
                "driver": "Driver",
                "vehicle_plate_col": "Vehicle Plate",
                "status_col": "Status",
                "expiry_col": "Expiry Date",
                "window_title_settings": "Settings",
                "main_title_settings": "Application Settings",
                "smtp_section": "Email Notifications (SMTP)",
                "smtp_server": "SMTP Server:",
                "smtp_port": "SMTP Port:",
                "smtp_email": "Email Address:",
                "smtp_password": "Password:",
                "smtp_recipient": "Recipient Email:",
                "test_email": "Test Email Configuration",
                "backup_section": "Backup Settings",
                "backup_folder": "Backup Folder:",
                "browse": "Browse...",
                "expiration_check_days": "Daily Expiration Check (Days):",
                "save_settings": "Save Settings",
                "close": "Close",
                "edit": "Edit",
                "delete": "Delete",
                "record_number": "Record #",
                "license_number": "License #",
                "driver": "Driver",
                "phone": "Phone",
                "vehicle_reg": "Vehicle Reg",
                "company": "Company",
                "carrier": "Carrier",
                "expiration": "Expiration",
                "all_status": "All",
                "active_status": "Active",
                "expired_status": "Expired",
                "all_carrier": "All",
                "public_carrier": "Public",
                "private_carrier": "Private",
                "statistics": "Statistics",
                "by_carrier_type": "Licenses by Carrier Type",
                "by_status": "Licenses by Status",
                "by_company": "Top Companies by License Count",
                "expiring_soon": "Licenses Expiring in 30 Days",
                "manage": "Manage",
                "window_title_management": "Manage Data",
                "manage_data": "Manage Data - Delete Records",
                "registration_number": "Registration Number:",
                "address": "Address:",
                "account_type": "Account Type:",
                "vehicle_registration": "Vehicle Registration:",
                "vehicle_category": "Vehicle Category:",
                "origin": "Origin:",
                "destination": "Destination:",
                "checkpoints": "Checkpoints (optional):",
                "record_number_label": "Record Number:",
                "driver_phone_label": "Driver Phone:",
                "signature_date": "Signature Date:",
                "hazmat_type": "Material Type (optional):",
                "public": "Public",
                "private": "Private",
            },
            "fr": {
                "window_title": "Gestion des Licences - Tableau de bord",
                "main_title": "Tableau de Bord Principal",
                "subtitle": "Systeme de gestion des licences",
                "language": "Langue",
                "add_record": "Ajouter un Dossier",
                "search_records": "Rechercher des Dossiers",
                "settings": "Parametres",
                "refresh": "Actualiser",
                "total_vehicles": "Vehicules Totaux",
                "total_drivers": "Conducteurs Totaux",
                "active_licenses": "Licences Actives",
                "expired_licenses": "Licences Expirees",
                "window_title_data_entry": "Ajouter un Nouveau Dossier de Licence",
                "main_title_data_entry": "Nouveau Dossier de Licence",
                "data_entry_subtitle": "Ajoutez des dossiers de licence pour les vehicules et les conducteurs. Une entreprise peut avoir plusieurs vehicules, et chaque vehicule peut avoir plusieurs conducteurs.",
                "company_section": "Informations de l'Entreprise",
                "company_name": "Nom de l'Entreprise:",
                "company_type": "Type d'Entreprise:",
                "vehicle_section": "Informations du Vehicule",
                "vehicle_plate": "Plaque du Vehicule:",
                "vehicle_type": "Type de Vehicule:",
                "vehicle_model": "Modele du Vehicule:",
                "chassis_number": "Numero de Chassis:",
                "route_section": "Informations de l'Itineraire",
                "route_name": "Nom de l'Itineraire:",
                "driver_section": "Informations du Conducteur",
                "driver_name": "Nom du Conducteur:",
                "driver_phone": "Telephone:",
                "driver_email": "Email:",
                "licence_section": "Informations de Licence",
                "licence_number": "Numero de Licence:",
                "licence_type": "Type de Licence:",
                "issue_date": "Date d'Emission:",
                "expiry_date": "Date d'Expiration:",
                "hazmat_section": "Matieres Dangereuses",
                "hazmat_categories": "Categories Approuvees:",
                "save_record": "Enregistrer",
                "clear_form": "Effacer",
                "close": "Fermer",
                "window_title_search": "Rechercher des Dossiers de Licence",
                "main_title_search": "Rechercher des Dossiers de Licence",
                "search": "Recherche:",
                "status": "Statut:",
                "carrier_type": "Type de Transporteur:",
                "search_placeholder": "Recherche par nom, plaque ou numero...",
                "results_found": "Resultats Trouves",
                "driver": "Conducteur",
                "vehicle_plate_col": "Plaque du Vehicule",
                "status_col": "Statut",
                "expiry_col": "Date d'Expiration",
                "window_title_settings": "Parametres",
                "main_title_settings": "Parametres de l'Application",
                "smtp_section": "Notifications par Email (SMTP)",
                "smtp_server": "Serveur SMTP:",
                "smtp_port": "Port SMTP:",
                "smtp_email": "Adresse Email:",
                "smtp_password": "Mot de Passe:",
                "smtp_recipient": "Email du Destinataire:",
                "test_email": "Tester la Configuration Email",
                "backup_section": "Parametres de Sauvegarde",
                "backup_folder": "Dossier de Sauvegarde:",
                "browse": "Parcourir...",
                "expiration_check_days": "Verification Quotidienne d'Expiration (Jours):",
                "save_settings": "Enregistrer les Parametres",
                "edit": "Modifier",
                "delete": "Supprimer",
                "record_number": "N° Dossier",
                "license_number": "N° Licence",
                "driver": "Conducteur",
                "phone": "Telephone",
                "vehicle_reg": "Plaque Vehicule",
                "company": "Entreprise",
                "carrier": "Transporteur",
                "expiration": "Expiration",
                "all_status": "Tous",
                "active_status": "Actif",
                "expired_status": "Expire",
                "all_carrier": "Tous",
                "public_carrier": "Public",
                "private_carrier": "Prive",
                "statistics": "Statistiques",
                "by_carrier_type": "Licences par Type de Transporteur",
                "by_status": "Licences par Statut",
                "by_company": "Top Entreprises par Nombre de Licences",
                "expiring_soon": "Licences Expirant dans 30 Jours",
                "manage": "Gerer",
                "window_title_management": "Gerer les Donnees",
                "manage_data": "Gerer les Donnees - Supprimer les Enregistrements",
                "registration_number": "Numero d'Enregistrement:",
                "address": "Adresse:",
                "account_type": "Type de Compte:",
                "vehicle_registration": "Immatriculation du Vehicule:",
                "vehicle_category": "Categorie du Vehicule:",
                "origin": "Origine:",
                "destination": "Destination:",
                "checkpoints": "Points de Controle (optional):",
                "record_number_label": "Numero de Dossier:",
                "driver_phone_label": "Telephone du Conducteur:",
                "signature_date": "Date de Signature:",
                "hazmat_type": "Type de Matiere (optional):",
                "public": "Public",
                "private": "Prive",
            },
            "ar": {
                "window_title": "إدارة التراخيص - لوحة التحكم",
                "main_title": "لوحة التحكم الرئيسية",
                "subtitle": "نظام إدارة التراخيص",
                "language": "اللغة",
                "add_record": "اضافة سجل",
                "search_records": "بحث السجلات",
                "settings": "الاعدادات",
                "refresh": "تحديث",
                "total_vehicles": "اجمالي المركبات",
                "total_drivers": "اجمالي السائقين",
                "active_licenses": "التراخيص النشطة",
                "expired_licenses": "التراخيص المنتهية",
                "window_title_data_entry": "إضافة سجل ترخيص جديد",
                "main_title_data_entry": "سجل ترخيص جديد",
                "data_entry_subtitle": "أضف سجلات ترخيص للمركبات والسائقين. يمكن لشركة واحدة أن تملك عدة مركبات، وكل مركبة يمكن أن يكون لها عدة سائقين.",
                "company_section": "معلومات الشركة",
                "company_name": "اسم الشركة:",
                "company_type": "نوع الشركة:",
                "vehicle_section": "معلومات المركبة",
                "vehicle_plate": "لوحة المركبة:",
                "vehicle_type": "نوع المركبة:",
                "vehicle_model": "موديل المركبة:",
                "chassis_number": "رقم الهيكل:",
                "route_section": "معلومات المسار",
                "route_name": "اسم المسار:",
                "driver_section": "معلومات السائق",
                "driver_name": "اسم السائق:",
                "driver_phone": "الهاتف:",
                "driver_email": "البريد الإلكتروني:",
                "licence_section": "معلومات الترخيص",
                "licence_number": "رقم الترخيص:",
                "licence_type": "نوع الترخيص:",
                "issue_date": "تاريخ الإصدار:",
                "expiry_date": "تاريخ الانتهاء:",
                "hazmat_section": "المواد الخطرة",
                "hazmat_categories": "الفئات الموافق عليها:",
                "save_record": "حفظ السجل",
                "clear_form": "مسح النموذج",
                "close": "إغلاق",
                "window_title_search": "البحث في سجلات الترخيص",
                "main_title_search": "البحث في سجلات الترخيص",
                "search": "البحث:",
                "status": "الحالة:",
                "carrier_type": "نوع الناقل:",
                "search_placeholder": "البحث بالاسم أو اللوحة أو الرقم...",
                "results_found": "النتائج المعثور عليها",
                "driver": "السائق",
                "vehicle_plate_col": "لوحة المركبة",
                "status_col": "الحالة",
                "expiry_col": "تاريخ الانتهاء",
                "window_title_settings": "الاعدادات",
                "main_title_settings": "إعدادات التطبيق",
                "smtp_section": "إشعارات البريد الإلكتروني (SMTP)",
                "smtp_server": "خادم SMTP:",
                "smtp_port": "منفذ SMTP:",
                "smtp_email": "عنوان البريد الإلكتروني:",
                "smtp_password": "كلمة المرور:",
                "smtp_recipient": "بريد المستقبل:",
                "test_email": "اختبار إعدادات البريد الإلكتروني",
                "backup_section": "إعدادات النسخ الاحتياطي",
                "backup_folder": "مجلد النسخة الاحتياطية:",
                "browse": "استعراض...",
                "expiration_check_days": "فحص الانتهاء اليومي (أيام):",
                "save_settings": "حفظ الاعدادات",
                "edit": "تعديل",
                "delete": "حذف",
                "record_number": "رقم السجل",
                "license_number": "رقم الترخيص",
                "driver": "السائق",
                "phone": "الهاتف",
                "vehicle_reg": "لوحة المركبة",
                "company": "الشركة",
                "carrier": "الناقل",
                "expiration": "الانتهاء",
                "all_status": "الكل",
                "active_status": "نشط",
                "expired_status": "منتهي",
                "all_carrier": "الكل",
                "public_carrier": "عام",
                "private_carrier": "خاص",
                "statistics": "الإحصائيات",
                "by_carrier_type": "التراخيص حسب نوع الناقل",
                "by_status": "التراخيص حسب الحالة",
                "by_company": "أفضل الشركات حسب عدد التراخيص",
                "expiring_soon": "التراخيص المنتهية في 30 يوم",
                "manage": "إدارة",
                "window_title_management": "إدارة البيانات",
                "manage_data": "إدارة البيانات - حذف السجلات",
                "registration_number": "رقم التسجيل:",
                "address": "العنوان:",
                "account_type": "نوع الحساب:",
                "vehicle_registration": "تسجيل المركبة:",
                "vehicle_category": "فئة المركبة:",
                "origin": "الأصل:",
                "destination": "الوجهة:",
                "checkpoints": "نقاط التفتيش (اختياري):",
                "record_number_label": "رقم السجل:",
                "driver_phone_label": "هاتف السائق:",
                "signature_date": "تاريخ التوقيع:",
                "hazmat_type": "نوع المادة (اختياري):",
                "public": "عام",
                "private": "خاص",
            },
        }

        self._build_ui()
        self._apply_language()
        self._refresh_statistics()

        # Auto-refresh statistics every 30 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_statistics)
        self.refresh_timer.start(30000)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        self.setStyleSheet(
            """
            QWidget { background: #f5f5f5; color: #1f2937; font-family: 'DejaVu Sans', sans-serif; font-size: 11pt; }
            QPushButton { background: #2563eb; color: white; border: none; border-radius: 6px; padding: 8px 12px; }
            QPushButton:hover { background: #1d4ed8; }
            QComboBox { background: white; border: 1px solid #d1d5db; border-radius: 6px; padding: 4px 8px; }
            QFrame#card { background: white; border: 1px solid #e5e7eb; border-radius: 8px; }
            """
        )

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        title_layout = QVBoxLayout()
        self.title = QLabel()
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.title.setFont(font)
        title_layout.addWidget(self.title)

        self.subtitle = QLabel()
        self.subtitle.setStyleSheet("color: #4b5563;")
        title_layout.addWidget(self.subtitle)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        self.language_label = QLabel()
        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Francais", "fr")
        self.language_combo.addItem("Arabic", "ar")
        self.language_combo.setCurrentIndex(2)  # Set Arabic as default (index 2)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        self.language_combo.setFixedWidth(140)

        header_layout.addWidget(self.language_label)
        header_layout.addWidget(self.language_combo)
        main_layout.addLayout(header_layout)

        # Navigation Buttons
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(10)

        self.add_btn = QPushButton()
        self.search_btn = QPushButton()
        self.settings_btn = QPushButton()
        self.refresh_btn = QPushButton()
        self.stats_btn = QPushButton()
        self.manage_btn = QPushButton()

        self.add_btn.clicked.connect(self._open_data_entry)
        self.search_btn.clicked.connect(self._open_search)
        self.settings_btn.clicked.connect(self._open_settings)
        self.refresh_btn.clicked.connect(self._refresh_statistics)
        self.stats_btn.clicked.connect(self._open_statistics)
        self.manage_btn.clicked.connect(self._open_management)

        for btn in (self.add_btn, self.search_btn, self.settings_btn, self.stats_btn, self.manage_btn, self.refresh_btn):
            btn.setMinimumHeight(38)
            btn.setCursor(Qt.PointingHandCursor)
            buttons_row.addWidget(btn)

        main_layout.addLayout(buttons_row)

        # Statistics Cards
        stats_layout = QGridLayout()
        stats_layout.setHorizontalSpacing(10)
        stats_layout.setVerticalSpacing(10)

        self.vehicles_lcd = self._create_lcd()
        self.drivers_lcd = self._create_lcd()
        self.active_lcd = self._create_lcd()
        self.expired_lcd = self._create_lcd()

        self.vehicle_label = QLabel()
        self.driver_label = QLabel()
        self.active_label = QLabel()
        self.expired_label = QLabel()

        stats_layout.addWidget(self._create_stat_card(self.vehicle_label, self.vehicles_lcd), 0, 0)
        stats_layout.addWidget(self._create_stat_card(self.driver_label, self.drivers_lcd), 0, 1)
        stats_layout.addWidget(self._create_stat_card(self.active_label, self.active_lcd), 1, 0)
        stats_layout.addWidget(self._create_stat_card(self.expired_label, self.expired_lcd), 1, 1)
        main_layout.addLayout(stats_layout)

        main_layout.addStretch()

    def _create_lcd(self):
        lcd = QLCDNumber()
        lcd.setDigitCount(7)
        lcd.setSegmentStyle(QLCDNumber.Flat)
        lcd.setMinimumHeight(64)
        lcd.setStyleSheet("color: #2563eb;")
        return lcd

    def _create_stat_card(self, label, lcd):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        label.setStyleSheet("font-weight: 600;")
        layout.addWidget(label)
        layout.addWidget(lcd)
        return card

    def _refresh_statistics(self):
        """Refresh database statistics."""
        try:
            stats = self.db.get_statistics()
            self.vehicles_lcd.display(stats["total_vehicles"])
            self.drivers_lcd.display(stats["total_drivers"])
            self.active_lcd.display(stats["active_licenses"])
            self.expired_lcd.display(stats["expired_licenses"])
        except Exception as e:
            print(f"Error refreshing statistics: {str(e)}")

    def _on_language_changed(self, _index):
        self.current_language = self.language_combo.currentData()
        self._apply_language()

    def _apply_language(self):
        t = self.translations[self.current_language]
        self.setWindowTitle(t["window_title"])
        self.title.setText(t["main_title"])
        self.subtitle.setText(t["subtitle"])
        self.language_label.setText(t["language"])

        self.add_btn.setText(t["add_record"])
        self.search_btn.setText(t["search_records"])
        self.settings_btn.setText(t["settings"])
        self.stats_btn.setText(t.get("statistics", "Statistics"))
        self.manage_btn.setText(t.get("manage", "Manage"))
        self.refresh_btn.setText(t["refresh"])

        self.vehicle_label.setText(t["total_vehicles"])
        self.driver_label.setText(t["total_drivers"])
        self.active_label.setText(t["active_licenses"])
        self.expired_label.setText(t["expired_licenses"])

        is_arabic = self.current_language == "ar"
        self.setLayoutDirection(Qt.RightToLeft if is_arabic else Qt.LeftToRight)

    def _open_data_entry(self):
        """Open data entry window."""
        self.data_entry_window = DataEntryWindow(self.db, language=self.current_language, translations=self.translations)
        self.data_entry_window.exec_()
        self._refresh_statistics()

    def _open_search(self):
        """Open search records window."""
        self.search_window = SearchRecordsWindow(self.db, language=self.current_language, translations=self.translations)
        self.search_window.exec_()

    def _open_settings(self):
        """Open settings window."""
        self.settings_window = SettingsWindow(self.db, language=self.current_language, translations=self.translations)
        self.settings_window.exec_()

    def _open_statistics(self):
        """Open statistics window."""
        from ui.statistics_page import StatisticsWindow
        # Use French for statistics if Arabic is selected (matplotlib doesn't support Arabic text)
        stats_language = "fr" if self.current_language == "ar" else self.current_language
        self.stats_window = StatisticsWindow(self.db, language=stats_language, translations=self.translations)
        self.stats_window.exec_()

    def _open_management(self):
        """Open management window for deleting records."""
        from ui.management import ManagementWindow
        self.management_window = ManagementWindow(self.db, language=self.current_language, translations=self.translations)
        self.management_window.exec_()
        self._refresh_statistics()

    def closeEvent(self, event):
        """Clean up on close."""
        self.refresh_timer.stop()
        self.scheduler.stop()
        event.accept()

