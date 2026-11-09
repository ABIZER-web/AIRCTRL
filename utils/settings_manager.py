"""
AIRCTRL Settings Manager
Loads, validates, and persists user preferences and configuration in config.json.
"""
import os
import json
import threading
from typing import Any, Dict
from utils.logger import get_logger

logger = get_logger("SettingsManager")

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "app": {
        "theme": "dark",
        "start_minimized": False,
        "minimize_to_tray": False,
        "start_with_windows": False,
        "emergency_shortcut": "ctrl+shift+q",
        "sound_feedback": True,
        "auto_save": True
    },
    "mouse": {
        "enabled": True,
        "sensitivity": 1.3,
        "smoothness": 0.65,
        "movement_speed": 1.0,
        "acceleration": 1.1,
        "click_threshold": 0.055,
        "drag_hold_sec": 0.4,
        "double_click_interval": 0.4,
        "gesture_cooldown": 0.25,
        "active_area": [0.15, 0.15, 0.85, 0.85]
    },
    "camera": {
        "device_index": 0,
        "width": 640,
        "height": 480,
        "fps": 30,
        "detection_confidence": 0.5,
        "tracking_confidence": 0.5,
        "mirror": True
    },
    "audio": {
        "enabled": True,
        "device_index": -1,
        "clap_sensitivity": 0.7,
        "noise_floor": 0.02,
        "clap_timing_window": 1.2,
        "action_cooldown": 0.6,
        "clap_actions": {
            "1": "toggle_mouse",
            "2": "quick_launch",
            "3": "virtual_keyboard",
            "4": "emergency_pause"
        }
    },
    "gestures": {
        "cursor_move": True,
        "left_click": True,
        "drag_and_drop": True,
        "right_click": True,
        "double_click": True,
        "open_palm": True,
        "closed_fist": True,
        "menu_hold_time": 0.8
    },
    "keyboard": {
        "hover_duration": 0.4,
        "selection_cooldown": 0.25,
        "direct_system_input": True
    },
    "quick_launch": [
        {
            "id": "youtube",
            "name": "YouTube",
            "url": "https://www.youtube.com",
            "icon": "youtube",
            "shortcut": "Y",
            "pinned": True,
            "usage_count": 0,
            "last_opened": None
        },
        {
            "id": "googledocs",
            "name": "Google Docs",
            "url": "https://docs.google.com",
            "icon": "googledocs",
            "shortcut": "D",
            "pinned": True,
            "usage_count": 0,
            "last_opened": None
        },
        {
            "id": "chatgpt",
            "name": "ChatGPT",
            "url": "https://chatgpt.com",
            "icon": "chatgpt",
            "shortcut": "C",
            "pinned": True,
            "usage_count": 0,
            "last_opened": None
        },
        {
            "id": "claude",
            "name": "Claude",
            "url": "https://claude.ai",
            "icon": "claude",
            "shortcut": "A",
            "pinned": True,
            "usage_count": 0,
            "last_opened": None
        },
        {
            "id": "github",
            "name": "GitHub",
            "url": "https://github.com",
            "icon": "github",
            "shortcut": "G",
            "pinned": True,
            "usage_count": 0,
            "last_opened": None
        }
    ]
}


class SettingsManager:
    """Singleton settings manager with file synchronization."""
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SettingsManager, cls).__new__(cls)
                cls._instance._config = {}
                cls._instance.load()
            return cls._instance

    def load(self):
        """Loads configuration from JSON, merged with defaults."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    user_cfg = json.load(f)
                self._config = self._deep_merge(DEFAULT_CONFIG, user_cfg)
                logger.info("Loaded settings from config.json")
            else:
                self._config = dict(DEFAULT_CONFIG)
                self.save()
                logger.info("Created default config.json")
        except Exception as e:
            logger.error(f"Error loading config.json, using defaults: {e}")
            self._config = dict(DEFAULT_CONFIG)

    def _deep_merge(self, default: dict, override: dict) -> dict:
        result = dict(default)
        for k, v in override.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = self._deep_merge(result[k], v)
            else:
                result[k] = v
        return result

    def save(self):
        """Persists settings to config.json."""
        with self._lock:
            try:
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(self._config, f, indent=4)
                logger.debug("Saved settings to config.json")
            except Exception as e:
                logger.error(f"Failed to save config.json: {e}")

    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        with self._lock:
            sec = self._config.get(section, {})
            if key is None:
                return sec
            if isinstance(sec, dict):
                return sec.get(key, default)
            return default

    def set(self, section: str, key: str, value: Any, save_now: bool = True):
        with self._lock:
            if key is None:
                self._config[section] = value
            else:
                if section not in self._config or not isinstance(self._config[section], dict):
                    self._config[section] = {}
                self._config[section][key] = value
        if save_now:
            self.save()

    def get_all(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._config)

    def reset_to_defaults(self):
        with self._lock:
            self._config = dict(DEFAULT_CONFIG)
            self.save()
            logger.info("Configuration reset to defaults.")


# Global instance
settings = SettingsManager()
