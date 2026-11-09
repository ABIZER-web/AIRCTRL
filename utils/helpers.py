"""
AIRCTRL Helpers & Math Utilities
Provides filters, coordinate transformations, sound feedback, and geometry helpers.
"""
import math
import time
import ctypes
from typing import Tuple, Optional

# Windows sound support
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


def play_feedback_sound(sound_type: str = "click"):
    """Plays low-latency Windows system feedback sounds."""
    if not HAS_WINSOUND:
        return
    try:
        if sound_type == "click":
            winsound.Beep(1200, 30)
        elif sound_type == "double_click":
            winsound.Beep(1400, 25)
            winsound.Beep(1600, 25)
        elif sound_type == "right_click":
            winsound.Beep(800, 40)
        elif sound_type == "clap":
            winsound.Beep(2000, 40)
        elif sound_type == "emergency":
            winsound.Beep(400, 150)
            winsound.Beep(300, 150)
        elif sound_type == "launch":
            winsound.Beep(1000, 30)
            winsound.Beep(1500, 40)
    except Exception:
        pass


def calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculates Euclidean distance between two 2D points."""
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def calculate_distance_3d(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
    """Calculates Euclidean distance between two 3D points."""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)


def get_screen_resolution() -> Tuple[int, int]:
    """Gets the primary Windows screen resolution using Win32 API."""
    try:
        user32 = ctypes.windll.user32
        # Enable DPI awareness to get actual physical pixels
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        if width > 0 and height > 0:
            return width, height
    except Exception:
        pass
    return 1920, 1080


class EMAFilter:
    """Exponential Moving Average filter for smooth trajectory tracking."""
    def __init__(self, alpha: float = 0.5):
        self.alpha = max(0.01, min(1.0, alpha))
        self.prev_val: Optional[Tuple[float, float]] = None

    def update(self, x: float, y: float) -> Tuple[float, float]:
        if self.prev_val is None:
            self.prev_val = (x, y)
            return x, y
        filtered_x = self.alpha * x + (1.0 - self.alpha) * self.prev_val[0]
        filtered_y = self.alpha * y + (1.0 - self.alpha) * self.prev_val[1]
        self.prev_val = (filtered_x, filtered_y)
        return filtered_x, filtered_y

    def reset(self):
        self.prev_val = None


class LowPassFilter:
    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha
        self.prev: Optional[float] = None

    def update(self, val: float, alpha: Optional[float] = None) -> float:
        a = self.alpha if alpha is None else alpha
        if self.prev is None:
            self.prev = val
            return val
        self.prev = a * val + (1.0 - a) * self.prev
        return self.prev

    def reset(self):
        self.prev = None


class OneEuroFilter:
    """
    1-Euro Filter: An adaptive low-pass filter specifically designed
    for human-computer interaction (tremor reduction at low speed, zero latency at high speed).
    """
    def __init__(self, min_cutoff: float = 1.0, beta: float = 0.007, d_cutoff: float = 1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_filter = LowPassFilter()
        self.dx_filter = LowPassFilter()
        self.y_filter = LowPassFilter()
        self.dy_filter = LowPassFilter()
        self.last_time: Optional[float] = None

    def _alpha(self, rate: float, cutoff: float) -> float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        te = 1.0 / rate
        return 1.0 / (1.0 + tau / te)

    def update(self, x: float, y: float) -> Tuple[float, float]:
        now = time.time()
        if self.last_time is None:
            self.last_time = now
            self.x_filter.update(x)
            self.y_filter.update(y)
            return x, y

        dt = max(1e-4, now - self.last_time)
        rate = 1.0 / dt
        self.last_time = now

        # Compute derivative (speed)
        prev_x = self.x_filter.prev if self.x_filter.prev is not None else x
        prev_y = self.y_filter.prev if self.y_filter.prev is not None else y
        dx = (x - prev_x) * rate
        dy = (y - prev_y) * rate

        # Filter derivative
        alpha_d = self._alpha(rate, self.d_cutoff)
        edx = self.dx_filter.update(dx, alpha_d)
        edy = self.dy_filter.update(dy, alpha_d)

        # Compute dynamic cutoff frequency based on movement speed
        cutoff_x = self.min_cutoff + self.beta * abs(edx)
        cutoff_y = self.min_cutoff + self.beta * abs(edy)

        # Filter position
        alpha_x = self._alpha(rate, cutoff_x)
        alpha_y = self._alpha(rate, cutoff_y)

        filtered_x = self.x_filter.update(x, alpha_x)
        filtered_y = self.y_filter.update(y, alpha_y)
        return filtered_x, filtered_y

    def reset(self):
        self.last_time = None
        self.x_filter.reset()
        self.dx_filter.reset()
        self.y_filter.reset()
        self.dy_filter.reset()


def map_coordinates(
    norm_x: float,
    norm_y: float,
    screen_width: int,
    screen_height: int,
    calib_box: Tuple[float, float, float, float] = (0.15, 0.15, 0.85, 0.85),
    sensitivity: float = 1.2,
    acceleration: float = 1.0
) -> Tuple[int, int]:
    """
    Maps normalized camera coordinates (0.0 to 1.0) within a calibration active area
    to physical Windows screen pixels, with optional acceleration.
    """
    x_min, y_min, x_max, y_max = calib_box
    active_w = max(0.05, x_max - x_min)
    active_h = max(0.05, y_max - y_min)

    # Normalize within calibration box
    rel_x = (norm_x - x_min) / active_w
    rel_y = (norm_y - y_min) / active_h

    # Center-based scaling with sensitivity
    rel_x = (rel_x - 0.5) * sensitivity + 0.5
    rel_y = (rel_y - 0.5) * sensitivity + 0.5

    # Optional non-linear acceleration
    if abs(acceleration - 1.0) > 0.05:
        dx = rel_x - 0.5
        dy = rel_y - 0.5
        sign_x = 1.0 if dx >= 0 else -1.0
        sign_y = 1.0 if dy >= 0 else -1.0
        rel_x = 0.5 + sign_x * (abs(dx) ** acceleration)
        rel_y = 0.5 + sign_y * (abs(dy) ** acceleration)

    # Clamp to [0, 1]
    rel_x = max(0.0, min(1.0, rel_x))
    rel_y = max(0.0, min(1.0, rel_y))

    target_x = int(rel_x * screen_width)
    target_y = int(rel_y * screen_height)

    # Ensure within bounds
    target_x = max(0, min(screen_width - 1, target_x))
    target_y = max(0, min(screen_height - 1, target_y))

    return target_x, target_y

