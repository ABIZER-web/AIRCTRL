"""
AIRCTRL Quick Launcher Module
Manages website bookmarks, launches URLs in the default web browser,
tracks open counts and timestamps in SQLite, and synchronizes with config.json.
"""
import time
import webbrowser
import datetime
from typing import List, Dict, Any, Optional
from PySide6.QtCore import QObject, Signal

from utils.logger import get_logger
from utils.settings_manager import settings
from utils.helpers import play_feedback_sound
from database.history_manager import history

logger = get_logger("QuickLauncher")

class QuickLauncher(QObject):
    """Manages Quick Launch websites and launches them in default browser."""
    website_launched = Signal(str, str)  # name, url
    sites_updated = Signal()

    def __init__(self):
        super().__init__()

    def get_sites(self, sorted_by_usage: bool = True) -> List[Dict[str, Any]]:
        """Returns the list of websites, pinned first, then sorted by usage count."""
        raw_sites = settings.get("quick_launch") or []
        sites = list(raw_sites)
        if sorted_by_usage:
            # Pinned items first, then descending usage_count
            sites.sort(key=lambda x: (not x.get("pinned", False), -x.get("usage_count", 0)))
        return sites

    def launch(self, site_id: str) -> bool:
        """Launches a website by ID in the default browser."""
        sites = self.get_sites(sorted_by_usage=False)
        target = None
        for s in sites:
            if s.get("id") == site_id:
                target = s
                break

        if not target:
            logger.warning(f"Site ID '{site_id}' not found.")
            return False

        url = target.get("url", "")
        name = target.get("name", "Website")

        try:
            logger.info(f"Opening {name} -> {url}")
            webbrowser.open_new_tab(url)
            play_feedback_sound("launch")

            # Update count and timestamp
            target["usage_count"] = target.get("usage_count", 0) + 1
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            target["last_opened"] = now_str

            # Persist updated sites to config
            raw_sites = settings.get("quick_launch") or []
            for s in raw_sites:
                if s.get("id") == site_id:
                    s["usage_count"] = target["usage_count"]
                    s["last_opened"] = target["last_opened"]
                    break
            settings.set("quick_launch", None, raw_sites, save_now=True)

            # Record in SQLite database
            history.record_website_open(site_id, name, url)

            self.website_launched.emit(name, url)
            self.sites_updated.emit()
            return True
        except Exception as e:
            logger.error(f"Failed to launch website {name}: {e}")
            return False

    def add_site(self, name: str, url: str, icon: str = "web", shortcut: str = "", pinned: bool = False) -> str:
        """Adds a new customizable website."""
        import uuid
        site_id = f"site_{uuid.uuid4().hex[:8]}"

        # Ensure scheme
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url

        new_entry = {
            "id": site_id,
            "name": name.strip(),
            "url": url.strip(),
            "icon": icon,
            "shortcut": shortcut.strip().upper(),
            "pinned": pinned,
            "usage_count": 0,
            "last_opened": None
        }

        sites = list(settings.get("quick_launch") or [])
        sites.append(new_entry)
        settings.set("quick_launch", None, sites, save_now=True)
        logger.info(f"Added new site: {name} ({url})")
        self.sites_updated.emit()
        return site_id

    def edit_site(self, site_id: str, name: str, url: str, shortcut: str = "", pinned: bool = False):
        """Edits an existing site."""
        sites = list(settings.get("quick_launch") or [])
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url

        for s in sites:
            if s.get("id") == site_id:
                s["name"] = name.strip()
                s["url"] = url.strip()
                s["shortcut"] = shortcut.strip().upper()
                s["pinned"] = pinned
                break

        settings.set("quick_launch", None, sites, save_now=True)
        logger.info(f"Updated site: {site_id}")
        self.sites_updated.emit()

    def remove_site(self, site_id: str):
        """Removes a website by ID."""
        sites = list(settings.get("quick_launch") or [])
        filtered = [s for s in sites if s.get("id") != site_id]
        settings.set("quick_launch", None, filtered, save_now=True)
        logger.info(f"Removed site: {site_id}")
        self.sites_updated.emit()

    def toggle_pin(self, site_id: str):
        """Toggles pinned status."""
        sites = list(settings.get("quick_launch") or [])
        for s in sites:
            if s.get("id") == site_id:
                s["pinned"] = not s.get("pinned", False)
                break
        settings.set("quick_launch", None, sites, save_now=True)
        self.sites_updated.emit()

launcher = QuickLauncher()
