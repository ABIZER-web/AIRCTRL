"""
AIRCTRL Stat Card Component
Displays a modern metric card with title, large numerical value, and optional subtitle.
"""
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class StatCard(QFrame):
    def __init__(self, title: str, initial_value: str = "0", subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("class", "Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setProperty("class", "CardTitle")

        self.value_label = QLabel(initial_value)
        self.value_label.setProperty("class", "CardValue")

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setProperty("class", "CardSubtitle")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        if subtitle:
            layout.addWidget(self.subtitle_label)

    def set_value(self, val: str):
        self.value_label.setText(str(val))

    def set_subtitle(self, sub: str):
        self.subtitle_label.setText(str(sub))

