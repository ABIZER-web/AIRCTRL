"""
Unit Tests for AIRCTRL Mouse Controller & Coordinate Math
Tests real cursor positioning, coordinate mapping, filters, clicks, and safety pausing.
"""
import sys
import os
import unittest
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.helpers import get_screen_resolution, map_coordinates, OneEuroFilter, EMAFilter
from core.mouse_controller import mouse_ctrl
from core.safety_manager import safety

class TestMouseController(unittest.TestCase):
    def setUp(self):
        mouse_ctrl.reset_filters()
        safety.resume_from_emergency()
        safety.set_pause(False)

    def test_screen_resolution(self):
        """Test physical screen detection returns valid dimensions."""
        w, h = get_screen_resolution()
        self.assertGreater(w, 0)
        self.assertGreater(h, 0)

    def test_coordinate_mapping(self):
        """Test normalized camera coordinates map correctly within calibration bounds."""
        sw, sh = 1920, 1080
        calib_box = (0.15, 0.15, 0.85, 0.85)

        # Center maps to center
        cx, cy = map_coordinates(0.5, 0.5, sw, sh, calib_box=calib_box, sensitivity=1.0)
        self.assertAlmostEqual(cx, sw // 2, delta=10)
        self.assertAlmostEqual(cy, sh // 2, delta=10)

        # Top-left maps near (0, 0)
        tx, ty = map_coordinates(0.15, 0.15, sw, sh, calib_box=calib_box, sensitivity=1.0)
        self.assertLessEqual(tx, 50)
        self.assertLessEqual(ty, 50)

        # Bottom-right maps near (sw, sh)
        bx, by = map_coordinates(0.85, 0.85, sw, sh, calib_box=calib_box, sensitivity=1.0)
        self.assertGreaterEqual(bx, sw - 50)
        self.assertGreaterEqual(by, sh - 50)

    def test_filters(self):
        """Test EMA and 1-Euro smoothing filters stabilize jitter."""
        ema = EMAFilter(alpha=0.5)
        p1 = ema.update(100.0, 100.0)
        self.assertEqual(p1, (100.0, 100.0))
        p2 = ema.update(110.0, 110.0)
        self.assertEqual(p2, (105.0, 105.0))

        one_euro = OneEuroFilter(min_cutoff=1.0, beta=0.007)
        fx, fy = one_euro.update(500.0, 500.0)
        self.assertEqual((fx, fy), (500.0, 500.0))

    def test_mouse_actions(self):
        """Test left, right, double click, and drag state toggle."""
        init_clicks = mouse_ctrl.total_clicks

        mouse_ctrl.left_click()
        self.assertEqual(mouse_ctrl.total_clicks, init_clicks + 1)

        mouse_ctrl.right_click()
        self.assertEqual(mouse_ctrl.total_clicks, init_clicks + 2)

        mouse_ctrl.double_click()
        self.assertEqual(mouse_ctrl.total_clicks, init_clicks + 4)

        # Test Drag
        self.assertFalse(mouse_ctrl.is_dragging)
        mouse_ctrl.start_drag()
        self.assertTrue(mouse_ctrl.is_dragging)
        mouse_ctrl.end_drag()
        self.assertFalse(mouse_ctrl.is_dragging)

    def test_safety_blocking(self):
        """Test safety pause prevents mouse click actions."""
        init_clicks = mouse_ctrl.total_clicks
        safety.trigger_emergency_stop()

        mouse_ctrl.left_click()
        self.assertEqual(mouse_ctrl.total_clicks, init_clicks)

        safety.resume_from_emergency()
        mouse_ctrl.left_click()
        self.assertEqual(mouse_ctrl.total_clicks, init_clicks + 1)

if __name__ == "__main__":
    unittest.main()

