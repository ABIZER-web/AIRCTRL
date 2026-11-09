"""
AIRCTRL Virtual Keyboard
High-fidelity modern on-screen virtual keyboard with full QWERTY, numeric,
symbol, and navigation key matrices. Supports real OS typing, hover feedback,
pinch-to-type gesture selection, and an integrated typing preview.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QCheckBox, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont

from core.keyboard_controller import keyboard_ctrl
from utils.settings_manager import settings
from utils.helpers import play_feedback_sound

class VirtualKeyButton(QPushButton):
    """Custom styled virtual keyboard button with hover highlighting."""
    def __init__(self, label: str, key_code: str = None, parent=None):
        super().__init__(label, parent)
        self.key_code = key_code or label
        self.setFocusPolicy(Qt.NoFocus)  # Prevent stealing OS window focus
        self._set_idle_style()

    def _set_idle_style(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: #162235;
                color: #e2e8f0;
                border: 1px solid rgba(0, 242, 254, 0.2);
                border-radius: 6px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                font-weight: 700;
                min-height: 42px;
                min-width: 42px;
            }
            QPushButton:hover {
                background-color: rgba(0, 242, 254, 0.25);
                border-color: #00f2fe;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #00c6ff;
                color: #000000;
            }
        """)

    def set_highlight(self, active: bool):
        if active:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #00f2fe;
                    color: #000000;
                    border: 2px solid #ffffff;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: 800;
                    min-height: 42px;
                    min-width: 42px;
                }
            """)
        else:
            self._set_idle_style()


class VirtualKeyboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.keys_map = {}
        self._setup_ui()
        keyboard_ctrl.key_typed.connect(self._on_key_typed_signal)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Header
        top_box = QHBoxLayout()
        header = QVBoxLayout()
        t = QLabel("VIRTUAL KEYBOARD")
        t.setStyleSheet("color: #00f2fe; font-size: 20px; font-weight: 800; letter-spacing: 1px;")
        sub = QLabel("Type hands-free into any Windows application (Notepad, browser) using hover and pinch gestures.")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        header.addWidget(t)
        header.addWidget(sub)
        top_box.addLayout(header)
        top_box.addStretch()

        # Options Box
        self.chk_direct = QCheckBox("Direct OS Application Input")
        self.chk_direct.setChecked(settings.get("keyboard", "direct_system_input", True))
        self.chk_direct.stateChanged.connect(self._toggle_direct_input)
        top_box.addWidget(self.chk_direct)

        layout.addLayout(top_box)

        # Typing Preview Card
        preview_card = QFrame()
        preview_card.setProperty("class", "Card")
        preview_layout = QHBoxLayout(preview_card)
        preview_layout.setContentsMargins(16, 12, 16, 12)
        preview_layout.setSpacing(12)

        self.preview_input = QLineEdit()
        self.preview_input.setPlaceholderText("Virtual typing preview buffer (text appears here)...")
        self.preview_input.setStyleSheet("""
            QLineEdit {
                background-color: #090e17;
                color: #00f2fe;
                font-family: 'Consolas', monospace;
                font-size: 16px;
                padding: 10px;
                border: 1px solid rgba(0, 242, 254, 0.4);
            }
        """)

        btn_copy = QPushButton("Copy Text")
        btn_copy.setProperty("class", "SecondaryBtn")
        btn_copy.clicked.connect(self._copy_preview)

        btn_clear = QPushButton("Clear")
        btn_clear.setProperty("class", "DangerBtn")
        btn_clear.clicked.connect(self._clear_preview)

        preview_layout.addWidget(self.preview_input, stretch=1)
        preview_layout.addWidget(btn_copy)
        preview_layout.addWidget(btn_clear)
        layout.addWidget(preview_card)

        # Keyboard Matrix Frame
        kb_frame = QFrame()
        kb_frame.setProperty("class", "Card")
        kb_layout = QVBoxLayout(kb_frame)
        kb_layout.setSpacing(8)

        # Row 1: Numbers & Symbols
        row1 = ["`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "BACKSPACE"]
        # Row 2: Tab + QWERTY
        row2 = ["TAB", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", "\\"]
        # Row 3: Caps + ASDF + Enter
        row3 = ["CAPS", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "ENTER"]
        # Row 4: Shift + ZXCV + Arrows
        row4 = ["SHIFT", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "UP", "DEL"]
        # Row 5: Space & Controls
        row5 = ["CTRL", "ALT", "SPACE", "ESC", "LEFT", "DOWN", "RIGHT"]

        kb_layout.addLayout(self._create_key_row(row1, stretch_keys={"BACKSPACE": 2}))
        kb_layout.addLayout(self._create_key_row(row2, stretch_keys={"TAB": 2, "\\": 1}))
        kb_layout.addLayout(self._create_key_row(row3, stretch_keys={"CAPS": 2, "ENTER": 2}))
        kb_layout.addLayout(self._create_key_row(row4, stretch_keys={"SHIFT": 2}))
        kb_layout.addLayout(self._create_key_row(row5, stretch_keys={"SPACE": 5}))

        layout.addWidget(kb_frame)
        layout.addStretch()

    def _create_key_row(self, keys_list, stretch_keys=None):
        row_layout = QHBoxLayout()
        row_layout.setSpacing(6)
        stretch_keys = stretch_keys or {}

        for k in keys_list:
            btn = VirtualKeyButton(k, parent=self)
            btn.clicked.connect(lambda ch=False, key=k: self._on_key_clicked(key))
            self.keys_map[k] = btn
            stretch = stretch_keys.get(k, 1)
            row_layout.addWidget(btn, stretch=stretch)

        return row_layout

    def _on_key_clicked(self, key_label: str):
        keyboard_ctrl.type_key(key_label)

    def _on_key_typed_signal(self, char: str):
        # Update local preview box
        if char == "BACKSPACE":
            cur = self.preview_input.text()
            self.preview_input.setText(cur[:-1])
        elif char == "\n":
            self.preview_input.setText(self.preview_input.text() + " ")
        elif char in ("SHIFT", "CAPS", "CTRL", "ALT", "ESC", "UP", "DOWN", "LEFT", "RIGHT", "DELETE"):
            pass
        else:
            self.preview_input.setText(self.preview_input.text() + char)

    def _toggle_direct_input(self, state):
        enabled = (state == Qt.Checked.value or state == True)
        settings.set("keyboard", "direct_system_input", enabled)

    def _copy_preview(self):
        play_feedback_sound("click")
        text = self.preview_input.text()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)

    def _clear_preview(self):
        play_feedback_sound("click")
        self.preview_input.clear()

