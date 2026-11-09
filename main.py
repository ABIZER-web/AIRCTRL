"""
AIRCTRL – AI-Powered Virtual Mouse, Keyboard & Clap-Controlled Desktop Assistant
Your Hands. Your Voice. Your Control.

Production Application Entry Point
"""
import sys
import os

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.logger import get_logger
from utils.settings_manager import settings
from database.database import db
from app.application import AirCtrlApplication

logger = get_logger("Main")

def main():
    logger.info("==================================================")
    logger.info("   Starting AIRCTRL Desktop AI Assistant v1.0.0   ")
    logger.info("   Your Hands. Your Voice. Your Control.         ")
    logger.info("==================================================")

    # Initialize settings and database
    settings.load()
    _ = db.get_connection()

    # Launch GUI Application
    app = AirCtrlApplication(sys.argv)
    sys.exit(app.run())

if __name__ == "__main__":
    main()

