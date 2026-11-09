"""
AIRCTRL Safety Manager
Coordinates emergency stop, pause/resume, and fail-safe protections across all subsystems.
"""
import threading
from PySide6.QtCore import QObject, Signal
from utils.logger import get_logger
from utils.helpers import play_feedback_sound
from utils.settings_manager import settings

logger = get_logger("SafetyManager")

class SafetyManager(QObject):
    """
    Central safety coordinator.
    Ensures that physical user control always takes precedence and provides
    instant pause/emergency-stop mechanisms.
    """
    emergency_stopped = Signal(bool)  # True if emergency paused
    paused_state_changed = Signal(bool)  # True if paused

    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SafetyManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        super().__init__()
        self._initialized = True
        self._is_emergency_paused = False
        self._is_user_paused = False
        self._hotkey_listener = None

    def start_hotkey_listener(self):
        """Starts a background global hotkey listener using pynput."""
        if self._hotkey_listener is not None:
            return
        try:
            from pynput import keyboard
            def on_activate():
                logger.warning("Global emergency shortcut triggered!")
                self.trigger_emergency_stop()

            hotkey_str = "<ctrl>+<shift>+q"
            self._hotkey_listener = keyboard.GlobalHotKeys({
                hotkey_str: on_activate
            })
            self._hotkey_listener.daemon = True
            self._hotkey_listener.start()
            logger.info(f"Registered global emergency hotkey: {hotkey_str}")
        except Exception as e:
            logger.warning(f"Failed to initialize global emergency hotkey listener: {e}")

    @property
    def is_active(self) -> bool:
        """Returns True if automation is currently permitted to run."""
        return not (self._is_emergency_paused or self._is_user_paused)

    @property
    def is_emergency_paused(self) -> bool:
        return self._is_emergency_paused

    @property
    def is_user_paused(self) -> bool:
        return self._is_user_paused

    def trigger_emergency_stop(self):
        """Halts all automation immediately."""
        self._is_emergency_paused = True
        play_feedback_sound("emergency")
        logger.warning("EMERGENCY STOP ACTIVATED! All virtual controls halted.")
        self.emergency_stopped.emit(True)
        self.paused_state_changed.emit(True)

    def resume_from_emergency(self):
        """Resumes automation after an emergency stop."""
        self._is_emergency_paused = False
        logger.info("Resumed from emergency stop.")
        self.emergency_stopped.emit(False)
        self.paused_state_changed.emit(self._is_user_paused)

    def toggle_emergency_stop(self):
        if self._is_emergency_paused:
            self.resume_from_emergency()
        else:
            self.trigger_emergency_stop()

    def toggle_pause(self):
        """Toggles user-level pause."""
        self._is_user_paused = not self._is_user_paused
        logger.info(f"User pause toggled: {self._is_user_paused}")
        self.paused_state_changed.emit(self._is_user_paused or self._is_emergency_paused)

    def set_pause(self, paused: bool):
        self._is_user_paused = paused
        self.paused_state_changed.emit(self._is_user_paused or self._is_emergency_paused)

    def cleanup(self):
        if self._hotkey_listener and self._hotkey_listener.is_alive():
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass

safety = SafetyManager()
