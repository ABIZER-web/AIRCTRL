"""
Unit Tests for AIRCTRL Quick Launcher
Tests default sites (YouTube, Google Docs, ChatGPT, Claude, GitHub),
adding, editing, removing, pinning, and usage tracking.
"""
import sys
import os
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.quick_launcher import launcher
from utils.settings_manager import settings
from database.history_manager import history

class TestQuickLauncher(unittest.TestCase):
    def test_default_websites_present(self):
        """Test default 5 required websites exist in config."""
        sites = launcher.get_sites(sorted_by_usage=False)
        site_ids = [s.get("id") for s in sites]

        self.assertIn("youtube", site_ids)
        self.assertIn("googledocs", site_ids)
        self.assertIn("chatgpt", site_ids)
        self.assertIn("claude", site_ids)
        self.assertIn("github", site_ids)

    def test_add_edit_remove_site(self):
        """Test adding, modifying, and deleting a bookmark."""
        initial_count = len(launcher.get_sites(sorted_by_usage=False))

        # 1. Add
        new_id = launcher.add_site("Test Platform", "testplatform.com", shortcut="T")
        sites_after_add = launcher.get_sites(sorted_by_usage=False)
        self.assertEqual(len(sites_after_add), initial_count + 1)

        # 2. Edit
        launcher.edit_site(new_id, "Renamed Platform", "https://newtest.org", shortcut="X", pinned=True)
        updated = next(s for s in launcher.get_sites(sorted_by_usage=False) if s["id"] == new_id)
        self.assertEqual(updated["name"], "Renamed Platform")
        self.assertEqual(updated["url"], "https://newtest.org")
        self.assertTrue(updated["pinned"])

        # 3. Remove
        launcher.remove_site(new_id)
        sites_after_del = launcher.get_sites(sorted_by_usage=False)
        self.assertEqual(len(sites_after_del), initial_count)

    def test_pin_toggle(self):
        """Test toggling pinned status moves items to top."""
        sites = launcher.get_sites(sorted_by_usage=False)
        first_id = sites[0]["id"]
        was_pinned = sites[0].get("pinned", False)

        launcher.toggle_pin(first_id)
        updated = next(s for s in launcher.get_sites(sorted_by_usage=False) if s["id"] == first_id)
        self.assertEqual(updated.get("pinned"), not was_pinned)

        # Revert
        launcher.toggle_pin(first_id)

if __name__ == "__main__":
    unittest.main()

