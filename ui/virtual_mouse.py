"""
AIRCTRL Virtual Mouse Controls Page
Configures mouse sensitivity, smoothing, acceleration, 4-corner calibration,
and tests real cursor movement and click gestures.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QFrame, QGridLayout, QGroupBox
)
from PySide6.QtCore import Qt, Signal

from core.mouse_controller import mouse_ctrl
from core.calibration import calibration_mgr
from utils.settings_manager import settings
from utils.helpers import play_feedback_sound

class VirtualMousePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        calibration_mgr.step_changed.connect(self._on_calibration_step)
        calibration_mgr.calibration_finished.connect(self._on_calibration_finished)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        # Title
        title_box = QVBoxLayout()
        t = QLabel("VIRTUAL MOUSE & TRACKING CONTROLS")
        t.setStyleSheet("color: #00f2fe; font-size: 20px; font-weight: 800; letter-spacing: 1px;")
        sub = QLabel("Configure real Windows cursor motion, anti-tremor smoothing, and interactive 4-corner calibration.")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(t)
        title_box.addWidget(sub)
        layout.addLayout(title_box)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)

        # Left Column: Configuration Sliders
        left_col = QVBoxLayout()
        left_col.setSpacing(14)

        slider_card = QFrame()
        slider_card.setProperty("class", "Card")
        slider_layout = QVBoxLayout(slider_card)
        slider_layout.setSpacing(14)

        cfg_mouse = settings.get("mouse")

        # 1. Sensitivity Slider
        self.lbl_sens = QLabel(f"Cursor Sensitivity: {cfg_mouse.get('sensitivity', 1.2):.1f}x")
        self.slider_sens = QSlider(Qt.Horizontal)
        self.slider_sens.setRange(5, 30)  # 0.5x to 3.0x
        self.slider_sens.setValue(int(cfg_mouse.get("sensitivity", 1.2) * 10))
        self.slider_sens.valueChanged.connect(self._on_sens_changed)
        slider_layout.addWidget(self.lbl_sens)
        slider_layout.addWidget(self.slider_sens)

        # 2. Smoothness Slider
        self.lbl_smooth = QLabel(f"Anti-Tremor Smoothing: {int(cfg_mouse.get('smoothness', 0.65) * 100)}%")
        self.slider_smooth = QSlider(Qt.Horizontal)
        self.slider_smooth.setRange(10, 95)
        self.slider_smooth.setValue(int(cfg_mouse.get("smoothness", 0.65) * 100))
        self.slider_smooth.valueChanged.connect(self._on_smooth_changed)
        slider_layout.addWidget(self.lbl_smooth)
        slider_layout.addWidget(self.slider_smooth)

        # 3. Acceleration Curve Slider
        self.lbl_accel = QLabel(f"Movement Acceleration: {cfg_mouse.get('acceleration', 1.0):.1f}x")
        self.slider_accel = QSlider(Qt.Horizontal)
        self.slider_accel.setRange(8, 20)  # 0.8x to 2.0x
        self.slider_accel.setValue(int(cfg_mouse.get("acceleration", 1.0) * 10))
        self.slider_accel.valueChanged.connect(self._on_accel_changed)
        slider_layout.addWidget(self.lbl_accel)
        slider_layout.addWidget(self.slider_accel)

        # 4. Click Distance Threshold
        self.lbl_pinch = QLabel(f"Pinch Click Sensitivity: {int(cfg_mouse.get('click_threshold', 0.055) * 1000)}")
        self.slider_pinch = QSlider(Qt.Horizontal)
        self.slider_pinch.setRange(20, 100)
        self.slider_pinch.setValue(int(cfg_mouse.get("click_threshold", 0.055) * 1000))
        self.slider_pinch.valueChanged.connect(self._on_pinch_changed)
        slider_layout.addWidget(self.lbl_pinch)
        slider_layout.addWidget(self.slider_pinch)

        left_col.addWidget(slider_card)
        content_layout.addLayout(left_col, stretch=1)

        # Right Column: 4-Corner Calibration & Test Pad
        right_col = QVBoxLayout()
        right_col.setSpacing(14)

        # Calibration Card
        calib_card = QFrame()
        calib_card.setProperty("class", "Card")
        calib_layout = QVBoxLayout(calib_card)
        calib_layout.setSpacing(10)

        calib_title = QLabel("4-CORNER SCREEN CALIBRATION")
        calib_title.setProperty("class", "CardTitle")
        calib_desc = QLabel("Calibrate the active tracking box so your webcam field of view perfectly maps to your screen corners.")
        calib_desc.setWordWrap(True)
        calib_desc.setStyleSheet("color: #94a3b8; font-size: 12px;")

        self.lbl_calib_status = QLabel("Status: Ready to calibrate")
        self.lbl_calib_status.setStyleSheet("color: #38bdf8; font-weight: 700;")

        btn_box = QHBoxLayout()
        self.btn_start_calib = QPushButton("Start Calibration Wizard")
        self.btn_start_calib.setProperty("class", "PrimaryBtn")
        self.btn_start_calib.clicked.connect(self._start_calibration)

        self.btn_reset_calib = QPushButton("Reset Calibration")
        self.btn_reset_calib.setProperty("class", "SecondaryBtn")
        self.btn_reset_calib.clicked.connect(self._reset_calibration)

        btn_box.addWidget(self.btn_start_calib)
        btn_box.addWidget(self.btn_reset_calib)

        calib_layout.addWidget(calib_title)
        calib_layout.addWidget(calib_desc)
        calib_layout.addWidget(self.lbl_calib_status)
        calib_layout.addLayout(btn_box)
        right_col.addWidget(calib_card)

        # Manual Mouse Test Actions Card
        test_card = QFrame()
        test_card.setProperty("class", "Card")
        test_layout = QVBoxLayout(test_card)
        test_layout.setSpacing(10)

        test_title = QLabel("MANUAL MOUSE ACTION TEST")
        test_title.setProperty("class", "CardTitle")
        test_desc = QLabel("Trigger real mouse actions directly to verify Windows integration.")
        test_desc.setStyleSheet("color: #94a3b8; font-size: 12px;")

        actions_grid = QGridLayout()
        btn_test_left = QPushButton("Trigger Left Click")
        btn_test_left.setProperty("class", "SecondaryBtn")
        btn_test_left.clicked.connect(lambda: mouse_ctrl.left_click())

        btn_test_right = QPushButton("Trigger Right Click")
        btn_test_right.setProperty("class", "SecondaryBtn")
        btn_test_right.clicked.connect(lambda: mouse_ctrl.right_click())

        btn_test_double = QPushButton("Trigger Double Click")
        btn_test_double.setProperty("class", "SecondaryBtn")
        btn_test_double.clicked.connect(lambda: mouse_ctrl.double_click())

        btn_test_drag = QPushButton("Toggle Drag State")
        btn_test_drag.setProperty("class", "SecondaryBtn")
        btn_test_drag.clicked.connect(self._toggle_drag)

        actions_grid.addWidget(btn_test_left, 0, 0)
        actions_grid.addWidget(btn_test_right, 0, 1)
        actions_grid.addWidget(btn_test_double, 1, 0)
        actions_grid.addWidget(btn_test_drag, 1, 1)

        test_layout.addWidget(test_title)
        test_layout.addWidget(test_desc)
        test_layout.addLayout(actions_grid)
        right_col.addWidget(test_card)

        content_layout.addLayout(right_col, stretch=1)
        layout.addLayout(content_layout)

    def _on_sens_changed(self, val):
        sens = val / 10.0
        self.lbl_sens.setText(f"Cursor Sensitivity: {sens:.1f}x")
        settings.set("mouse", "sensitivity", sens)

    def _on_smooth_changed(self, val):
        smooth = val / 100.0
        self.lbl_smooth.setText(f"Anti-Tremor Smoothing: {val}%")
        settings.set("mouse", "smoothness", smooth)

    def _on_accel_changed(self, val):
        accel = val / 10.0
        self.lbl_accel.setText(f"Movement Acceleration: {accel:.1f}x")
        settings.set("mouse", "acceleration", accel)

    def _on_pinch_changed(self, val):
        thresh = val / 1000.0
        self.lbl_pinch.setText(f"Pinch Click Sensitivity: {val}")
        settings.set("mouse", "click_threshold", thresh)

    def _start_calibration(self):
        play_feedback_sound("launch")
        calibration_mgr.start_calibration()
        self.btn_start_calib.setEnabled(False)

    def _reset_calibration(self):
        play_feedback_sound("click")
        default_box = [0.15, 0.15, 0.85, 0.85]
        settings.set("mouse", "active_area", default_box)
        self.lbl_calib_status.setText(f"Calibration reset to default: {default_box}")

    def _on_calibration_step(self, step, msg):
        self.lbl_calib_status.setText(f"Step {step + 1}/4: {msg}")

    def _on_calibration_finished(self, box):
        self.lbl_calib_status.setText(f"Calibration Saved! Box: {box}")
        self.btn_start_calib.setEnabled(True)

    def _toggle_drag(self):
        if mouse_ctrl.is_dragging:
            mouse_ctrl.end_drag()
        else:
            mouse_ctrl.start_drag()

