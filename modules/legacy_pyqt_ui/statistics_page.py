from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QWidget,
    QTabWidget,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class StatisticsWindow(QDialog):
    """Statistics window with charts and graphs."""

    def __init__(self, database, language="en", translations=None):
        super().__init__()
        self.db = database
        self.current_language = language
        self.translations = translations or {}
        self.setWindowTitle("Statistics & Reports")
        self.resize(1400, 900)
        # Enable minimize and maximize buttons
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self._build_ui()
        self._apply_language()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        self.title = QLabel("Statistics & Reports")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title.setFont(title_font)
        layout.addWidget(self.title)

        # Create tab widget
        self.tabs = QTabWidget()
        
        # Tab 1: License Statistics
        self.license_stats_tab = self._create_license_statistics_tab()
        self.tabs.addTab(self.license_stats_tab, "License Statistics")
        
        # Tab 2: Transport Statistics
        self.transport_stats_tab = self._create_transport_statistics_tab()
        self.tabs.addTab(self.transport_stats_tab, "Transport Statistics")
        
        layout.addWidget(self.tabs)

    def _create_license_statistics_tab(self):
        """Create tab for license statistics."""
        # Create scroll area for charts
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea { 
                border: 1px solid #d1d5db;
                border-radius: 4px;
            }
            QScrollBar:vertical {
                border: none;
                background: #f3f4f6;
                width: 12px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #9ca3af;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6b7280;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(20)
        scroll_layout.setContentsMargins(10, 10, 10, 10)

        # Create charts container
        charts_container = QWidget()
        charts_layout = QVBoxLayout(charts_container)
        charts_layout.setSpacing(20)

        # Status and Carrier charts side by side
        top_charts_layout = QHBoxLayout()
        top_charts_layout.setSpacing(15)
        
        # Status pie chart
        self.status_canvas = self._create_status_chart()
        self.status_canvas.setMinimumHeight(350)
        top_charts_layout.addWidget(self.status_canvas)

        # Carrier type pie chart
        self.carrier_canvas = self._create_carrier_chart()
        self.carrier_canvas.setMinimumHeight(350)
        top_charts_layout.addWidget(self.carrier_canvas)

        charts_layout.addLayout(top_charts_layout)

        # Companies bar chart (full width)
        self.company_canvas = self._create_company_chart()
        self.company_canvas.setMinimumHeight(400)
        charts_layout.addWidget(self.company_canvas)

        # Info section
        info_layout = QHBoxLayout()
        self.expiring_label = QLabel()
        self.expiring_label.setStyleSheet("font-weight: 600; color: #d97706; font-size: 12pt;")
        info_layout.addWidget(self.expiring_label)
        info_layout.addStretch()
        charts_layout.addLayout(info_layout)

        charts_layout.addStretch()
        scroll_layout.addWidget(charts_container)
        
        scroll.setWidget(scroll_widget)
        return scroll

    def _create_transport_statistics_tab(self):
        """Create tab for transport statistics."""
        # Create scroll area for transport charts
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea { 
                border: 1px solid #d1d5db;
                border-radius: 4px;
            }
            QScrollBar:vertical {
                border: none;
                background: #f3f4f6;
                width: 12px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #9ca3af;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6b7280;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(20)
        scroll_layout.setContentsMargins(10, 10, 10, 10)

        # Create transport charts container
        transport_container = QWidget()
        transport_layout = QVBoxLayout(transport_container)
        transport_layout.setSpacing(20)

        # Daily transports chart
        daily_label = QLabel("Daily Transports (Last 30 Days)")
        daily_label_font = QFont()
        daily_label_font.setBold(True)
        daily_label_font.setPointSize(11)
        daily_label.setFont(daily_label_font)
        transport_layout.addWidget(daily_label)
        
        self.daily_canvas = self._create_daily_transports_chart()
        self.daily_canvas.setMinimumHeight(350)
        transport_layout.addWidget(self.daily_canvas)

        # Weekly transports chart
        weekly_label = QLabel("Weekly Transports (Last 12 Weeks)")
        weekly_label_font = QFont()
        weekly_label_font.setBold(True)
        weekly_label_font.setPointSize(11)
        weekly_label.setFont(weekly_label_font)
        transport_layout.addWidget(weekly_label)
        
        self.weekly_canvas = self._create_weekly_transports_chart()
        self.weekly_canvas.setMinimumHeight(350)
        transport_layout.addWidget(self.weekly_canvas)

        # Monthly transports chart
        monthly_label = QLabel("Monthly Transports (Last 12 Months)")
        monthly_label_font = QFont()
        monthly_label_font.setBold(True)
        monthly_label_font.setPointSize(11)
        monthly_label.setFont(monthly_label_font)
        transport_layout.addWidget(monthly_label)
        
        self.monthly_canvas = self._create_monthly_transports_chart()
        self.monthly_canvas.setMinimumHeight(350)
        transport_layout.addWidget(self.monthly_canvas)

        transport_layout.addStretch()
        scroll_layout.addWidget(transport_container)
        
        scroll.setWidget(scroll_widget)
        return scroll

    def _create_figure(self):
        """Create a matplotlib figure."""
        fig = Figure(figsize=(5, 4), dpi=100)
        return fig

    def _create_status_chart(self):
        """Create pie chart for licenses by status."""
        fig = self._create_figure()
        ax = fig.add_subplot(111)

        try:
            stats = self.db.get_advanced_statistics()
            by_status = stats.get("by_status", {})

            if by_status:
                labels = list(by_status.keys())
                sizes = list(by_status.values())
                colors = ["#10b981", "#ef4444"]  # Green for active, red for expired
                
                ax.pie(sizes, labels=labels, autopct="%1.1f%%", colors=colors[:len(sizes)], startangle=90)
                ax.set_title(self.translations.get(self.current_language, {}).get("by_status", "Licenses by Status"))
            else:
                ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        except Exception as e:
            ax.text(0.5, 0.5, f"Error: {str(e)}", ha="center", va="center")

        canvas = FigureCanvas(fig)
        return canvas

    def _create_carrier_chart(self):
        """Create pie chart for licenses by carrier type."""
        fig = self._create_figure()
        ax = fig.add_subplot(111)

        try:
            stats = self.db.get_advanced_statistics()
            by_carrier = stats.get("by_carrier", {})

            if by_carrier:
                labels = list(by_carrier.keys())
                sizes = list(by_carrier.values())
                colors = ["#3b82f6", "#8b5cf6", "#ec4899"]  # Blue, purple, pink
                
                ax.pie(sizes, labels=labels, autopct="%1.1f%%", colors=colors[:len(sizes)], startangle=90)
                ax.set_title(self.translations.get(self.current_language, {}).get("by_carrier_type", "Licenses by Carrier Type"))
            else:
                ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        except Exception as e:
            ax.text(0.5, 0.5, f"Error: {str(e)}", ha="center", va="center")

        canvas = FigureCanvas(fig)
        return canvas

    def _create_company_chart(self):
        """Create bar chart for top companies."""
        fig = Figure(figsize=(12, 4), dpi=100)
        ax = fig.add_subplot(111)

        try:
            stats = self.db.get_advanced_statistics()
            by_company = stats.get("by_company", {})

            if by_company:
                companies = list(by_company.keys())
                counts = list(by_company.values())
                
                ax.bar(companies, counts, color="#2563eb")
                ax.set_xlabel(self.translations.get(self.current_language, {}).get("company", "Company"))
                ax.set_ylabel(self.translations.get(self.current_language, {}).get("license_number", "License Count"))
                ax.set_title(self.translations.get(self.current_language, {}).get("by_company", "Top Companies by License Count"))
                ax.tick_params(axis="x", rotation=45)
                fig.tight_layout()
            else:
                ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        except Exception as e:
            ax.text(0.5, 0.5, f"Error: {str(e)}", ha="center", va="center")

        canvas = FigureCanvas(fig)
        return canvas

    def _create_daily_transports_chart(self):
        """Create line chart for daily transports."""
        fig = Figure(figsize=(12, 4), dpi=100)
        ax = fig.add_subplot(111)

        try:
            daily_data = self.db.get_daily_transports(days=30)
            
            if daily_data:
                dates = [d["date"] for d in daily_data]
                counts = [d["count"] for d in daily_data]
                
                ax.plot(dates, counts, marker='o', color="#10b981", linewidth=2, markersize=6)
                ax.fill_between(range(len(dates)), counts, alpha=0.3, color="#10b981")
                ax.set_xlabel("Date")
                ax.set_ylabel("Transport Count")
                ax.set_title("Daily Transports (Last 30 Days)")
                ax.tick_params(axis="x", rotation=45)
                fig.tight_layout()
            else:
                ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        except Exception as e:
            ax.text(0.5, 0.5, f"Error: {str(e)}", ha="center", va="center")

        canvas = FigureCanvas(fig)
        return canvas

    def _create_weekly_transports_chart(self):
        """Create bar chart for weekly transports."""
        fig = Figure(figsize=(12, 4), dpi=100)
        ax = fig.add_subplot(111)

        try:
            weekly_data = self.db.get_weekly_transports(weeks=12)
            
            if weekly_data:
                weeks = [d["week"] for d in weekly_data]
                counts = [d["count"] for d in weekly_data]
                
                ax.bar(weeks, counts, color="#3b82f6")
                ax.set_xlabel("Week")
                ax.set_ylabel("Transport Count")
                ax.set_title("Weekly Transports (Last 12 Weeks)")
                ax.tick_params(axis="x", rotation=45)
                fig.tight_layout()
            else:
                ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        except Exception as e:
            ax.text(0.5, 0.5, f"Error: {str(e)}", ha="center", va="center")

        canvas = FigureCanvas(fig)
        return canvas

    def _create_monthly_transports_chart(self):
        """Create bar chart for monthly transports."""
        fig = Figure(figsize=(12, 4), dpi=100)
        ax = fig.add_subplot(111)

        try:
            monthly_data = self.db.get_monthly_transports(months=12)
            
            if monthly_data:
                months = [d["month"] for d in monthly_data]
                counts = [d["count"] for d in monthly_data]
                
                ax.bar(months, counts, color="#8b5cf6")
                ax.set_xlabel("Month")
                ax.set_ylabel("Transport Count")
                ax.set_title("Monthly Transports (Last 12 Months)")
                ax.tick_params(axis="x", rotation=45)
                fig.tight_layout()
            else:
                ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        except Exception as e:
            ax.text(0.5, 0.5, f"Error: {str(e)}", ha="center", va="center")

        canvas = FigureCanvas(fig)
        return canvas

    def _apply_language(self):
        """Apply language translations."""
        t = self.translations.get(self.current_language, {})
        self.setWindowTitle(t.get("window_title_statistics", "Statistics & Reports"))
        self.title.setText(t.get("statistics", "Statistics & Reports"))
        
        # Update tab names
        self.tabs.setTabText(0, "License Statistics")
        self.tabs.setTabText(1, "Transport Statistics")

        try:
            stats = self.db.get_advanced_statistics()
            expiring = stats.get("expiring_soon", 0)
            self.expiring_label.setText(t.get("expiring_soon", f"Licenses Expiring in 30 Days: {expiring}"))
        except:
            self.expiring_label.setText(t.get("expiring_soon", "Licenses Expiring in 30 Days: N/A"))

        is_arabic = self.current_language == "ar"
        self.setLayoutDirection(Qt.RightToLeft if is_arabic else Qt.LeftToRight)
