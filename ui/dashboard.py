"""
AIRCTRL Main Dashboard Page
Displays system health, live camera feed, active gesture HUD, interaction telemetry,
and master controls.
"""
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal

from ui.components.stat_card import StatCard
from ui.components.webcam_widget import WebcamPreviewWidget
from core.safety_manager import safety
from database.history_manager import history
from utils.settings_manager import settings
from utils.helpers import play_feedback_sound

class DashboardPage(QWidget):
    start_all_requested = Signal()
    stop_all_requested = Signal()
    quick_launch_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_start = time.time()
        self._setup_ui()

        # Refresh timer for metrics & session duration
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self._refresh_stats)
        self.stats_timer.start(1000)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(18)

        # Header Banner
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        welcome_lbl = QLabel("WELCOME TO AIRCTRL")
        welcome_lbl.setStyleSheet("color: #00f2fe; font-size: 22px; font-weight: 800; letter-spacing: 1px;")
        tagline_lbl = QLabel("Your Hands. Your Voice. Your Control. — Real-time Desktop AI Assistant")
        tagline_lbl.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 500;")
        title_box.addWidget(welcome_lbl)
        title_box.addWidget(tagline_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Master Start / Stop Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)
        self.btn_start_all = QPushButton("Start All Controls")
        self.btn_start_all.setProperty("class", "PrimaryBtn")
        self.btn_start_all.clicked.connect(self._on_start_all)

        self.btn_stop_all = QPushButton("Stop / Pause All")
        self.btn_stop_all.setProperty("class", "DangerBtn")
        self.btn_stop_all.clicked.connect(self._on_stop_all)

        btn_box.addWidget(self.btn_start_all)
        btn_box.addWidget(self.btn_stop_all)
        header_layout.addLayout(btn_box)
        main_layout.addLayout(header_layout)

        # Status Badges Bar
        status_bar = QFrame()
        status_bar.setProperty("class", "Card")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(16, 10, 16, 10)
        status_layout.setSpacing(14)

        self.lbl_cam_status = self._create_badge("Webcam: Initializing", "BadgeNeutral")
        self.lbl_mic_status = self._create_badge("Microphone: Active", "BadgeSuccess")
        self.lbl_mouse_status = self._create_badge("Mouse: Active", "BadgeSuccess")
        self.lbl_mode_status = self._create_badge("Mode: Hand Tracking", "BadgeSuccess")
        self.lbl_gesture_status = self._create_badge("Gesture: None", "BadgeNeutral")

        status_layout.addWidget(self.lbl_cam_status)
        status_layout.addWidget(self.lbl_mic_status)
        status_layout.addWidget(self.lbl_mouse_status)
        status_layout.addWidget(self.lbl_mode_status)
        status_layout.addWidget(self.lbl_gesture_status)
        status_layout.addStretch()
        main_layout.addWidget(status_bar)

        # Center Section: Live Preview & Quick Stats
        center_layout = QHBoxLayout()
        center_layout.setSpacing(18)

        # Webcam Preview Widget
        self.preview_widget = WebcamPreviewWidget(self)
        center_layout.addWidget(self.preview_widget, stretch=3)

        # Right Metrics Side
        right_box = QVBoxLayout()
        right_box.setSpacing(12)

        self.card_clicks = StatCard("TOTAL CLICKS", "0", "Hand pinch & double-clicks")
        self.card_gestures = StatCard("GESTURES DETECTED", "0", "Valid AI gestures mapped")
        self.card_claps = StatCard("CLAPS RECOGNIZED", "0", "Acoustic clap pulses")
        self.card_session = StatCard("SESSION TIME", "00:00:00", "Current active usage")

        right_box.addWidget(self.card_clicks)
        right_box.addWidget(self.card_gestures)
        right_box.addWidget(self.card_claps)
        right_box.addWidget(self.card_session)
        center_layout.addLayout(right_box, stretch=1)

        main_layout.addLayout(center_layout)

        # Bottom Section: Quick Launch Bar
        ql_bar = QFrame()
        ql_bar.setProperty("class", "Card")
        ql_layout = QHBoxLayout(ql_bar)
        ql_layout.setContentsMargins(16, 10, 16, 10)
        ql_layout.setSpacing(12)

        ql_title = QLabel("QUICK LAUNCH:")
        ql_title.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 12px;")
        ql_layout.addWidget(ql_title)

        # Quick default sites
        quick_sites = [
            ("YouTube", "youtube"),
            ("Google Docs", "googledocs"),
            ("ChatGPT", "chatgpt"),
            ("Claude", "claude"),
            ("GitHub", "github")
        ]
        for name, sid in quick_sites:
            btn = QPushButton(name)
            btn.setProperty("class", "SecondaryBtn")
            btn.clicked.connect(lambda ch=False, s=sid: self.quick_launch_requested.emit(s))
            ql_layout.addWidget(btn)

        ql_layout.addStretch()
        main_layout.addWidget(ql_bar)

    def _create_badge(self, text: str, css_class: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setProperty("class", css_class)
        return lbl

    def update_camera_status(self, connected: bool, message: str):
        if connected:
            self.lbl_cam_status.setText(f"Webcam: Connected")
            self.lbl_cam_status.setProperty("class", "BadgeSuccess")
        else:
            self.lbl_cam_status.setText(f"Webcam: Offline / Virtual")
            self.lbl_cam_status.setProperty("class", "BadgeNeutral")
        self.lbl_cam_status.style().polish(self.lbl_cam_status)

    def update_audio_status(self, connected: bool, message: str):
        if connected:
            self.lbl_mic_status.setText("Mic: Listening")
            self.lbl_mic_status.setProperty("class", "BadgeSuccess")
        else:
            self.lbl_mic_status.setText("Mic: Offline")
            self.lbl_mic_status.setProperty("class", "BadgeDanger")
        self.lbl_mic_status.style().polish(self.lbl_mic_status)

    def update_gesture_status(self, gesture_name: str):
        clean_name = gesture_name.replace("_", " ").title()
        self.lbl_gesture_status.setText(f"Gesture: {clean_name}")
        cls = "BadgeSuccess" if gesture_name != "NONE" else "BadgeNeutral"
        self.lbl_gesture_status.setProperty("class", cls)
        self.lbl_gesture_status.style().polish(self.lbl_gesture_status)

    def _refresh_stats(self):
        totals = history.get_totals()
        self.card_clicks.set_value(str(totals.get("clicks", 0)))
        self.card_gestures.set_value(str(totals.get("gestures", 0)))
        self.card_claps.set_value(str(totals.get("claps", 0)))

        # Update session time
        elapsed = int(time.time() - self.session_start)
        hours = elapsed // 3600
        mins = (elapsed % 3600) // 60
        secs = elapsed % 60
        self.card_session.set_value(f"{hours:02d}:{mins:02d}:{secs:02d}")

        # Update mouse status badge
        if safety.is_active:
            self.lbl_mouse_status.setText("Mouse: Active")
            self.lbl_mouse_status.setProperty("class", "BadgeSuccess")
        else:
            self.lbl_mouse_status.setText("Mouse: PAUSED")
            self.lbl_mouse_status.setProperty("class", "BadgeDanger")
        self.lbl_mouse_status.style().polish(self.lbl_mouse_status)

    def _on_start_all(self):
        play_feedback_sound("launch")
        safety.resume_from_emergency()
        safety.set_pause(False)
        self.start_all_requested.emit()

    def _on_stop_all(self):
        play_feedback_sound("emergency")
        safety.toggle_pause()
        self.stop_all_requested.emit()

