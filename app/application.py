"""
AIRCTRL Application Entry Wrapper
Handles Qt application lifecycle, high-DPI awareness, theme styling, and system tray integration.
"""
import sys
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from app.theme import get_theme_stylesheet
from app.main_window import MainWindow
from utils.settings_manager import settings
from utils.logger import get_logger

logger = get_logger("Application")

class AirCtrlApplication(QApplication):
    def __init__(self, argv):
        # Enable High-DPI scaling
        super().__init__(argv)
        self.setApplicationName("AIRCTRL")
        self.setApplicationDisplayName("AIRCTRL – AI Assistant")
        self.setOrganizationName("AIRCTRL Team")

        # Load Theme
        theme_name = settings.get("app", "theme", "dark")
        self.setStyleSheet(get_theme_stylesheet(theme_name))

        # Main Window
        self.main_window = MainWindow()

    def run(self) -> int:
        start_minimized = settings.get("app", "start_minimized", False)
        if start_minimized:
            self.main_window.showMinimized()
        else:
            self.main_window.show()
        logger.info("AIRCTRL GUI started successfully.")
        return self.exec()

