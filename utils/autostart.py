"""
AIRCTRL Windows Autostart Manager
Configures automatic launch of AIRCTRL upon Windows user login
using the official HKCU Run Registry key and Startup folder fallback.
"""
import sys
import os
from utils.logger import get_logger
from utils.settings_manager import settings

logger = get_logger("Autostart")

RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_ENTRY_NAME = "AIRCTRL"

try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False


def get_launch_command() -> str:
    """
    Constructs the exact command string to launch AIRCTRL.
    Uses AIRCTRL.exe if frozen via PyInstaller, otherwise pythonw/python + main.py.
    """
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main_py = os.path.join(base_dir, "main.py")
    py_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(py_dir, "pythonw.exe")

    # Use pythonw (windowless) if available, otherwise python
    launcher_exe = pythonw if os.path.exists(pythonw) else sys.executable
    return f'"{launcher_exe}" "{main_py}"'


def get_startup_folder() -> str:
    """Returns the Windows Startup folder path for the current user."""
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        return os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
    return ""


def is_windows_autostart_active() -> bool:
    """
    Checks if AIRCTRL is currently configured to launch on Windows startup
    by inspecting the Windows Registry, the Startup folder, and config.json.
    """
    # 1. Check Registry
    if HAS_WINREG:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, REG_ENTRY_NAME)
                if val:
                    return True
        except (FileNotFoundError, OSError, PermissionError):
            pass

    # 2. Check Startup folder shortcut
    startup_dir = get_startup_folder()
    if startup_dir:
        bat_path = os.path.join(startup_dir, "AIRCTRL.bat")
        vbs_path = os.path.join(startup_dir, "AIRCTRL.vbs")
        if os.path.exists(bat_path) or os.path.exists(vbs_path):
            return True

    # 3. Check saved configuration
    return bool(settings.get("app", "start_with_windows", False))


def set_windows_autostart(enable: bool) -> tuple[bool, str]:
    """
    Enables or disables launching AIRCTRL on Windows startup.
    Updates Windows Registry, Startup folder fallback, and persists setting in config.json.
    """
    cmd = get_launch_command()
    success = False
    details = ""

    # Attempt Windows Registry configuration
    if HAS_WINREG:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_ALL_ACCESS) as key:
                if enable:
                    winreg.SetValueEx(key, REG_ENTRY_NAME, 0, winreg.REG_SZ, cmd)
                    logger.info(f"Registered Windows autostart command in HKCU Run: {cmd}")
                    details = "Registered in Windows Startup Registry"
                else:
                    try:
                        winreg.DeleteValue(key, REG_ENTRY_NAME)
                        logger.info("Removed Windows autostart entry from HKCU Run.")
                    except FileNotFoundError:
                        pass
                    details = "Removed from Windows Startup Registry"
                success = True
        except Exception as e:
            logger.warning(f"Could not modify Windows Registry for autostart: {e}")

    # Fallback to Startup folder if Registry failed or as auxiliary
    if not success:
        startup_dir = get_startup_folder()
        if startup_dir and os.path.exists(startup_dir):
            bat_path = os.path.join(startup_dir, "AIRCTRL.bat")
            try:
                if enable:
                    with open(bat_path, "w", encoding="utf-8") as f:
                        f.write(f"@echo off\r\nstart \"\" {cmd}\r\n")
                    logger.info(f"Created autostart batch file in Startup folder: {bat_path}")
                    details = "Created startup script in Windows Startup folder"
                    success = True
                else:
                    if os.path.exists(bat_path):
                        os.remove(bat_path)
                    details = "Removed startup script from Windows Startup folder"
                    success = True
            except Exception as e:
                logger.warning(f"Could not modify Startup folder: {e}")

    # Always persist user preference in config.json
    settings.set("app", "start_with_windows", enable)
    logger.info(f"Updated config.json start_with_windows: {enable}")

    if not details:
        details = "Preference saved to settings"
        success = True

    status_msg = f"AIRCTRL will {'now' if enable else 'no longer'} start automatically with Windows ({details})."
    return success, status_msg

