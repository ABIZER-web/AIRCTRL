"""
AIRCTRL Calibration Module
Guides user through a 4-corner calibration routine to map their comfortable
webcam range to the computer screen resolution.
"""
import time
from typing import Tuple, List, Optional
from PySide6.QtCore import QObject, Signal
from utils.logger import get_logger
from utils.settings_manager import settings

logger = get_logger("Calibration")

CALIB_TOP_LEFT = 0
CALIB_TOP_RIGHT = 1
CALIB_BOTTOM_RIGHT = 2
CALIB_BOTTOM_LEFT = 3
CALIB_COMPLETE = 4

CORNER_NAMES = [
    "Top-Left Corner",
    "Top-Right Corner",
    "Bottom-Right Corner",
    "Bottom-Left Corner"
]

class CalibrationManager(QObject):
    """Coordinates the 4-corner camera active area calibration."""
    step_changed = Signal(int, str)  # current_step, step_instruction
    calibration_finished = Signal(list)  # [x_min, y_min, x_max, y_max]

    def __init__(self):
        super().__init__()
        self.is_calibrating = False
        self.current_step = CALIB_TOP_LEFT
        self._samples: List[Tuple[float, float]] = []
        self._corner_points: List[Tuple[float, float]] = []
        self._step_start_time = 0.0

    def start_calibration(self):
        """Starts or restarts calibration."""
        self.is_calibrating = True
        self.current_step = CALIB_TOP_LEFT
        self._samples.clear()
        self._corner_points.clear()
        self._step_start_time = time.time()
        logger.info("Starting 4-corner calibration.")
        self.step_changed.emit(self.current_step, f"Move your index finger to the {CORNER_NAMES[self.current_step]}")

    def update_tracking_point(self, norm_x: float, norm_y: float):
        """Processes index fingertip coordinates during calibration."""
        if not self.is_calibrating or self.current_step >= CALIB_COMPLETE:
            return

        self._samples.append((norm_x, norm_y))
        now = time.time()

        # Collect samples for 2.0 seconds per corner
        if now - self._step_start_time >= 2.0 and len(self._samples) >= 15:
            # Compute average position for this corner
            avg_x = sum(p[0] for p in self._samples) / len(self._samples)
            avg_y = sum(p[1] for p in self._samples) / len(self._samples)
            self._corner_points.append((avg_x, avg_y))
            logger.info(f"Captured corner {CORNER_NAMES[self.current_step]}: ({avg_x:.3f}, {avg_y:.3f})")

            self.current_step += 1
            self._samples.clear()
            self._step_start_time = time.time()

            if self.current_step < CALIB_COMPLETE:
                self.step_changed.emit(self.current_step, f"Move your index finger to the {CORNER_NAMES[self.current_step]}")
            else:
                self._finish_calibration()

    def _finish_calibration(self):
        """Computes bounding area and saves to settings."""
        self.is_calibrating = False

        xs = [p[0] for p in self._corner_points]
        ys = [p[1] for p in self._corner_points]

        x_min = max(0.02, min(xs))
        x_max = min(0.98, max(xs))
        y_min = max(0.02, min(ys))
        y_max = min(0.98, max(ys))

        # Ensure valid non-collapsed box
        if x_max - x_min < 0.15:
            x_min, x_max = 0.15, 0.85
        if y_max - y_min < 0.15:
            y_min, y_max = 0.15, 0.85

        active_area = [round(x_min, 3), round(y_min, 3), round(x_max, 3), round(y_max, 3)]
        logger.info(f"Calibration successful! New active area: {active_area}")

        settings.set("mouse", "active_area", active_area)
        self.calibration_finished.emit(active_area)
        self.step_changed.emit(CALIB_COMPLETE, "Calibration Complete! Settings saved.")

    def cancel(self):
        self.is_calibrating = False
        self._samples.clear()
        self._corner_points.clear()
        logger.info("Calibration cancelled.")

calibration_mgr = CalibrationManager()

