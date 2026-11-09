"""
AIRCTRL Camera & System Settings Page
Selects active video hardware device, resolution, target framerate,
MediaPipe confidence thresholds, mirror settings, and Windows startup preferences.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSlider, QCheckBox,
    QPushButton, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from core.camera_manager import camera_mgr, CameraManager
from utils.settings_manager import settings
from utils.helpers import play_feedback_sound
from utils.autostart import is_windows_autostart_active, set_windows_autostart

class CameraSettingsPage(QWidget):
    camera_reconfigured = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(18)

        # Header
        title_box = QVBoxLayout()
        t = QLabel("CAMERA & SYSTEM PREFERENCES")
        t.setStyleSheet("color: #00f2fe; font-size: 20px; font-weight: 800; letter-spacing: 1px;")
        sub = QLabel("Select optical webcam hardware, AI tracking confidence, and configure automatic Windows startup.")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(t)
        title_box.addWidget(sub)
        main_layout.addLayout(title_box)

        # Scroll Area for comfortable layout on all screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # CARD 1: Camera Hardware & Video Stream
        cam_card = QFrame()
        cam_card.setProperty("class", "Card")
        cam_card_layout = QVBoxLayout(cam_card)
        cam_card_layout.setSpacing(14)

        cam_title = QLabel("CAMERA & VISION STREAM")
        cam_title.setProperty("class", "CardTitle")
        cam_card_layout.addWidget(cam_title)

        cfg_cam = settings.get("camera")

        # Camera Device
        dev_row = QHBoxLayout()
        lbl_dev = QLabel("Active Camera Device:")
        lbl_dev.setStyleSheet("color: #38bdf8; font-weight: 700; min-width: 150px;")
        self.combo_device = QComboBox()
        self.combo_device.addItem("Camera Index 0 (Default)", 0)
        self.combo_device.addItem("Camera Index 1 (External / Secondary)", 1)
        self.combo_device.addItem("Camera Index 2", 2)
        dev_row.addWidget(lbl_dev)
        dev_row.addWidget(self.combo_device, stretch=1)
        cam_card_layout.addLayout(dev_row)

        # Resolution
        res_row = QHBoxLayout()
        lbl_res = QLabel("Capture Resolution:")
        lbl_res.setStyleSheet("color: #38bdf8; font-weight: 700; min-width: 150px;")
        self.combo_res = QComboBox()
        self.combo_res.addItem("640 x 480 (Recommended - High Speed)", (640, 480))
        self.combo_res.addItem("1280 x 720 (HD - High Accuracy)", (1280, 720))
        self.combo_res.addItem("1920 x 1080 (Full HD)", (1920, 1080))
        res_row.addWidget(lbl_res)
        res_row.addWidget(self.combo_res, stretch=1)
        cam_card_layout.addLayout(res_row)

        # Target FPS
        fps_row = QHBoxLayout()
        lbl_fps = QLabel("Target Framerate:")
        lbl_fps.setStyleSheet("color: #38bdf8; font-weight: 700; min-width: 150px;")
        self.combo_fps = QComboBox()
        self.combo_fps.addItem("30 FPS (Standard)", 30)
        self.combo_fps.addItem("60 FPS (Ultra Smooth)", 60)
        self.combo_fps.addItem("20 FPS (Low CPU Usage)", 20)
        fps_row.addWidget(lbl_fps)
        fps_row.addWidget(self.combo_fps, stretch=1)
        cam_card_layout.addLayout(fps_row)

        # Confidence Sliders
        self.lbl_det = QLabel(f"Min Hand Detection Confidence: {int(cfg_cam.get('detection_confidence', 0.5) * 100)}%")
        self.slider_det = QSlider(Qt.Horizontal)
        self.slider_det.setRange(20, 90)
        self.slider_det.setValue(int(cfg_cam.get("detection_confidence", 0.5) * 100))
        self.slider_det.valueChanged.connect(self._on_det_changed)
        cam_card_layout.addWidget(self.lbl_det)
        cam_card_layout.addWidget(self.slider_det)

        self.lbl_track = QLabel(f"Min Hand Tracking Confidence: {int(cfg_cam.get('tracking_confidence', 0.5) * 100)}%")
        self.slider_track = QSlider(Qt.Horizontal)
        self.slider_track.setRange(20, 90)
        self.slider_track.setValue(int(cfg_cam.get("tracking_confidence", 0.5) * 100))
        self.slider_track.valueChanged.connect(self._on_track_changed)
        cam_card_layout.addWidget(self.lbl_track)
        cam_card_layout.addWidget(self.slider_track)

        # Mirror Preview
        self.chk_mirror = QCheckBox("Mirror Preview (Natural selfie mode)")
        self.chk_mirror.setChecked(cfg_cam.get("mirror", True))
        self.chk_mirror.stateChanged.connect(self._on_mirror_toggle)
        cam_card_layout.addWidget(self.chk_mirror)

        # Apply Button
        btn_apply = QPushButton("Apply & Restart Camera Stream")
        btn_apply.setProperty("class", "PrimaryBtn")
        btn_apply.clicked.connect(self._on_apply)
        cam_card_layout.addWidget(btn_apply)

        layout.addWidget(cam_card)

        # CARD 2: Windows Startup & Application Preferences
        startup_card = QFrame()
        startup_card.setProperty("class", "Card")
        startup_layout = QVBoxLayout(startup_card)
        startup_layout.setSpacing(14)

        startup_title = QLabel("WINDOWS STARTUP & SYSTEM BEHAVIOR")
        startup_title.setProperty("class", "CardTitle")
        startup_layout.addWidget(startup_title)

        # 1. Launch with Windows Checkbox
        self.chk_autostart = QCheckBox("Launch AIRCTRL automatically when Windows starts")
        self.chk_autostart.setStyleSheet("font-size: 14px; font-weight: 700; color: #f8fafc;")
        is_active = is_windows_autostart_active()
        self.chk_autostart.setChecked(is_active)
        self.chk_autostart.stateChanged.connect(self._on_autostart_toggle)

        autostart_desc = QLabel("Automatically registers AIRCTRL with Windows so your hands-free desktop assistant is ready immediately upon logging into your PC.")
        autostart_desc.setWordWrap(True)
        autostart_desc.setStyleSheet("color: #94a3b8; font-size: 12px; margin-left: 26px;")

        startup_layout.addWidget(self.chk_autostart)
        startup_layout.addWidget(autostart_desc)

        # 2. Start Minimized Checkbox
        self.chk_minimized = QCheckBox("Start Minimized (Background Assistant Mode)")
        self.chk_minimized.setStyleSheet("font-size: 13px; font-weight: 600; color: #e2e8f0; margin-top: 6px;")
        self.chk_minimized.setChecked(settings.get("app", "start_minimized", False))
        self.chk_minimized.stateChanged.connect(self._on_minimized_toggle)

        minimized_desc = QLabel("Launches AIRCTRL minimized to keep your desktop workspace clear.")
        minimized_desc.setWordWrap(True)
        minimized_desc.setStyleSheet("color: #94a3b8; font-size: 12px; margin-left: 26px;")

        startup_layout.addWidget(self.chk_minimized)
        startup_layout.addWidget(minimized_desc)

        # Status Banner
        self.lbl_autostart_status = QLabel(
            "Status: Automatic Windows startup is ACTIVE" if is_active else "Status: Automatic Windows startup is DISABLED"
        )
        self.lbl_autostart_status.setStyleSheet(
            "color: #10b981; font-weight: 700; font-size: 12px; margin-top: 4px;" if is_active
            else "color: #94a3b8; font-weight: 600; font-size: 12px; margin-top: 4px;"
        )
        startup_layout.addWidget(self.lbl_autostart_status)

        layout.addWidget(startup_card)
        layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _on_det_changed(self, val):
        c = val / 100.0
        self.lbl_det.setText(f"Min Hand Detection Confidence: {val}%")
        settings.set("camera", "detection_confidence", c)

    def _on_track_changed(self, val):
        c = val / 100.0
        self.lbl_track.setText(f"Min Hand Tracking Confidence: {val}%")
        settings.set("camera", "tracking_confidence", c)

    def _on_mirror_toggle(self, state):
        m = (state == Qt.Checked.value or state == True)
        settings.set("camera", "mirror", m)

    def _on_apply(self):
        play_feedback_sound("launch")
        dev = self.combo_device.currentData()
        w, h = self.combo_res.currentData()
        fps = self.combo_fps.currentData()
        mirror = self.chk_mirror.isChecked()

        settings.set("camera", "device_index", dev)
        settings.set("camera", "width", w)
        settings.set("camera", "height", h)
        settings.set("camera", "fps", fps)
        settings.set("camera", "mirror", mirror)

        self.camera_reconfigured.emit()

    def _on_autostart_toggle(self, state):
        enable = (state == Qt.Checked.value or state == True)
        play_feedback_sound("click")
        success, msg = set_windows_autostart(enable)
        if enable:
            self.lbl_autostart_status.setText("Status: Automatic Windows startup is ACTIVE")
            self.lbl_autostart_status.setStyleSheet("color: #10b981; font-weight: 700; font-size: 12px; margin-top: 4px;")
        else:
            self.lbl_autostart_status.setText("Status: Automatic Windows startup is DISABLED")
            self.lbl_autostart_status.setStyleSheet("color: #94a3b8; font-weight: 600; font-size: 12px; margin-top: 4px;")

    def _on_minimized_toggle(self, state):
        minimized = (state == Qt.Checked.value or state == True)
        play_feedback_sound("click")
        settings.set("app", "start_minimized", minimized)
