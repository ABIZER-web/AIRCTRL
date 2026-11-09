"""
AIRCTRL Sidebar Navigation Component
Hosts app title, 10 primary module navigation buttons, and an emergency pause button.
"""
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton, QButtonGroup, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from utils.helpers import play_feedback_sound

NAV_ITEMS = [
    ("Dashboard", 0, "🏠"),
    ("Virtual Mouse", 1, "🖱️"),
    ("Virtual Keyboard", 2, "⌨️"),
    ("Clap Controls", 3, "👏"),
    ("Quick Launch", 4, "🚀"),
    ("Gesture Settings", 5, "🖐️"),
    ("Camera Settings", 6, "📷"),
    ("Audio Settings", 7, "🎙️"),
    ("Activity History", 8, "📊"),
    ("About AIRCTRL", 9, "ℹ️")
]

class SidebarNav(QFrame):
    page_changed = Signal(int)
    emergency_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        self.buttons = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 20, 14, 20)
        layout.setSpacing(6)

        # App Logo & Branding
        brand_box = QVBoxLayout()
        brand_box.setSpacing(2)
        title_lbl = QLabel("AIRCTRL")
        title_lbl.setObjectName("AppTitle")
        tagline_lbl = QLabel("AI Desktop Assistant")
        tagline_lbl.setObjectName("AppTagline")
        brand_box.addWidget(title_lbl)
        brand_box.addWidget(tagline_lbl)
        layout.addLayout(brand_box)

        layout.addSpacing(15)

        # 10 Navigation Buttons
        for name, page_idx, icon in NAV_ITEMS:
            btn = QPushButton(f"  {icon}  {name}")
            btn.setProperty("class", "NavBtn")
            btn.setCheckable(True)
            self.btn_group.addButton(btn, page_idx)
            self.buttons[page_idx] = btn
            btn.clicked.connect(lambda ch=False, idx=page_idx: self._on_btn_clicked(idx))
            layout.addWidget(btn)

        # Select Dashboard by default
        self.buttons[0].setChecked(True)

        layout.addStretch()

        # Emergency Stop Button at bottom of sidebar
        self.btn_emergency = QPushButton("🛑  EMERGENCY STOP")
        self.btn_emergency.setProperty("class", "DangerBtn")
        self.btn_emergency.clicked.connect(self._on_emergency_clicked)
        layout.addWidget(self.btn_emergency)

    def _on_btn_clicked(self, page_idx: int):
        play_feedback_sound("click")
        self.page_changed.emit(page_idx)

    def select_page(self, page_idx: int):
        if page_idx in self.buttons:
            self.buttons[page_idx].setChecked(True)
            self.page_changed.emit(page_idx)

    def _on_emergency_clicked(self):
        play_feedback_sound("emergency")
        self.emergency_clicked.emit()

