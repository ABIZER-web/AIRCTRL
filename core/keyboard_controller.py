"""
AIRCTRL Keyboard Controller
Sends real operating system keystrokes to active Windows applications with
safe character handling, modifier support (Shift/Caps/Ctrl/Alt), and typing debouncing.
"""
import time
from typing import Optional
from PySide6.QtCore import QObject, Signal
from pynput.keyboard import Controller as PynputController, Key

from utils.logger import get_logger
from utils.settings_manager import settings
from utils.helpers import play_feedback_sound
from database.history_manager import history
from core.safety_manager import safety

logger = get_logger("KeyboardController")

class KeyboardController(QObject):
    """Controls OS keyboard input safely."""
    key_typed = Signal(str)  # emitted when a key is executed

    def __init__(self):
        super().__init__()
        self._kb = PynputController()
        self.shift_active = False
        self.caps_lock_active = False
        self.ctrl_active = False
        self.alt_active = False
        self._last_type_time = 0.0

    def type_key(self, key_label: str):
        """
        Executes a key press and release in the currently active OS window.
        Handles letters, numbers, and special control keys.
        """
        if not safety.is_active:
            logger.warning("Keystroke ignored: safety mode active.")
            return

        cfg_kb = settings.get("keyboard")
        cooldown = cfg_kb.get("selection_cooldown", 0.25)
        now = time.time()
        if now - self._last_type_time < cooldown:
            return
        self._last_type_time = now

        direct_input = cfg_kb.get("direct_system_input", True)

        try:
            # Special Keys Handling
            norm_key = key_label.upper()

            if norm_key == "SPACE":
                if direct_input:
                    self._kb.press(Key.space)
                    self._kb.release(Key.space)
                typed_char = " "
            elif norm_key == "ENTER":
                if direct_input:
                    self._kb.press(Key.enter)
                    self._kb.release(Key.enter)
                typed_char = "\n"
            elif norm_key == "BACKSPACE" or norm_key == "BACK":
                if direct_input:
                    self._kb.press(Key.backspace)
                    self._kb.release(Key.backspace)
                typed_char = "BACKSPACE"
            elif norm_key == "TAB":
                if direct_input:
                    self._kb.press(Key.tab)
                    self._kb.release(Key.tab)
                typed_char = "\t"
            elif norm_key == "ESC" or norm_key == "ESCAPE":
                if direct_input:
                    self._kb.press(Key.esc)
                    self._kb.release(Key.esc)
                typed_char = "ESC"
            elif norm_key == "DELETE" or norm_key == "DEL":
                if direct_input:
                    self._kb.press(Key.delete)
                    self._kb.release(Key.delete)
                typed_char = "DELETE"
            elif norm_key == "SHIFT":
                self.shift_active = not self.shift_active
                logger.debug(f"Shift toggled: {self.shift_active}")
                play_feedback_sound("click")
                self.key_typed.emit("SHIFT")
                return
            elif norm_key == "CAPS" or norm_key == "CAPS LOCK":
                self.caps_lock_active = not self.caps_lock_active
                logger.debug(f"Caps lock toggled: {self.caps_lock_active}")
                play_feedback_sound("click")
                self.key_typed.emit("CAPS")
                return
            elif norm_key == "CTRL":
                self.ctrl_active = not self.ctrl_active
                self.key_typed.emit("CTRL")
                return
            elif norm_key == "ALT":
                self.alt_active = not self.alt_active
                self.key_typed.emit("ALT")
                return
            elif norm_key in ("UP", "ARROW_UP"):
                if direct_input:
                    self._kb.press(Key.up)
                    self._kb.release(Key.up)
                typed_char = "UP"
            elif norm_key in ("DOWN", "ARROW_DOWN"):
                if direct_input:
                    self._kb.press(Key.down)
                    self._kb.release(Key.down)
                typed_char = "DOWN"
            elif norm_key in ("LEFT", "ARROW_LEFT"):
                if direct_input:
                    self._kb.press(Key.left)
                    self._kb.release(Key.left)
                typed_char = "LEFT"
            elif norm_key in ("RIGHT", "ARROW_RIGHT"):
                if direct_input:
                    self._kb.press(Key.right)
                    self._kb.release(Key.right)
                typed_char = "RIGHT"
            else:
                # Regular characters: calculate upper/lower case
                char = key_label
                if len(char) == 1:
                    is_upper = self.shift_active ^ self.caps_lock_active
                    char = char.upper() if is_upper else char.lower()
                    if direct_input:
                        self._kb.type(char)
                    typed_char = char
                else:
                    if direct_input:
                        self._kb.type(key_label)
                    typed_char = key_label

                # If shift was single-use, turn it off after typing character
                if self.shift_active:
                    self.shift_active = False

            play_feedback_sound("click")
            history.record_event("key", typed_char, 1)
            self.key_typed.emit(typed_char)
            logger.debug(f"Typed key: '{typed_char}'")

        except Exception as e:
            logger.error(f"Failed to send keystroke '{key_label}': {e}")

keyboard_ctrl = KeyboardController()

