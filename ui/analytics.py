"""
AIRCTRL Analytics & Activity History Page
Visualizes interaction metrics, daily usage bar charts, top websites, and recent activity logs.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QFont, QLinearGradient

from ui.components.stat_card import StatCard
from database.history_manager import history
from utils.helpers import play_feedback_sound

class DailyTrendChartWidget(QWidget):
    """Custom painted high-DPI bar chart showing daily interactions."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(160)
        self.trend_data = []

    def set_data(self, data):
        self.trend_data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Background
        painter.setBrush(QColor(13, 21, 36))
        painter.setPen(QColor(255, 255, 255, 15))
        painter.drawRoundedRect(0, 0, w, h, 8, 8)

        if not self.trend_data:
            painter.setPen(QColor(100, 116, 139))
            painter.setFont(QFont("Segoe UI", 11))
            painter.drawText(self.rect(), Qt.AlignCenter, "No daily activity recorded yet today.")
            return

        # Calculate max interaction sum
        max_val = max([
            d.get("clicks", 0) + d.get("gestures", 0) + d.get("claps", 0)
            for d in self.trend_data
        ] or [10])
        max_val = max(10, max_val)

        bar_count = len(self.trend_data)
        margin = 35
        chart_w = w - margin * 2
        chart_h = h - 45
        bar_w = min(40, chart_w // max(1, bar_count * 2))

        for idx, d in enumerate(self.trend_data):
            val = d.get("clicks", 0) + d.get("gestures", 0) + d.get("claps", 0)
            bar_h = int((val / max_val) * chart_h)
            x = margin + idx * (chart_w // max(1, bar_count)) + 15
            y = h - 25 - bar_h

            # Bar Gradient
            grad = QLinearGradient(x, y, x, h - 25)
            grad.setColorAt(0.0, QColor(0, 242, 254))
            grad.setColorAt(1.0, QColor(0, 114, 255, 160))

            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x, y, bar_w, bar_h, 4, 4)

            # Label date
            painter.setPen(QColor(148, 163, 184))
            painter.setFont(QFont("Segoe UI", 9))
            date_short = d.get("date", "")[-5:]
            painter.drawText(x - 5, h - 8, date_short)

            # Value label
            if val > 0:
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(x, y - 4, str(val))


class AnalyticsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Header
        top_box = QHBoxLayout()
        header = QVBoxLayout()
        t = QLabel("ACTIVITY HISTORY & ANALYTICS")
        t.setStyleSheet("color: #00f2fe; font-size: 20px; font-weight: 800; letter-spacing: 1px;")
        sub = QLabel("Comprehensive metrics and audit logs stored locally in SQLite database.")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        header.addWidget(t)
        header.addWidget(sub)
        top_box.addLayout(header)
        top_box.addStretch()

        btn_clear = QPushButton("Clear Activity History")
        btn_clear.setProperty("class", "DangerBtn")
        btn_clear.clicked.connect(self._clear_history)
        top_box.addWidget(btn_clear)

        layout.addLayout(top_box)

        # Metrics Row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.card_clicks = StatCard("TOTAL CLICKS", "0")
        self.card_gestures = StatCard("TOTAL GESTURES", "0")
        self.card_claps = StatCard("TOTAL CLAPS", "0")
        self.card_keys = StatCard("KEYBOARD ACTIONS", "0")
        self.card_sites = StatCard("WEBSITES LAUNCHED", "0")

        cards_layout.addWidget(self.card_clicks)
        cards_layout.addWidget(self.card_gestures)
        cards_layout.addWidget(self.card_claps)
        cards_layout.addWidget(self.card_keys)
        cards_layout.addWidget(self.card_sites)
        layout.addLayout(cards_layout)

        # Daily Trend Chart Card
        chart_card = QFrame()
        chart_card.setProperty("class", "Card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setSpacing(8)

        chart_title = QLabel("DAILY USAGE TREND (LAST 7 DAYS)")
        chart_title.setProperty("class", "CardTitle")
        chart_layout.addWidget(chart_title)

        self.trend_chart = DailyTrendChartWidget(self)
        chart_layout.addWidget(self.trend_chart)
        layout.addWidget(chart_card)

        # Recent Activity Table Card
        table_card = QFrame()
        table_card.setProperty("class", "Card")
        table_layout = QVBoxLayout(table_card)
        table_layout.setSpacing(8)

        tbl_title = QLabel("RECENT INTERACTION AUDIT LOG")
        tbl_title.setProperty("class", "CardTitle")
        table_layout.addWidget(tbl_title)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Event Type", "Details", "Count"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setMinimumHeight(180)
        table_layout.addWidget(self.table)

        layout.addWidget(table_card)

    def refresh_data(self):
        totals = history.get_totals()
        self.card_clicks.set_value(str(totals.get("clicks", 0)))
        self.card_gestures.set_value(str(totals.get("gestures", 0)))
        self.card_claps.set_value(str(totals.get("claps", 0)))
        self.card_keys.set_value(str(totals.get("keystrokes", 0)))
        self.card_sites.set_value(str(totals.get("websites_opened", 0)))

        # Update Chart
        trend = history.get_daily_trend(days=7)
        self.trend_chart.set_data(trend)

        # Update Table
        activities = history.get_recent_activities(limit=30)
        self.table.setRowCount(len(activities))
        for row_idx, act in enumerate(activities):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(act.get("timestamp", ""))))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(act.get("event_type", "")).upper()))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(act.get("details", ""))))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(act.get("count", 1))))

    def _clear_history(self):
        reply = QMessageBox.question(
            self, "Clear History", "Are you sure you want to clear all activity and usage statistics?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            play_feedback_sound("click")
            history.clear_history()
            self.refresh_data()

