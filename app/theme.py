"""
AIRCTRL UI Theme & Styling
Defines modern futuristic dark and light design systems with electric blue / cyan accents,
glassmorphism card containers, rounded controls, and clean typography.
"""

DARK_THEME = """
/* Global Window & Base */
QMainWindow, QDialog, QWidget#MainContainer {
    background-color: #090e17;
    color: #e2e8f0;
    font-family: 'Segoe UI', 'SF Pro Display', -apple-system, Roboto, sans-serif;
    font-size: 13px;
}

/* Sidebar Navigation */
QFrame#Sidebar {
    background-color: #0d1524;
    border-right: 1px solid rgba(0, 242, 254, 0.15);
    min-width: 230px;
    max-width: 230px;
}

QLabel#AppTitle {
    color: #00f2fe;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 2px;
}

QLabel#AppTagline {
    color: #64748b;
    font-size: 11px;
    font-weight: 500;
}

/* Navigation Buttons */
QPushButton.NavBtn {
    background-color: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    font-size: 13px;
    font-weight: 600;
}

QPushButton.NavBtn:hover {
    background-color: rgba(0, 242, 254, 0.08);
    color: #38bdf8;
}

QPushButton.NavBtn:checked {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 242, 254, 0.25), stop:1 rgba(79, 172, 254, 0.1));
    color: #00f2fe;
    border-left: 3px solid #00f2fe;
}

/* Modern Card Containers */
QFrame.Card {
    background-color: #121c2d;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    padding: 16px;
}

QFrame.Card:hover {
    border: 1px solid rgba(0, 242, 254, 0.3);
}

QLabel.CardTitle {
    color: #38bdf8;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}

QLabel.CardValue {
    color: #f8fafc;
    font-size: 26px;
    font-weight: 800;
}

QLabel.CardSubtitle {
    color: #64748b;
    font-size: 11px;
}

/* Action Buttons */
QPushButton.PrimaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00c6ff, stop:1 #0072ff);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 700;
    font-size: 13px;
}

QPushButton.PrimaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1ad0ff, stop:1 #1a82ff);
}

QPushButton.PrimaryBtn:pressed {
    background: #0056c7;
}

QPushButton.DangerBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff3366, stop:1 #cb1143);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 700;
    font-size: 13px;
}

QPushButton.DangerBtn:hover {
    background: #ff4d7a;
}

QPushButton.SecondaryBtn {
    background-color: rgba(255, 255, 255, 0.06);
    color: #cbd5e1;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton.SecondaryBtn:hover {
    background-color: rgba(255, 255, 255, 0.12);
    color: #ffffff;
    border-color: rgba(0, 242, 254, 0.4);
}

/* Status Badges */
QLabel.BadgeSuccess {
    background-color: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
}

QLabel.BadgeDanger {
    background-color: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
}

QLabel.BadgeNeutral {
    background-color: rgba(148, 163, 184, 0.15);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.3);
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
}

/* Form Controls */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #0b121e;
    color: #f1f5f9;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 7px;
    padding: 7px 10px;
    font-size: 13px;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #00f2fe;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

/* Slider Controls */
QSlider::groove:horizontal {
    height: 6px;
    background: #1e293b;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00c6ff, stop:1 #0072ff);
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #00f2fe;
    border: 2px solid #ffffff;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}

/* Checkbox */
QCheckBox {
    color: #cbd5e1;
    font-weight: 500;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    background: #0b121e;
}

QCheckBox::indicator:checked {
    background: #00f2fe;
    border-color: #00f2fe;
}

/* ScrollBars */
QScrollBar:vertical {
    background: #090e17;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #1e293b;
    min-height: 25px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #00f2fe;
}

/* Table */
QTableWidget {
    background-color: #121c2d;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    gridline-color: rgba(255, 255, 255, 0.05);
}

QHeaderView::section {
    background-color: #0d1524;
    color: #38bdf8;
    font-weight: 700;
    border: none;
    padding: 8px;
}
"""

LIGHT_THEME = """
QMainWindow, QDialog, QWidget#MainContainer {
    background-color: #f1f5f9;
    color: #1e293b;
    font-family: 'Segoe UI', Roboto, sans-serif;
    font-size: 13px;
}

QFrame#Sidebar {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
    min-width: 230px;
    max-width: 230px;
}

QLabel#AppTitle {
    color: #0284c7;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 2px;
}

QLabel#AppTagline {
    color: #64748b;
    font-size: 11px;
}

QPushButton.NavBtn {
    background-color: transparent;
    color: #475569;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
}

QPushButton.NavBtn:hover {
    background-color: #e0f2fe;
    color: #0284c7;
}

QPushButton.NavBtn:checked {
    background-color: #bae6fd;
    color: #0369a1;
    border-left: 3px solid #0284c7;
}

QFrame.Card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px;
}

QLabel.CardTitle {
    color: #0284c7;
    font-size: 14px;
    font-weight: 700;
}

QLabel.CardValue {
    color: #0f172a;
    font-size: 26px;
    font-weight: 800;
}

QPushButton.PrimaryBtn {
    background: #0284c7;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 700;
}

QPushButton.DangerBtn {
    background: #ef4444;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 700;
}

QPushButton.SecondaryBtn {
    background-color: #e2e8f0;
    color: #334155;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

QLineEdit, QComboBox {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    padding: 7px 10px;
}
"""

def get_theme_stylesheet(theme_name: str = "dark") -> str:
    return DARK_THEME if theme_name.lower() == "dark" else LIGHT_THEME

