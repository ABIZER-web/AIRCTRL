"""
AIRCTRL Real Mouse Controller
Interfaces directly with the Windows Win32 API (and PyAutoGUI) to control
the actual operating system cursor with anti-tremor smoothing, acceleration,
and gesture-driven clicks/drags.
"""
import ctypes
import time
from typing import Tuple, Optional
from PySide6.QtCore import QObject, Signal

from utils.logger import get_logger
from utils.helpers import get_screen_resolution, map_coordinates, OneEuroFilter, EMAFilter, play_feedback_sound
from utils.settings_manager import settings
from database.history_manager import history
from core.safety_manager import safety

logger = get_logger("MouseController")

# Win32 Mouse Event Flags
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

class MouseController(QObject):
    """Controls the real Windows mouse cursor and click events."""
    mouse_moved = Signal(int, int)  # target_x, target_y
    clicked = Signal(str)           # "left", "right", "double"

    def __init__(self):
        super().__init__()
        self.screen_width, self.screen_height = get_screen_resolution()
        self._user32 = None
        self._init_win32()

        # Filters
        self._filter = OneEuroFilter(min_cutoff=1.2, beta=0.008)
        self._ema = EMAFilter(alpha=0.65)
        self.is_dragging = False
        self.total_clicks = 0

    def _init_win32(self):
        try:
            self._user32 = ctypes.windll.user32
            logger.info(f"Initialized Win32 mouse controller. Screen: {self.screen_width}x{self.screen_height}")
        except Exception as e:
            logger.warning(f"Win32 mouse API not directly accessible, will use pyautogui: {e}")
            self._user32 = None

    def refresh_screen_size(self):
        self.screen_width, self.screen_height = get_screen_resolution()

    def move_to(self, norm_x: float, norm_y: float):
        """
        Maps normalized index coordinates to screen pixels, filters jitter,
        and moves the real Windows cursor.
        """
        if not safety.is_active:
            return

        cfg_mouse = settings.get("mouse")
        if not cfg_mouse.get("enabled", True):
            return

        sensitivity = cfg_mouse.get("sensitivity", 1.2)
        acceleration = cfg_mouse.get("acceleration", 1.0)
        active_area = cfg_mouse.get("active_area", [0.15, 0.15, 0.85, 0.85])

        # Map to physical screen coordinates
        raw_x, raw_y = map_coordinates(
            norm_x, norm_y,
            self.screen_width, self.screen_height,
            calib_box=tuple(active_area),
            sensitivity=sensitivity,
            acceleration=acceleration
        )

        # Smooth position to prevent tremors
        smoothness = cfg_mouse.get("smoothness", 0.65)
        self._ema.alpha = max(0.1, min(0.95, 1.0 - smoothness * 0.7))
        smoothed_x, smoothed_y = self._ema.update(raw_x, raw_y)
        final_x, final_y = self._filter.update(smoothed_x, smoothed_y)

        ix, iy = int(round(final_x)), int(round(final_y))

        # Perform actual move
        if self._user32:
            self._user32.SetCursorPos(ix, iy)
        else:
            try:
                import pyautogui
                pyautogui.moveTo(ix, iy)
            except Exception:
                pass

        self.mouse_moved.emit(ix, iy)

    def left_click(self):
        """Performs a real left mouse click."""
        if not safety.is_active:
            return
        if self._user32:
            self._user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.015)
            self._user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        else:
            try:
                import pyautogui
                pyautogui.click(button='left')
            except Exception:
                pass

        self.total_clicks += 1
        history.record_event("click", "Left Click", 1)
        play_feedback_sound("click")
        self.clicked.emit("left")
        logger.debug("Left click triggered.")

    def double_click(self):
        """Performs a real double click."""
        if not safety.is_active:
            return
        if self._user32:
            self._user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.015)
            self._user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            time.sleep(0.08)
            self._user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.015)
            self._user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        else:
            try:
                import pyautogui
                pyautogui.doubleClick()
            except Exception:
                pass

        self.total_clicks += 2
        history.record_event("click", "Double Click", 2)
        play_feedback_sound("double_click")
        self.clicked.emit("double")
        logger.debug("Double click triggered.")

    def right_click(self):
        """Performs a real right click."""
        if not safety.is_active:
            return
        if self._user32:
            self._user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            time.sleep(0.015)
            self._user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        else:
            try:
                import pyautogui
                pyautogui.click(button='right')
            except Exception:
                pass

        self.total_clicks += 1
        history.record_event("click", "Right Click", 1)
        play_feedback_sound("right_click")
        self.clicked.emit("right")
        logger.debug("Right click triggered.")

    def start_drag(self):
        """Begins mouse drag (holds left button down)."""
        if not safety.is_active or self.is_dragging:
            return
        self.is_dragging = True
        if self._user32:
            self._user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        else:
            try:
                import pyautogui
                pyautogui.mouseDown(button='left')
            except Exception:
                pass
        play_feedback_sound("click")
        logger.info("Drag started (mouse button held down).")

    def end_drag(self):
        """Ends mouse drag (releases left button)."""
        if not self.is_dragging:
            return
        self.is_dragging = False
        if self._user32:
            self._user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        else:
            try:
                import pyautogui
                pyautogui.mouseUp(button='left')
            except Exception:
                pass
        play_feedback_sound("click")
        logger.info("Drag released.")

    def reset_filters(self):
        self._filter.reset()
        self._ema.reset()
        if self.is_dragging:
            self.end_drag()

mouse_ctrl = MouseController()

