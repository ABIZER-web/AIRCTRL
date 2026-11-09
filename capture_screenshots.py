"""
AIRCTRL Automated Screenshot Capture Utility
Initializes the Qt application, renders every page with full futuristic styling,
and captures high-resolution screenshots for the documentation.
"""
import sys
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from app.application import AirCtrlApplication
from utils.settings_manager import settings
from database.database import db

PAGES = [
    (0, "dashboard.png", "Dashboard"),
    (1, "virtual_mouse.png", "Virtual Mouse"),
    (2, "virtual_keyboard.png", "Virtual Keyboard"),
    (3, "clap_settings.png", "Clap Controls"),
    (4, "quick_launch.png", "Quick Launch"),
    (5, "gesture_settings.png", "Gesture Settings"),
    (6, "camera_settings.png", "Camera & System Settings"),
    (7, "audio_settings.png", "Audio Settings"),
    (8, "analytics.png", "Activity History"),
    (9, "about.png", "About AIRCTRL")
]

def capture_all():
    settings.load()
    _ = db.get_connection()

    app = AirCtrlApplication(sys.argv)
    window = app.main_window
    window.resize(1280, 800)
    window.show()

    out_dir = os.path.join(BASE_DIR, "assets", "screenshots")
    os.makedirs(out_dir, exist_ok=True)

    # Let UI settle
    for _ in range(15):
        app.processEvents()
        time.sleep(0.04)

    for page_idx, filename, title in PAGES:
        window.sidebar.select_page(page_idx)
        # Process events for layout & drawing
        for _ in range(8):
            app.processEvents()
            time.sleep(0.03)

        save_path = os.path.join(out_dir, filename)
        pixmap = window.grab()
        pixmap.save(save_path, "PNG")
        print(f"[Captured] {title} -> {save_path}")

    # Capture Floating Menu
    window.floating_menu.show_menu()
    for _ in range(6):
        app.processEvents()
        time.sleep(0.03)

    menu_pixmap = window.floating_menu.grab()
    menu_path = os.path.join(out_dir, "floating_menu.png")
    menu_pixmap.save(menu_path, "PNG")
    print(f"[Captured] Floating Menu -> {menu_path}")
    window.floating_menu.hide_menu()

    # Clean shutdown
    window.close()
    app.processEvents()
    print("All screenshots captured successfully!")

if __name__ == "__main__":
    capture_all()
