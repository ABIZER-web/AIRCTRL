"""
AIRCTRL Camera Manager
Runs in a background QThread to capture video frames asynchronously from real webcams
or provides an intelligent synthetic feed when no camera is present.
"""
import time
import math
import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal
from utils.logger import get_logger
from utils.settings_manager import settings

logger = get_logger("CameraManager")

class CameraWorker(QThread):
    """Asynchronous worker thread for continuous camera capture."""
    frame_ready = Signal(np.ndarray)
    status_changed = Signal(bool, str)
    fps_changed = Signal(float)

    def __init__(self, device_index: int = 0, width: int = 640, height: int = 480, fps: int = 30, mirror: bool = True):
        super().__init__()
        self.device_index = device_index
        self.target_width = width
        self.target_height = height
        self.target_fps = fps
        self.mirror = mirror
        self.running = False
        self.is_connected = False
        self.using_fallback = False
        self._cap = None
        self._anim_phase = 0.0

    def run(self):
        self.running = True
        logger.info(f"Starting camera capture thread (Device: {self.device_index})")
        self._open_camera()

        prev_time = time.time()
        fps_count = 0
        fps_start = time.time()
        current_fps = 0.0

        while self.running:
            frame = None
            if self._cap and self._cap.isOpened():
                ret, raw_frame = self._cap.read()
                if ret and raw_frame is not None:
                    if not self.is_connected:
                        self.is_connected = True
                        self.using_fallback = False
                        self.status_changed.emit(True, f"Webcam Connected (Cam {self.device_index})")
                    frame = raw_frame
                else:
                    logger.warning("Camera read returned empty frame. Attempting recovery...")
                    self.is_connected = False
                    self.status_changed.emit(False, "Webcam disconnected. Reconnecting...")
                    self._cap.release()
                    self._cap = None
                    time.sleep(1.0)
                    self._open_camera()

            if frame is None:
                # Generate synthetic frame if hardware camera is unavailable
                frame = self._generate_synthetic_frame()
                if not self.using_fallback:
                    self.using_fallback = True
                    self.is_connected = False
                    self.status_changed.emit(False, "No physical camera detected. Running virtual test feed.")

            # Mirror preview if requested
            if self.mirror:
                frame = cv2.flip(frame, 1)

            # Resize if needed
            if frame.shape[1] != self.target_width or frame.shape[0] != self.target_height:
                frame = cv2.resize(frame, (self.target_width, self.target_height))

            self.frame_ready.emit(frame)

            # FPS calculation
            fps_count += 1
            now = time.time()
            if now - fps_start >= 1.0:
                current_fps = fps_count / (now - fps_start)
                self.fps_changed.emit(round(current_fps, 1))
                fps_count = 0
                fps_start = now

            # Throttle loop to target FPS
            elapsed = time.time() - prev_time
            sleep_time = max(0.001, (1.0 / max(1, self.target_fps)) - elapsed)
            time.sleep(sleep_time)
            prev_time = time.time()

        self._cleanup()
        logger.info("Camera capture thread stopped.")

    def _open_camera(self):
        """Attempts to open physical camera using DirectShow then default backend."""
        try:
            # Try DirectShow first on Windows for fast startup
            cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap.release()
                cap = cv2.VideoCapture(self.device_index)

            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
                cap.set(cv2.CAP_PROP_FPS, self.target_fps)
                self._cap = cap
                self.is_connected = True
                self.using_fallback = False
                logger.info(f"Successfully opened camera {self.device_index}")
                self.status_changed.emit(True, f"Webcam Connected (Cam {self.device_index})")
            else:
                logger.info(f"Camera index {self.device_index} not accessible.")
                self._cap = None
        except Exception as e:
            logger.error(f"Error opening camera: {e}")
            self._cap = None

    def _generate_synthetic_frame(self) -> np.ndarray:
        """
        Generates a synthetic camera test frame.
        Renders an animated test hand so features can be tested even on machines without a webcam.
        """
        w, h = self.target_width, self.target_height
        img = np.zeros((h, w, 3), dtype=np.uint8)

        # Futuristic dark background gradient
        for y in range(h):
            ratio = y / h
            b = int(24 + 10 * ratio)
            g = int(14 + 10 * ratio)
            r = int(10 + 5 * ratio)
            img[y, :] = (b, g, r)

        # Draw subtle grid lines
        grid_size = 40
        for x in range(0, w, grid_size):
            cv2.line(img, (x, 0), (x, h), (35, 25, 20), 1)
        for y in range(0, h, grid_size):
            cv2.line(img, (0, y), (w, y), (35, 25, 20), 1)

        self._anim_phase += 0.04
        t = self._anim_phase

        # Center target
        cx = int(w * 0.5 + math.sin(t * 0.8) * (w * 0.2))
        cy = int(h * 0.5 + math.cos(t * 0.6) * (h * 0.15))

        # Render a stylized simulated hand outline
        # Palm
        cv2.circle(img, (cx, cy + 30), 25, (80, 50, 30), -1)
        cv2.circle(img, (cx, cy + 30), 25, (0, 220, 255), 2)

        # Wrist
        cv2.line(img, (cx, cy + 30), (cx, cy + 80), (0, 200, 240), 3)

        # Index finger pointing up
        idx_tip = (cx, cy - 40)
        cv2.line(img, (cx, cy + 30), idx_tip, (0, 242, 254), 3)
        cv2.circle(img, idx_tip, 8, (0, 255, 255), -1)
        cv2.circle(img, idx_tip, 12, (255, 200, 0), 1)

        # Thumb
        thumb_tip = (cx - 30, cy + 10)
        cv2.line(img, (cx, cy + 30), thumb_tip, (0, 200, 240), 2)
        cv2.circle(img, thumb_tip, 6, (0, 220, 255), -1)

        # Curled middle, ring, pinky
        for i, offset_x in enumerate([15, 30, 42]):
            cv2.circle(img, (cx + offset_x, cy + 15), 5, (0, 180, 200), -1)
            cv2.line(img, (cx, cy + 30), (cx + offset_x, cy + 15), (0, 150, 180), 2)

        # HUD Overlay text
        cv2.putText(img, "AIRCTRL VIRTUAL CAMERA (SYNTHETIC FEED)", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 240, 255), 1, cv2.LINE_AA)
        cv2.putText(img, "Connect physical webcam or run live AI tracking", (20, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1, cv2.LINE_AA)
        cv2.putText(img, f"Tracked Index: ({cx}, {cy - 40})", (20, h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 128), 1, cv2.LINE_AA)

        return img

    def _cleanup(self):
        if self._cap:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        self.is_connected = False

    def stop(self):
        self.running = False
        self.wait(1500)


class CameraManager:
    """High-level camera management interface."""
    def __init__(self):
        self.worker: CameraWorker = None

    def start(self, device_index: int = None, width: int = None, height: int = None, fps: int = None, mirror: bool = None) -> CameraWorker:
        cfg = settings.get("camera")
        dev = device_index if device_index is not None else cfg.get("device_index", 0)
        w = width if width is not None else cfg.get("width", 640)
        h = height if height is not None else cfg.get("height", 480)
        f = fps if fps is not None else cfg.get("fps", 30)
        m = mirror if mirror is not None else cfg.get("mirror", True)

        self.stop()
        self.worker = CameraWorker(device_index=dev, width=w, height=h, fps=f, mirror=m)
        self.worker.start()
        return self.worker

    def stop(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker = None

    @staticmethod
    def get_available_cameras(max_tested: int = 4) -> list:
        """Probes available video devices on Windows."""
        available = []
        for index in range(max_tested):
            try:
                cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
                if cap.isOpened():
                    available.append(index)
                    cap.release()
            except Exception:
                pass
        return available

camera_mgr = CameraManager()

