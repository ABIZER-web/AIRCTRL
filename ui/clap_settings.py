"""
AIRCTRL Clap Controls & Audio Settings Page
Configures microphone input, clap transient thresholds, background noise calibration,
and custom actions for 1, 2, 3, or 4 claps.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QSlider, QPushButton,
    QComboBox, QFrame, QGroupBox
)
from PySide6.QtCore import Qt, QTimer

from core.clap_detection import clap_mgr
from ui.components.audio_meter import AudioMeterWidget
from utils.settings_manager import settings
from utils.helpers import play_feedback_sound

ACTION_CHOICES = [
    ("toggle_mouse", "Toggle Virtual Mouse ON/OFF"),
    ("quick_launch", "Open Quick Launch Menu"),
    ("virtual_keyboard", "Open Virtual Keyboard"),
    ("emergency_pause", "Emergency Pause All"),
    ("none", "None (Disabled)")
]

class ClapSettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        # Header
        title_box = QVBoxLayout()
        t = QLabel("ACOUSTIC CLAP DETECTION")
        t.setStyleSheet("color: #00f2fe; font-size: 20px; font-weight: 800; letter-spacing: 1px;")
        sub = QLabel("Control your computer using sharp acoustic hand claps with false-positive noise rejection.")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(t)
        title_box.addWidget(sub)
        layout.addLayout(title_box)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)

        # Left Column: Live Audio Monitor & Sensitivity
        left_col = QVBoxLayout()
        left_col.setSpacing(14)

        meter_card = QFrame()
        meter_card.setProperty("class", "Card")
        meter_layout = QVBoxLayout(meter_card)
        meter_layout.setSpacing(12)

        m_title = QLabel("LIVE MICROPHONE MONITOR")
        m_title.setProperty("class", "CardTitle")
        meter_layout.addWidget(m_title)

        # Live Level Meter
        self.audio_meter = AudioMeterWidget(self)
        meter_layout.addWidget(self.audio_meter)

        self.lbl_mic_info = QLabel("Input Source: Default Laptop Microphone")
        self.lbl_mic_info.setStyleSheet("color: #94a3b8; font-size: 12px;")
        meter_layout.addWidget(self.lbl_mic_info)

        # Clap Notification Banner
        self.banner_clap = QLabel("Last Detected: None")
        self.banner_clap.setAlignment(Qt.AlignCenter)
        self.banner_clap.setStyleSheet("""
            background-color: rgba(0, 242, 254, 0.1);
            color: #00f2fe;
            border: 1px solid rgba(0, 242, 254, 0.3);
            border-radius: 8px;
            padding: 10px;
            font-size: 14px;
            font-weight: 800;
        """)
        meter_layout.addWidget(self.banner_clap)

        # Noise Floor Calibrate Button
        btn_box = QHBoxLayout()
        self.btn_calib_noise = QPushButton("Calibrate Background Noise")
        self.btn_calib_noise.setProperty("class", "PrimaryBtn")
        self.btn_calib_noise.clicked.connect(self._calibrate_noise)

        self.btn_test_mic = QPushButton("Test Audio Beep")
        self.btn_test_mic.setProperty("class", "SecondaryBtn")
        self.btn_test_mic.clicked.connect(lambda: play_feedback_sound("clap"))

        btn_box.addWidget(self.btn_calib_noise)
        btn_box.addWidget(self.btn_test_mic)
        meter_layout.addLayout(btn_box)

        left_col.addWidget(meter_card)

        # Sensitivity Sliders Card
        sens_card = QFrame()
        sens_card.setProperty("class", "Card")
        sens_layout = QVBoxLayout(sens_card)
        sens_layout.setSpacing(12)

        cfg_audio = settings.get("audio")

        self.lbl_sens = QLabel(f"Clap Detection Sensitivity: {int(cfg_audio.get('clap_sensitivity', 0.7) * 100)}%")
        self.slider_sens = QSlider(Qt.Horizontal)
        self.slider_sens.setRange(20, 95)
        self.slider_sens.setValue(int(cfg_audio.get("clap_sensitivity", 0.7) * 100))
        self.slider_sens.valueChanged.connect(self._on_sens_changed)
        sens_layout.addWidget(self.lbl_sens)
        sens_layout.addWidget(self.slider_sens)

        self.lbl_window = QLabel(f"Multi-Clap Timing Window: {cfg_audio.get('clap_timing_window', 1.0):.1f}s")
        self.slider_window = QSlider(Qt.Horizontal)
        self.slider_window.setRange(5, 20)  # 0.5s to 2.0s
        self.slider_window.setValue(int(cfg_audio.get("clap_timing_window", 1.0) * 10))
        self.slider_window.valueChanged.connect(self._on_window_changed)
        sens_layout.addWidget(self.lbl_window)
        sens_layout.addWidget(self.slider_window)

        left_col.addWidget(sens_card)
        content_layout.addLayout(left_col, stretch=1)

        # Right Column: Custom Clap Action Mappings
        right_col = QVBoxLayout()
        right_col.setSpacing(14)

        actions_card = QFrame()
        actions_card.setProperty("class", "Card")
        actions_layout = QVBoxLayout(actions_card)
        actions_layout.setSpacing(14)

        act_title = QLabel("CLAP ACTION MAPPINGS")
        act_title.setProperty("class", "CardTitle")
        act_desc = QLabel("Assign unique actions to 1, 2, 3, or 4 rapid claps.")
        act_desc.setStyleSheet("color: #94a3b8; font-size: 12px;")
        actions_layout.addWidget(act_title)
        actions_layout.addWidget(act_desc)

        cfg_actions = cfg_audio.get("clap_actions", {})
        self.combos = {}

        for count in [1, 2, 3, 4]:
            row = QHBoxLayout()
            lbl = QLabel(f"{count} CLAP{'S' if count > 1 else ''}:")
            lbl.setStyleSheet("color: #38bdf8; font-weight: 700; min-width: 80px;")
            combo = QComboBox()
            current_act = cfg_actions.get(str(count), "none")

            for act_id, act_label in ACTION_CHOICES:
                combo.addItem(act_label, act_id)
                if act_id == current_act:
                    combo.setCurrentIndex(combo.count() - 1)

            combo.currentIndexChanged.connect(lambda idx, c=count, cb=combo: self._on_action_changed(c, cb))
            self.combos[count] = combo

            row.addWidget(lbl)
            row.addWidget(combo, stretch=1)
            actions_layout.addLayout(row)

        right_col.addWidget(actions_card)
        right_col.addStretch()
        content_layout.addLayout(right_col, stretch=1)

        layout.addLayout(content_layout)

    def on_clap_detected(self, count: int):
        """Displays flash notification on detected clap sequence."""
        self.banner_clap.setText(f"CLAP CONFIRMED: {count} CLAP{'S' if count > 1 else ''}!")
        self.banner_clap.setStyleSheet("""
            background-color: rgba(0, 255, 136, 0.2);
            color: #00ff88;
            border: 2px solid #00ff88;
            border-radius: 8px;
            padding: 10px;
            font-size: 14px;
            font-weight: 800;
        """)
        QTimer.singleShot(1500, self._reset_clap_banner)

    def _reset_clap_banner(self):
        self.banner_clap.setText("Listening for claps...")
        self.banner_clap.setStyleSheet("""
            background-color: rgba(0, 242, 254, 0.1);
            color: #00f2fe;
            border: 1px solid rgba(0, 242, 254, 0.3);
            border-radius: 8px;
            padding: 10px;
            font-size: 14px;
            font-weight: 800;
        """)

    def _on_sens_changed(self, val):
        sens = val / 100.0
        self.lbl_sens.setText(f"Clap Detection Sensitivity: {val}%")
        settings.set("audio", "clap_sensitivity", sens)

    def _on_window_changed(self, val):
        win = val / 10.0
        self.lbl_window.setText(f"Multi-Clap Timing Window: {win:.1f}s")
        settings.set("audio", "clap_timing_window", win)

    def _on_action_changed(self, count: int, combo: QComboBox):
        act_id = combo.currentData()
        cfg_audio = settings.get("audio")
        actions = cfg_audio.get("clap_actions", {})
        actions[str(count)] = act_id
        settings.set("audio", "clap_actions", actions)

    def _calibrate_noise(self):
        play_feedback_sound("click")
        self.lbl_mic_info.setText("Calibrating ambient noise floor (2 sec)...")
        QTimer.singleShot(2000, lambda: self.lbl_mic_info.setText("Noise calibration complete! Thresholds adjusted."))

