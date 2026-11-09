"""
AIRCTRL Audio Settings Page
Microphone hardware device selection, acoustic signal parameters, and sound feedback settings.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSlider, QCheckBox, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal
import sounddevice as sd

from core.clap_detection import clap_mgr
from utils.settings_manager import settings
from utils.helpers import play_feedback_sound

class AudioSettingsPage(QWidget):
    audio_reconfigured = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        # Header
        title_box = QVBoxLayout()
        t = QLabel("AUDIO & MICROPHONE SETTINGS")
        t.setStyleSheet("color: #00f2fe; font-size: 20px; font-weight: 800; letter-spacing: 1px;")
        sub = QLabel("Select acoustic input hardware, transient sensitivity, and audio feedback.")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(t)
        title_box.addWidget(sub)
        layout.addLayout(title_box)

        card = QFrame()
        card.setProperty("class", "Card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)

        cfg_audio = settings.get("audio")

        # Device Combo
        dev_row = QHBoxLayout()
        lbl_dev = QLabel("Microphone Device:")
        lbl_dev.setStyleSheet("color: #38bdf8; font-weight: 700; min-width: 150px;")
        self.combo_dev = QComboBox()
        self.combo_dev.addItem("Default System Recording Device", -1)

        # Populate available mics
        for idx, name in clap_mgr.get_available_mics():
            self.combo_dev.addItem(f"{idx}: {name[:36]}", idx)

        dev_row.addWidget(lbl_dev)
        dev_row.addWidget(self.combo_dev, stretch=1)
        card_layout.addLayout(dev_row)

        # Action Cooldown Slider
        self.lbl_cooldown = QLabel(f"Post-Clap Action Cooldown: {cfg_audio.get('action_cooldown', 0.6):.1f}s")
        self.slider_cooldown = QSlider(Qt.Horizontal)
        self.slider_cooldown.setRange(3, 15)  # 0.3s to 1.5s
        self.slider_cooldown.setValue(int(cfg_audio.get("action_cooldown", 0.6) * 10))
        self.slider_cooldown.valueChanged.connect(self._on_cooldown_changed)
        card_layout.addWidget(self.lbl_cooldown)
        card_layout.addWidget(self.slider_cooldown)

        # Feedback Sounds Toggle
        self.chk_sound = QCheckBox("Enable Audible Tone Feedback on Actions")
        self.chk_sound.setChecked(settings.get("app", "sound_feedback", True))
        self.chk_sound.stateChanged.connect(self._on_sound_toggle)
        card_layout.addWidget(self.chk_sound)

        # Apply Button
        btn_apply = QPushButton("Apply Audio Settings")
        btn_apply.setProperty("class", "PrimaryBtn")
        btn_apply.clicked.connect(self._on_apply)
        card_layout.addWidget(btn_apply)

        layout.addWidget(card)
        layout.addStretch()

    def _on_cooldown_changed(self, val):
        sec = val / 10.0
        self.lbl_cooldown.setText(f"Post-Clap Action Cooldown: {sec:.1f}s")
        settings.set("audio", "action_cooldown", sec)

    def _on_sound_toggle(self, state):
        en = (state == Qt.Checked.value or state == True)
        settings.set("app", "sound_feedback", en)
        if en:
            play_feedback_sound("click")

    def _on_apply(self):
        play_feedback_sound("launch")
        dev_idx = self.combo_dev.currentData()
        settings.set("audio", "device_index", dev_idx)
        self.audio_reconfigured.emit()

