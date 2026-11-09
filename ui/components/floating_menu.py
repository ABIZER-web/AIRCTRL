"""
AIRCTRL Floating Gesture Control Menu
Appears as a sleek HUD overlay when the user holds an Open Palm gesture.
Allows rapid navigation to Virtual Mouse, Virtual Keyboard, Quick Launch, Pause All, or Settings.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
from utils.helpers import play_feedback_sound

class FloatingGestureMenu(QWidget):
    option_selected = Signal(str)  # emitted with action identifier

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(260, 320)

        # Auto dismiss timer (5 seconds inactivity)
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self.hide_menu)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        # Container card
        self.card = QWidget(self)
        self.card.setStyleSheet("""
            QWidget {
                background-color: rgba(13, 21, 36, 0.95);
                border: 2px solid #00f2fe;
                border-radius: 16px;
            }
        """)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)

        # Title
        title = QLabel("QUICK GESTURE MENU", self.card)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #00f2fe; font-size: 13px; font-weight: 800; letter-spacing: 1.5px;")
        card_layout.addWidget(title)

        # Options
        options = [
            ("Virtual Mouse", "nav_mouse"),
            ("Virtual Keyboard", "nav_keyboard"),
            ("Quick Launch", "nav_quick_launch"),
            ("Pause All Controls", "pause_all"),
            ("Settings", "nav_settings")
        ]

        self.buttons = []
        for label, action in options:
            btn = QPushButton(label, self.card)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.06);
                    color: #f1f5f9;
                    border: 1px solid rgba(0, 242, 254, 0.25);
                    border-radius: 8px;
                    padding: 9px;
                    font-weight: 600;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 242, 254, 0.2);
                    border-color: #00f2fe;
                    color: #ffffff;
                }
            """)
            btn.clicked.connect(lambda checked=False, a=action: self._select_action(a))
            card_layout.addWidget(btn)
            self.buttons.append((btn, action))

        layout.addWidget(self.card)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 242, 254, 120))
        shadow.setOffset(0, 0)
        self.card.setGraphicsEffect(shadow)

    def show_menu(self):
        """Displays menu and starts auto-dismiss timer."""
        self.show()
        self.raise_()
        self.dismiss_timer.start(5000)
        play_feedback_sound("launch")

    def hide_menu(self):
        self.dismiss_timer.stop()
        self.hide()

    def _select_action(self, action: str):
        play_feedback_sound("click")
        self.option_selected.emit(action)
        self.hide_menu()

