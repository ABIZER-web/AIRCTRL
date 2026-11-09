"""
AIRCTRL Audio Meter Component
Visualizes live audio microphone level and clap transients with a glowing LED meter.
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QLinearGradient

class AudioMeterWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(18)
        self.setMaximumHeight(24)
        self._level = 0.0  # 0.0 to 1.0
        self._peak_level = 0.0

    def set_level(self, level: float):
        self._level = max(0.0, min(1.0, level))
        if self._level > self._peak_level:
            self._peak_level = self._level
        else:
            self._peak_level = max(0.0, self._peak_level - 0.02)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Background track
        painter.setBrush(QColor(15, 23, 42))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 6, 6)

        # Active fill width
        fill_w = int(w * self._level)
        if fill_w > 0:
            gradient = QLinearGradient(0, 0, w, 0)
            gradient.setColorAt(0.0, QColor(0, 198, 255))
            gradient.setColorAt(0.65, QColor(0, 242, 254))
            gradient.setColorAt(0.9, QColor(255, 187, 0))
            gradient.setColorAt(1.0, QColor(255, 51, 102))

            painter.setBrush(gradient)
            painter.drawRoundedRect(0, 0, fill_w, h, 6, 6)

        # Peak indicator line
        peak_x = int(w * self._peak_level)
        if peak_x > 0:
            painter.setPen(QColor(255, 255, 255, 200))
            painter.drawLine(peak_x, 2, peak_x, h - 2)

