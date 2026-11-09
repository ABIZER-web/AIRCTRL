"""
AIRCTRL Gesture Settings Page
Enables/disables individual gesture detectors, configures hold duration and cooldowns.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QSlider, QPushButton, QFrame, QGridLayout
)
from PySide6.QtCore import Qt
from utils.settings_manager import settings
from utils.helpers import play_feedback_sound

GESTURE_DESCRIPTIONS = [
    ("cursor_move", "Index Finger Tracking", "Moves the real Windows cursor according to your fingertip."),
    ("left_click", "Thumb + Index Pinch", "Triggers a single left mouse click upon quick pinch."),
    ("double_click", "Double Pinch", "Two rapid pinches perform an operating system double click."),
    ("drag_and_drop", "Pinch and Hold", "Holding pinch maintains left button down to drag windows and files."),
    ("right_click", "Index + Middle Together", "Extending index and middle fingers together triggers a right click."),
    ("open_palm", "Open Palm (5 Fingers)", "Holding an open palm summons the floating HUD gesture menu."),
    ("closed_fist", "Closed Fist", "Curling all fingers temporarily stops mouse motion as a safety pause.")
]

class GestureSettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.checkboxes = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        # Header
        title_box = QVBoxLayout()
        t = QLabel("GESTURE RECOGNITION CONFIGURATION")
        t.setStyleSheet("color: #00f2fe; font-size: 20px; font-weight: 800; letter-spacing: 1px;")
        sub = QLabel("Customize hand gesture triggers, debouncing thresholds, and safety gestures.")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(t)
        title_box.addWidget(sub)
        layout.addLayout(title_box)

        content = QHBoxLayout()
        content.setSpacing(18)

        # Left Column: Enabled Gestures Matrix
        left_col = QVBoxLayout()
        left_col.setSpacing(12)

        matrix_card = QFrame()
        matrix_card.setProperty("class", "Card")
        matrix_layout = QVBoxLayout(matrix_card)
        matrix_layout.setSpacing(14)

        m_title = QLabel("ACTIVE GESTURE TRIGGERS")
        m_title.setProperty("class", "CardTitle")
        matrix_layout.addWidget(m_title)

        cfg_gestures = settings.get("gestures")

        for key, name, desc in GESTURE_DESCRIPTIONS:
            row = QHBoxLayout()
            chk = QCheckBox(name)
            chk.setChecked(cfg_gestures.get(key, True))
            chk.stateChanged.connect(lambda state, k=key: self._on_toggle_gesture(k, state))
            self.checkboxes[key] = chk

            lbl_desc = QLabel(desc)
            lbl_desc.setStyleSheet("color: #64748b; font-size: 11px;")

            box = QVBoxLayout()
            box.addWidget(chk)
            box.addWidget(lbl_desc)

            matrix_layout.addLayout(box)

        left_col.addWidget(matrix_card)
        content.addLayout(left_col, stretch=3)

        # Right Column: Hold Durations & Reset
        right_col = QVBoxLayout()
        right_col.setSpacing(14)

        timing_card = QFrame()
        timing_card.setProperty("class", "Card")
        timing_layout = QVBoxLayout(timing_card)
        timing_layout.setSpacing(14)

        t_title = QLabel("GESTURE TIMING")
        t_title.setProperty("class", "CardTitle")
        timing_layout.addWidget(t_title)

        self.lbl_menu_hold = QLabel(f"Open Palm Menu Hold: {cfg_gestures.get('menu_hold_time', 0.8):.1f}s")
        self.slider_menu_hold = QSlider(Qt.Horizontal)
        self.slider_menu_hold.setRange(4, 25)  # 0.4s to 2.5s
        self.slider_menu_hold.setValue(int(cfg_gestures.get("menu_hold_time", 0.8) * 10))
        self.slider_menu_hold.valueChanged.connect(self._on_hold_changed)
        timing_layout.addWidget(self.lbl_menu_hold)
        timing_layout.addWidget(self.slider_menu_hold)

        btn_reset = QPushButton("Reset All Gestures to Defaults")
        btn_reset.setProperty("class", "SecondaryBtn")
        btn_reset.clicked.connect(self._reset_defaults)
        timing_layout.addWidget(btn_reset)

        right_col.addWidget(timing_card)
        right_col.addStretch()
        content.addLayout(right_col, stretch=2)

        layout.addLayout(content)

    def _on_toggle_gesture(self, key: str, state):
        enabled = (state == Qt.Checked.value or state == True)
        settings.set("gestures", key, enabled)
        play_feedback_sound("click")

    def _on_hold_changed(self, val):
        sec = val / 10.0
        self.lbl_menu_hold.setText(f"Open Palm Menu Hold: {sec:.1f}s")
        settings.set("gestures", "menu_hold_time", sec)

    def _reset_defaults(self):
        play_feedback_sound("click")
        for key, _, _ in GESTURE_DESCRIPTIONS:
            settings.set("gestures", key, True)
            if key in self.checkboxes:
                self.checkboxes[key].setChecked(True)
        settings.set("gestures", "menu_hold_time", 0.8)
        self.slider_menu_hold.setValue(8)

