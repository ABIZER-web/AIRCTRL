"""
AIRCTRL Webcam Preview Widget
Displays camera video feed with hardware acceleration, responsive scaling,
and HUD overlays (landmarks, bounding box, active gesture label, FPS).
"""
import cv2
import numpy as np
from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QFont, QPen

class WebcamPreviewWidget(QLabel):
    """Custom widget for rendering the video stream and HUD telemetry."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(480, 320)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
            WebcamPreviewWidget {
                background-color: #060a10;
                border: 2px solid rgba(0, 242, 254, 0.25);
                border-radius: 12px;
            }
        """)

        self._current_pixmap: QPixmap = None
        self.fps: float = 0.0
        self.gesture_name: str = "NONE"
        self.tracking_active: bool = False
        self.cursor_point = None

    def update_frame(self, frame_bgr: np.ndarray, gesture_name: str = "NONE", fps: float = 0.0, cursor_px=None):
        """Converts BGR OpenCV frame to QPixmap and triggers repaint."""
        self.gesture_name = gesture_name
        self.fps = fps
        self.cursor_point = cursor_px

        h, w, ch = frame_bgr.shape
        bytes_per_line = ch * w
        # Convert BGR to RGB for Qt
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        q_img = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self._current_pixmap = QPixmap.fromImage(q_img)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self._current_pixmap and not self._current_pixmap.isNull():
            # Scale pixmap preserving aspect ratio
            scaled = self._current_pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            # Center it
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

            # Draw HUD Overlays
            # FPS Tag
            painter.setPen(QColor(0, 242, 254))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(x + 15, y + 25, f"FPS: {self.fps:.1f}")

            # Active Gesture Pill at bottom
            if self.gesture_name and self.gesture_name != "NONE":
                pill_text = f"GESTURE: {self.gesture_name}"
                painter.setBrush(QColor(13, 21, 36, 220))
                painter.setPen(QColor(0, 242, 254))
                font = QFont("Segoe UI", 10, QFont.Bold)
                painter.setFont(font)
                metrics = painter.fontMetrics()
                tw = metrics.horizontalAdvance(pill_text) + 24
                th = metrics.height() + 10
                bx = x + (scaled.width() - tw) // 2
                by = y + scaled.height() - 40
                painter.drawRoundedRect(bx, by, tw, th, 8, 8)
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(bx + 12, by + metrics.ascent() + 4, pill_text)
        else:
            # Placeholder text if no frame received
            painter.setPen(QColor(100, 116, 139))
            painter.setFont(QFont("Segoe UI", 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "Webcam feed loading or paused...")

