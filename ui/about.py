"""
AIRCTRL About Page
Information regarding the AIRCTRL system architecture, libraries, gestures, and shortcut references.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
from PySide6.QtCore import Qt

class AboutPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(18)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setSpacing(18)

        # App Banner Card
        banner_card = QFrame()
        banner_card.setProperty("class", "Card")
        b_layout = QVBoxLayout(banner_card)
        b_layout.setSpacing(8)

        app_title = QLabel("AIRCTRL – AI-POWERED DESKTOP ASSISTANT")
        app_title.setStyleSheet("color: #00f2fe; font-size: 22px; font-weight: 800; letter-spacing: 1.5px;")
        tagline = QLabel("Tagline: Your Hands. Your Voice. Your Control.")
        tagline.setStyleSheet("color: #38bdf8; font-size: 14px; font-weight: 600;")
        version = QLabel("Version: 1.0.0 Production Release  |  Architecture: 100% Local Inference (No Cloud)")
        version.setStyleSheet("color: #94a3b8; font-size: 12px;")

        b_layout.addWidget(app_title)
        b_layout.addWidget(tagline)
        b_layout.addWidget(version)
        layout.addWidget(banner_card)

        # Gestures Quick Reference Card
        guide_card = QFrame()
        guide_card.setProperty("class", "Card")
        g_layout = QVBoxLayout(guide_card)
        g_layout.setSpacing(12)

        g_title = QLabel("HAND GESTURE QUICK REFERENCE")
        g_title.setProperty("class", "CardTitle")
        g_layout.addWidget(g_title)

        gestures_list = [
            ("Index Finger Only", "Move the real Windows cursor with anti-tremor smoothing"),
            ("Thumb + Index Pinch", "Single Left Mouse Click"),
            ("Two Quick Pinches", "Double Left Mouse Click"),
            ("Pinch and Hold", "Drag and Drop (holds down left mouse button)"),
            ("Index + Middle Together", "Right Mouse Click"),
            ("Open Palm (Hold 0.8s)", "Summons the Floating HUD Quick Control Menu"),
            ("Closed Fist", "Emergency Safety Stop (temporarily pauses cursor motion)")
        ]

        for trigger, action in gestures_list:
            row = QHBoxLayout()
            lbl_trig = QLabel(f"• {trigger}:")
            lbl_trig.setStyleSheet("color: #00f2fe; font-weight: 700; min-width: 200px;")
            lbl_act = QLabel(action)
            lbl_act.setStyleSheet("color: #e2e8f0;")
            row.addWidget(lbl_trig)
            row.addWidget(lbl_act, stretch=1)
            g_layout.addLayout(row)

        layout.addWidget(guide_card)

        # Clap Control Reference Card
        clap_card = QFrame()
        clap_card.setProperty("class", "Card")
        c_layout = QVBoxLayout(clap_card)
        c_layout.setSpacing(12)

        c_title = QLabel("CLAP DETECTION QUICK REFERENCE")
        c_title.setProperty("class", "CardTitle")
        c_layout.addWidget(c_title)

        claps_list = [
            ("1 Clap", "Toggle Virtual Mouse ON / OFF"),
            ("2 Claps", "Open AIRCTRL Quick Launch Menu"),
            ("3 Claps", "Open Virtual Keyboard"),
            ("4 Claps", "Emergency Pause All Virtual Controls"),
            ("Keyboard Shortcut", "Press Ctrl + Shift + Q anywhere on Windows to halt automation")
        ]

        for trigger, action in claps_list:
            row = QHBoxLayout()
            lbl_trig = QLabel(f"• {trigger}:")
            lbl_trig.setStyleSheet("color: #38bdf8; font-weight: 700; min-width: 200px;")
            lbl_act = QLabel(action)
            lbl_act.setStyleSheet("color: #e2e8f0;")
            row.addWidget(lbl_trig)
            row.addWidget(lbl_act, stretch=1)
            c_layout.addLayout(row)

        layout.addWidget(clap_card)

        # Tech Stack Card
        tech_card = QFrame()
        tech_card.setProperty("class", "Card")
        t_layout = QVBoxLayout(tech_card)
        t_layout.setSpacing(8)

        t_title = QLabel("BUILT WITH PRODUCTION PYTHON TECHNOLOGIES")
        t_title.setProperty("class", "CardTitle")
        t_layout.addWidget(t_title)

        tech_desc = QLabel(
            "• OpenCV – Real-time low-latency video capture & frame rendering\n"
            "• MediaPipe Tasks – 21 3D hand landmark recognition model\n"
            "• PySide6 (Qt) – Modern reactive dark futuristic desktop GUI\n"
            "• SoundDevice & SciPy – Real-time audio DSP, Butterworth bandpass filtering & transient detection\n"
            "• Win32 API, PyAutoGUI & Pynput – Hardware-level mouse & keyboard automation\n"
            "• Windows Registry & Startup Integration – Native HKCU autostart on Windows boot\n"
            "• SQLite3 & JSON – Embedded local persistence for audit logs and user preferences"
        )
        tech_desc.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.6;")
        t_layout.addWidget(tech_desc)
        layout.addWidget(tech_card)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

