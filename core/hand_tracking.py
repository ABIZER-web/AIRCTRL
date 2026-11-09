"""
AIRCTRL Hand Tracking Module
Performs real-time 21-landmark hand detection using MediaPipe HandLandmarker.
Provides coordinate extraction, custom futuristic HUD landmark rendering, and finger geometry.
"""
import os
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from utils.logger import get_logger
from utils.settings_manager import settings

logger = get_logger("HandTracking")

# Model path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "assets", "models", "hand_landmarker.task")

# Standard MediaPipe hand landmark connections
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
    (0, 17)                                # Palm base
]

# Landmark indices
WRIST = 0
THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20


class HandData:
    """Encapsulates detected hand landmarks, normalized & pixel coordinates, and finger states."""
    def __init__(self, landmarks_norm: List[Tuple[float, float, float]], image_shape: Tuple[int, int], handedness: str = "Right"):
        self.landmarks_norm = landmarks_norm  # List of (x, y, z) 0.0-1.0
        self.handedness = handedness
        h, w = image_shape[:2]
        self.width = w
        self.height = h

        # Pixel coordinates
        self.landmarks_px: List[Tuple[int, int]] = [
            (int(lm[0] * w), int(lm[1] * h)) for lm in landmarks_norm
        ]

        # Finger tip positions
        self.index_tip_norm = landmarks_norm[INDEX_TIP][:2]
        self.thumb_tip_norm = landmarks_norm[THUMB_TIP][:2]
        self.middle_tip_norm = landmarks_norm[MIDDLE_TIP][:2]
        self.ring_tip_norm = landmarks_norm[RING_TIP][:2]
        self.pinky_tip_norm = landmarks_norm[PINKY_TIP][:2]

        self.index_tip_px = self.landmarks_px[INDEX_TIP]
        self.thumb_tip_px = self.landmarks_px[THUMB_TIP]
        self.middle_tip_px = self.landmarks_px[MIDDLE_TIP]
        self.ring_tip_px = self.landmarks_px[RING_TIP]
        self.pinky_tip_px = self.landmarks_px[PINKY_TIP]
        self.wrist_px = self.landmarks_px[WRIST]

        # Geometric calculations
        self._analyze_fingers()

    def _analyze_fingers(self):
        """Determines whether each finger is extended or curled."""
        # Index finger: TIP is higher (smaller y) than PIP
        self.is_index_extended = self.landmarks_norm[INDEX_TIP][1] < self.landmarks_norm[INDEX_PIP][1] - 0.02
        # Middle finger
        self.is_middle_extended = self.landmarks_norm[MIDDLE_TIP][1] < self.landmarks_norm[MIDDLE_PIP][1] - 0.02
        # Ring finger
        self.is_ring_extended = self.landmarks_norm[RING_TIP][1] < self.landmarks_norm[RING_PIP][1] - 0.02
        # Pinky finger
        self.is_pinky_extended = self.landmarks_norm[PINKY_TIP][1] < self.landmarks_norm[PINKY_PIP][1] - 0.02

        # Thumb: compare x or distance to MCP/IP depending on hand
        thumb_dist = np.hypot(
            self.landmarks_norm[THUMB_TIP][0] - self.landmarks_norm[INDEX_MCP][0],
            self.landmarks_norm[THUMB_TIP][1] - self.landmarks_norm[INDEX_MCP][1]
        )
        self.is_thumb_extended = thumb_dist > 0.08

        # Pinch distances (Normalized)
        self.thumb_index_dist = np.hypot(
            self.thumb_tip_norm[0] - self.index_tip_norm[0],
            self.thumb_tip_norm[1] - self.index_tip_norm[1]
        )
        self.index_middle_dist = np.hypot(
            self.index_tip_norm[0] - self.middle_tip_norm[0],
            self.index_tip_norm[1] - self.middle_tip_norm[1]
        )

        # Count total extended fingers
        self.extended_count = sum([
            self.is_thumb_extended,
            self.is_index_extended,
            self.is_middle_extended,
            self.is_ring_extended,
            self.is_pinky_extended
        ])


class HandTracker:
    """Wrapper around MediaPipe HandLandmarker."""
    def __init__(self):
        self.detector = None
        self._initialized = False

    def _init_detector(self):
        if self._initialized:
            return
        self._initialized = True
        if not os.path.exists(MODEL_PATH):
            logger.error(f"MediaPipe hand model not found at {MODEL_PATH}")
            return

        try:
            cfg = settings.get("camera")
            det_conf = cfg.get("detection_confidence", 0.5)
            track_conf = cfg.get("tracking_confidence", 0.5)

            base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE,
                num_hands=2,
                min_hand_detection_confidence=det_conf,
                min_hand_presence_confidence=det_conf,
                min_tracking_confidence=track_conf
            )
            self.detector = vision.HandLandmarker.create_from_options(options)
            logger.info("MediaPipe HandLandmarker initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to create MediaPipe HandLandmarker: {e}")
            self.detector = None

    def process_frame(self, frame_bgr: np.ndarray) -> Tuple[List[HandData], np.ndarray]:
        """
        Processes a BGR image frame, detects hand landmarks,
        and renders futuristic HUD overlays onto a copy of the image.
        """
        if not self._initialized:
            self._init_detector()

        output_frame = frame_bgr.copy()
        hands: List[HandData] = []

        if self.detector is None:
            return hands, output_frame

        h, w = frame_bgr.shape[:2]

        try:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            detection_result = self.detector.detect(mp_image)

            if detection_result and detection_result.hand_landmarks:
                for idx, hand_lms in enumerate(detection_result.hand_landmarks):
                    # Extract handedness if available
                    handedness_str = "Right"
                    if detection_result.handedness and idx < len(detection_result.handedness):
                        handedness_str = detection_result.handedness[idx][0].category_name

                    landmarks_norm = [(lm.x, lm.y, lm.z) for lm in hand_lms]
                    hand_data = HandData(landmarks_norm, (h, w), handedness=handedness_str)
                    hands.append(hand_data)

                    # Render futuristic HUD overlay for each hand
                    self._render_hand_hud(output_frame, hand_data)
        except Exception as e:
            logger.debug(f"Hand detection frame processing error: {e}")

        return hands, output_frame

    def _render_hand_hud(self, img: np.ndarray, hand: HandData):
        """Draws neon cyan/electric blue futuristic bones and glowing joints."""
        # Draw skeleton connections
        for start_idx, end_idx in HAND_CONNECTIONS:
            p1 = hand.landmarks_px[start_idx]
            p2 = hand.landmarks_px[end_idx]
            # Outer cyan glow
            cv2.line(img, p1, p2, (254, 242, 0), 3, cv2.LINE_AA)
            # Inner white/bright core
            cv2.line(img, p1, p2, (255, 255, 255), 1, cv2.LINE_AA)

        # Draw joints
        for idx, (px, py) in enumerate(hand.landmarks_px):
            if idx == INDEX_TIP:
                # Target cursor reticle on index tip
                cv2.circle(img, (px, py), 10, (0, 255, 255), -1)
                cv2.circle(img, (px, py), 16, (0, 200, 255), 2, cv2.LINE_AA)
                cv2.circle(img, (px, py), 22, (255, 242, 0), 1, cv2.LINE_AA)
            elif idx == THUMB_TIP:
                cv2.circle(img, (px, py), 8, (255, 100, 0), -1)
                cv2.circle(img, (px, py), 12, (255, 200, 100), 2, cv2.LINE_AA)
            elif idx in (MIDDLE_TIP, RING_TIP, PINKY_TIP):
                cv2.circle(img, (px, py), 6, (0, 220, 255), -1)
            else:
                cv2.circle(img, (px, py), 4, (180, 220, 255), -1)

        # Display Pinch Distance between Thumb and Index
        mid_x = int((hand.thumb_tip_px[0] + hand.index_tip_px[0]) / 2)
        mid_y = int((hand.thumb_tip_px[1] + hand.index_tip_px[1]) / 2)
        if hand.thumb_index_dist < 0.08:
            # Draw pinch connection line
            cv2.line(img, hand.thumb_tip_px, hand.index_tip_px, (0, 0, 255), 2, cv2.LINE_AA)
            cv2.circle(img, (mid_x, mid_y), 6, (0, 0, 255), -1)


hand_tracker = HandTracker()
