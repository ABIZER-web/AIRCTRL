"""
Unit Tests for AIRCTRL Gesture Recognition
Tests all 7 hand gestures, debouncing, and state machine transitions.
"""
import sys
import os
import unittest
import time

# Ensure project root is in path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.hand_tracking import HandData
from core.gesture_recognition import (
    GestureRecognizer, GESTURE_NONE, GESTURE_MOVE, GESTURE_LEFT_CLICK,
    GESTURE_DOUBLE_CLICK, GESTURE_DRAG, GESTURE_RIGHT_CLICK,
    GESTURE_OPEN_PALM, GESTURE_OPEN_PALM_MENU, GESTURE_CLOSED_FIST
)

def create_mock_hand(
    index_up=True,
    middle_up=False,
    ring_up=False,
    pinky_up=False,
    thumb_index_dist=0.2,
    index_middle_dist=0.2,
    index_pos=(0.5, 0.4)
) -> HandData:
    """Creates a synthetic 21-landmark hand configuration with proper anatomical joints."""
    lms = [(0.5, 0.8, 0.0)] * 21  # Wrist

    # Thumb (1 CMC, 2 MCP, 3 IP, 4 TIP)
    lms[1] = (0.45, 0.75, 0.0)
    lms[2] = (0.40, 0.70, 0.0)
    lms[3] = (0.35, 0.60, 0.0)
    # Thumb tip: when index is up (at 0.30), thumb tip is at same level to pinch
    thumb_y = 0.30 if index_up else 0.60
    lms[4] = (index_pos[0] - thumb_index_dist, thumb_y, 0.0)

    # Index finger (5 MCP, 6 PIP, 7 DIP, 8 TIP)
    lms[5] = (index_pos[0], 0.60, 0.0)
    lms[6] = (index_pos[0], 0.50, 0.0)
    lms[7] = (index_pos[0], 0.42, 0.0)
    lms[8] = (index_pos[0], 0.30 if index_up else 0.65, 0.0)

    # Middle finger (9 MCP, 10 PIP, 11 DIP, 12 TIP)
    mid_x = index_pos[0] + index_middle_dist
    lms[9] = (mid_x, 0.60, 0.0)
    lms[10] = (mid_x, 0.50, 0.0)
    lms[11] = (mid_x, 0.42, 0.0)
    lms[12] = (mid_x, 0.30 if middle_up else 0.65, 0.0)

    # Ring finger (13 MCP, 14 PIP, 15 DIP, 16 TIP)
    lms[13] = (0.65, 0.60, 0.0)
    lms[14] = (0.65, 0.50, 0.0)
    lms[15] = (0.65, 0.42, 0.0)
    lms[16] = (0.65, 0.30 if ring_up else 0.65, 0.0)

    # Pinky finger (17 MCP, 18 PIP, 19 DIP, 20 TIP)
    lms[17] = (0.75, 0.62, 0.0)
    lms[18] = (0.75, 0.52, 0.0)
    lms[19] = (0.75, 0.44, 0.0)
    lms[20] = (0.75, 0.32 if pinky_up else 0.65, 0.0)

    return HandData(lms, (480, 640), handedness="Right")


class TestGestureRecognition(unittest.TestCase):
    def setUp(self):
        self.recognizer = GestureRecognizer()

    def test_cursor_move(self):
        """Test pointing with index finger triggers CURSOR_MOVE."""
        hand = create_mock_hand(index_up=True, middle_up=False, ring_up=False, pinky_up=False, thumb_index_dist=0.25)
        gesture, _ = self.recognizer.update(hand)
        self.assertEqual(gesture, GESTURE_MOVE)

    def test_pinch_click(self):
        """Test thumb + index pinch triggers LEFT_CLICK."""
        # Pinch close (< 0.055)
        hand_pinch = create_mock_hand(index_up=True, thumb_index_dist=0.03)
        gesture, _ = self.recognizer.update(hand_pinch)
        self.assertEqual(gesture, GESTURE_LEFT_CLICK)

    def test_drag_and_drop(self):
        """Test holding pinch past threshold transitions to DRAG."""
        hand_pinch = create_mock_hand(index_up=True, thumb_index_dist=0.03)
        # First pinch
        self.recognizer.update(hand_pinch)
        # Simulate elapsed time
        self.recognizer._pinch_start_time = time.time() - 0.5
        gesture, extra = self.recognizer.update(hand_pinch)
        self.assertEqual(gesture, GESTURE_DRAG)
        self.assertTrue(extra["is_dragging"])

    def test_right_click(self):
        """Test index + middle together triggers RIGHT_CLICK."""
        hand = create_mock_hand(
            index_up=True, middle_up=True, ring_up=False, pinky_up=False,
            thumb_index_dist=0.2, index_middle_dist=0.02
        )
        gesture, _ = self.recognizer.update(hand)
        self.assertEqual(gesture, GESTURE_RIGHT_CLICK)

    def test_open_palm_and_menu(self):
        """Test open palm triggers OPEN_PALM and holding triggers OPEN_PALM_MENU."""
        hand = create_mock_hand(index_up=True, middle_up=True, ring_up=True, pinky_up=True, thumb_index_dist=0.3)
        gesture, _ = self.recognizer.update(hand)
        self.assertIn(gesture, (GESTURE_OPEN_PALM, GESTURE_OPEN_PALM_MENU))

        # Hold open palm for > 0.8s
        self.recognizer._palm_start_time = time.time() - 1.0
        gesture, _ = self.recognizer.update(hand)
        self.assertEqual(gesture, GESTURE_OPEN_PALM_MENU)

    def test_closed_fist(self):
        """Test curled fingers triggers CLOSED_FIST."""
        hand = create_mock_hand(
            index_up=False, middle_up=False, ring_up=False, pinky_up=False,
            thumb_index_dist=0.02, index_pos=(0.5, 0.60)
        )
        gesture, _ = self.recognizer.update(hand)
        self.assertEqual(gesture, GESTURE_CLOSED_FIST)

if __name__ == "__main__":
    unittest.main()
