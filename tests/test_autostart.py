"""
Unit Tests for AIRCTRL Windows Autostart Manager
Tests launch command generation, startup path resolution, and autostart toggle behavior.
"""
import sys
import os
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.autostart import (
    get_launch_command, get_startup_folder, is_windows_autostart_active, set_windows_autostart
)
from utils.settings_manager import settings

class TestAutostartManager(unittest.TestCase):
    def setUp(self):
        self._initial_state = settings.get("app", "start_with_windows", False)

    def tearDown(self):
        # Restore original preference
        set_windows_autostart(self._initial_state)

    def test_launch_command_structure(self):
        """Test launch command contains valid executable and script paths."""
        cmd = get_launch_command()
        self.assertIsInstance(cmd, str)
        self.assertGreater(len(cmd), 5)
        # Should reference python, pythonw, or exe
        self.assertTrue("python" in cmd.lower() or ".exe" in cmd.lower())

    def test_startup_folder_resolution(self):
        """Test Windows user startup folder resolution."""
        folder = get_startup_folder()
        self.assertIsInstance(folder, str)
        if folder:
            self.assertIn("Startup", folder)

    def test_autostart_toggle_enable_disable(self):
        """Test enabling and disabling autostart updates config and returns status."""
        # Enable
        success, msg = set_windows_autostart(True)
        self.assertTrue(success)
        self.assertTrue(settings.get("app", "start_with_windows", False))
        self.assertIn("AIRCTRL will now start automatically", msg)

        # Disable
        success, msg = set_windows_autostart(False)
        self.assertTrue(success)
        self.assertFalse(settings.get("app", "start_with_windows", True))
        self.assertIn("no longer start automatically", msg)

if __name__ == "__main__":
    unittest.main()

