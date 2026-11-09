"""
AIRCTRL Gesture Recognition Module
High-precision state machine recognizing 7 core hand gestures with debouncing,
hysteresis, double-pinch detection, and drag-and-drop transitions.
"""
import time
from typing import Optional, Tuple
from PySide6.QtCore import QObject, Signal
from core.hand_tracking import HandData
from utils.logger import get_logger
from utils.settings_manager import settings
from database.history_manager import history

logger = get_logger("GestureRecognition")

# Gesture Enum Strings
GESTURE_NONE = "NONE"
GESTURE_MOVE = "CURSOR_MOVE"
GESTURE_LEFT_CLICK = "LEFT_CLICK"
GESTURE_DOUBLE_CLICK = "DOUBLE_CLICK"
GESTURE_DRAG = "DRAG"
GESTURE_RIGHT_CLICK = "RIGHT_CLICK"
GESTURE_OPEN_PALM = "OPEN_PALM"
GESTURE_OPEN_PALM_MENU = "OPEN_PALM_MENU"
GESTURE_CLOSED_FIST = "CLOSED_FIST"

class GestureRecognizer(QObject):
    """Detects and debounces gestures from hand landmarks."""
    gesture_detected = Signal(str, object)  # gesture_name, extra_data dict

    def __init__(self):
        super().__init__()
        self._current_gesture = GESTURE_NONE
        self._pinch_active = False
        self._pinch_start_time = 0.0
        self._is_dragging = False

        self._last_click_time = 0.0
        self._last_gesture_time = 0.0
        self._palm_start_time = 0.0
        self._last_right_click_time = 0.0

        # Pending single click detection for double click differentiation
        self._last_pinch_release_time = 0.0
        self._pending_single_click = False

    def reset_state(self):
        """Resets state machine."""
        self._current_gesture = GESTURE_NONE
        self._pinch_active = False
        self._is_dragging = False
        self._palm_start_time = 0.0
        self._pending_single_click = False

    def update(self, hand: Optional[HandData]) -> Tuple[str, dict]:
        """
        Evaluates the current hand pose and updates gesture state.
        Returns (gesture_name, extra_info).
        """
        now = time.time()
        extra_info = {
            "cursor_norm": (0.5, 0.5),
            "is_dragging": self._is_dragging,
            "raw_gesture": GESTURE_NONE
        }

        # Resolve pending single click if double click window expired
        cfg_mouse = settings.get("mouse")
        double_click_interval = cfg_mouse.get("double_click_interval", 0.4)
        if self._pending_single_click and (now - self._last_pinch_release_time > double_click_interval):
            self._pending_single_click = False
            self.gesture_detected.emit(GESTURE_LEFT_CLICK, {"type": "single"})
            history.record_event("gesture", GESTURE_LEFT_CLICK, 1)

        if hand is None:
            if self._is_dragging:
                self._is_dragging = False
                self.gesture_detected.emit("DRAG_END", {})
            self._pinch_active = False
            self._current_gesture = GESTURE_NONE
            return GESTURE_NONE, extra_info

        # Track index fingertip
        extra_info["cursor_norm"] = hand.index_tip_norm
        cfg_gestures = settings.get("gestures")
        click_threshold = cfg_mouse.get("click_threshold", 0.055)
        drag_hold_sec = cfg_mouse.get("drag_hold_sec", 0.35)
        gesture_cooldown = cfg_mouse.get("gesture_cooldown", 0.25)

        # 1. Check for CLOSED FIST
        if cfg_gestures.get("closed_fist", True) and hand.extended_count == 0:
            self._current_gesture = GESTURE_CLOSED_FIST
            extra_info["raw_gesture"] = GESTURE_CLOSED_FIST
            if self._is_dragging:
                self._is_dragging = False
                self.gesture_detected.emit("DRAG_END", {})
            return GESTURE_CLOSED_FIST, extra_info

        # 2. Check for OPEN PALM
        if cfg_gestures.get("open_palm", True) and hand.extended_count >= 4:
            if self._palm_start_time == 0.0:
                self._palm_start_time = now
            palm_duration = now - self._palm_start_time
            menu_hold_time = cfg_gestures.get("menu_hold_time", 0.8)

            if palm_duration >= menu_hold_time:
                self._current_gesture = GESTURE_OPEN_PALM_MENU
                extra_info["raw_gesture"] = GESTURE_OPEN_PALM_MENU
                self.gesture_detected.emit(GESTURE_OPEN_PALM_MENU, {"duration": palm_duration})
                return GESTURE_OPEN_PALM_MENU, extra_info
            else:
                self._current_gesture = GESTURE_OPEN_PALM
                extra_info["raw_gesture"] = GESTURE_OPEN_PALM
                return GESTURE_OPEN_PALM, extra_info
        else:
            self._palm_start_time = 0.0

        # 3. Check for RIGHT CLICK (Index + Middle fingers together, ring & pinky down)
        if (cfg_gestures.get("right_click", True) and
            hand.is_index_extended and hand.is_middle_extended and
            not hand.is_ring_extended and not hand.is_pinky_extended and
            hand.index_middle_dist < 0.045):

            if now - self._last_right_click_time > max(0.5, gesture_cooldown):
                self._last_right_click_time = now
                self._current_gesture = GESTURE_RIGHT_CLICK
                extra_info["raw_gesture"] = GESTURE_RIGHT_CLICK
                self.gesture_detected.emit(GESTURE_RIGHT_CLICK, {})
                history.record_event("gesture", GESTURE_RIGHT_CLICK, 1)
                return GESTURE_RIGHT_CLICK, extra_info
            else:
                return GESTURE_NONE, extra_info

        # 4. Check for THUMB + INDEX PINCH (Left Click, Double Click, Drag & Drop)
        is_pinching = hand.thumb_index_dist < click_threshold

        if is_pinching:
            if not self._pinch_active:
                # Pinch down started
                self._pinch_active = True
                self._pinch_start_time = now
                self._is_dragging = False
            else:
                # Pinch is being held
                hold_duration = now - self._pinch_start_time
                if hold_duration >= drag_hold_sec and not self._is_dragging:
                    # Transition to DRAG
                    if cfg_gestures.get("drag_and_drop", True):
                        self._is_dragging = True
                        self._current_gesture = GESTURE_DRAG
                        extra_info["raw_gesture"] = GESTURE_DRAG
                        extra_info["is_dragging"] = True
                        self.gesture_detected.emit("DRAG_START", {})
                        history.record_event("gesture", "DRAG_START", 1)

            if self._is_dragging:
                self._current_gesture = GESTURE_DRAG
                extra_info["raw_gesture"] = GESTURE_DRAG
                extra_info["is_dragging"] = True
                return GESTURE_DRAG, extra_info

            # In transient pinch
            self._current_gesture = GESTURE_LEFT_CLICK
            extra_info["raw_gesture"] = GESTURE_LEFT_CLICK
            return GESTURE_LEFT_CLICK, extra_info

        else:
            # Pinch released
            if self._pinch_active:
                self._pinch_active = False
                hold_duration = now - self._pinch_start_time

                if self._is_dragging:
                    # End drag
                    self._is_dragging = False
                    self.gesture_detected.emit("DRAG_END", {})
                    history.record_event("gesture", "DRAG_END", 1)
                elif hold_duration < drag_hold_sec:
                    # Quick release: Could be single or double click
                    if self._pending_single_click and (now - self._last_pinch_release_time <= double_click_interval):
                        # 2nd quick pinch within interval -> DOUBLE CLICK!
                        self._pending_single_click = False
                        self._current_gesture = GESTURE_DOUBLE_CLICK
                        extra_info["raw_gesture"] = GESTURE_DOUBLE_CLICK
                        self.gesture_detected.emit(GESTURE_DOUBLE_CLICK, {})
                        history.record_event("gesture", GESTURE_DOUBLE_CLICK, 1)
                        return GESTURE_DOUBLE_CLICK, extra_info
                    else:
                        # First pinch release, mark pending
                        self._pending_single_click = True
                        self._last_pinch_release_time = now

        # 5. Default: CURSOR MOVEMENT
        if cfg_gestures.get("cursor_move", True) and hand.is_index_extended:
            self._current_gesture = GESTURE_MOVE
            extra_info["raw_gesture"] = GESTURE_MOVE
            return GESTURE_MOVE, extra_info

        self._current_gesture = GESTURE_NONE
        return GESTURE_NONE, extra_info


gesture_recognizer = GestureRecognizer()

