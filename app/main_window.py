"""
AIRCTRL Main Application Window
Coordinates GUI views, background worker threads (Camera, Hand Tracking, Clap Detection),
gesture state dispatching, and safety fail-safes.
"""
import time
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QMessageBox
from PySide6.QtCore import Qt, QTimer

from app.navigation import SidebarNav
from app.theme import get_theme_stylesheet
from ui.dashboard import DashboardPage
from ui.virtual_mouse import VirtualMousePage
from ui.virtual_keyboard import VirtualKeyboardPage
from ui.clap_settings import ClapSettingsPage
from ui.quick_launch import QuickLaunchPage
from ui.gesture_settings import GestureSettingsPage
from ui.camera_settings import CameraSettingsPage
from ui.audio_settings import AudioSettingsPage
from ui.analytics import AnalyticsPage
from ui.about import AboutPage
from ui.components.floating_menu import FloatingGestureMenu

from core.camera_manager import camera_mgr
from core.hand_tracking import hand_tracker
from core.gesture_recognition import (
    gesture_recognizer, GESTURE_MOVE, GESTURE_LEFT_CLICK, GESTURE_DOUBLE_CLICK,
    GESTURE_DRAG, GESTURE_RIGHT_CLICK, GESTURE_OPEN_PALM_MENU
)
from core.mouse_controller import mouse_ctrl
from core.calibration import calibration_mgr
from core.clap_detection import clap_mgr
from core.safety_manager import safety
from core.quick_launcher import launcher
from utils.settings_manager import settings
from utils.logger import get_logger

logger = get_logger("MainWindow")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AIRCTRL – AI-Powered Virtual Mouse, Keyboard & Assistant")
        self.setMinimumSize(1100, 720)
        self.resize(1200, 780)

        # Main Central Container
        central_widget = QWidget(self)
        central_widget.setObjectName("MainContainer")
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar Navigation
        self.sidebar = SidebarNav(self)
        self.sidebar.page_changed.connect(self._on_navigate)
        self.sidebar.emergency_clicked.connect(self._on_emergency_toggle)
        main_layout.addWidget(self.sidebar)

        # Pages Stack
        self.pages_stack = QStackedWidget(self)

        self.page_dashboard = DashboardPage(self)
        self.page_mouse = VirtualMousePage(self)
        self.page_keyboard = VirtualKeyboardPage(self)
        self.page_clap = ClapSettingsPage(self)
        self.page_quick_launch = QuickLaunchPage(self)
        self.page_gestures = GestureSettingsPage(self)
        self.page_camera = CameraSettingsPage(self)
        self.page_audio = AudioSettingsPage(self)
        self.page_analytics = AnalyticsPage(self)
        self.page_about = AboutPage(self)

        self.pages_stack.addWidget(self.page_dashboard)      # 0
        self.pages_stack.addWidget(self.page_mouse)          # 1
        self.pages_stack.addWidget(self.page_keyboard)       # 2
        self.pages_stack.addWidget(self.page_clap)           # 3
        self.pages_stack.addWidget(self.page_quick_launch)   # 4
        self.pages_stack.addWidget(self.page_gestures)       # 5
        self.pages_stack.addWidget(self.page_camera)         # 6
        self.pages_stack.addWidget(self.page_audio)          # 7
        self.pages_stack.addWidget(self.page_analytics)      # 8
        self.pages_stack.addWidget(self.page_about)          # 9

        main_layout.addWidget(self.pages_stack, stretch=1)

        # Floating Gesture Menu
        self.floating_menu = FloatingGestureMenu(self)
        self.floating_menu.option_selected.connect(self._on_floating_menu_action)

        # Inter-page & Controller Signals
        self.page_dashboard.start_all_requested.connect(self._start_all_workers)
        self.page_dashboard.stop_all_requested.connect(self._stop_all_workers)
        self.page_dashboard.quick_launch_requested.connect(lambda sid: launcher.launch(sid))

        self.page_camera.camera_reconfigured.connect(self._restart_camera)
        self.page_audio.audio_reconfigured.connect(self._restart_audio)

        gesture_recognizer.gesture_detected.connect(self._on_gesture_event)
        safety.emergency_stopped.connect(self._on_emergency_state_changed)
        safety.paused_state_changed.connect(self._on_pause_state_changed)

        # Start Camera and Clap detection background threads
        self._start_all_workers()

    def _start_all_workers(self):
        """Starts real-time asynchronous camera capture and acoustic clap listener."""
        logger.info("Initializing background AI services...")
        safety.start_hotkey_listener()
        # 1. Camera Worker
        cam_worker = camera_mgr.start()
        if cam_worker:
            cam_worker.frame_ready.connect(self._on_camera_frame)
            cam_worker.status_changed.connect(self.page_dashboard.update_camera_status)

        # 2. Clap Detector Worker
        clap_worker = clap_mgr.start()
        if clap_worker:
            clap_worker.clap_detected.connect(self._on_clap_detected)
            clap_worker.level_updated.connect(self.page_clap.audio_meter.set_level)
            clap_worker.status_changed.connect(self.page_dashboard.update_audio_status)

    def _stop_all_workers(self):
        safety.set_pause(True)
        mouse_ctrl.reset_filters()

    def _restart_camera(self):
        cam_worker = camera_mgr.start()
        if cam_worker:
            cam_worker.frame_ready.connect(self._on_camera_frame)
            cam_worker.status_changed.connect(self.page_dashboard.update_camera_status)

    def _restart_audio(self):
        clap_worker = clap_mgr.start()
        if clap_worker:
            clap_worker.clap_detected.connect(self._on_clap_detected)
            clap_worker.level_updated.connect(self.page_clap.audio_meter.set_level)
            clap_worker.status_changed.connect(self.page_dashboard.update_audio_status)

    def _on_camera_frame(self, frame):
        """Processes each incoming camera frame."""
        # 1. AI Hand Tracking Landmark Extraction
        hands, annotated_frame = hand_tracker.process_frame(frame)
        primary_hand = hands[0] if hands else None

        # 2. Gesture State Machine
        gesture_name, extra_info = gesture_recognizer.update(primary_hand)

        # 3. Check 4-Corner Calibration if active
        if calibration_mgr.is_calibrating and primary_hand:
            norm_x, norm_y = primary_hand.index_tip_norm
            calibration_mgr.update_tracking_point(norm_x, norm_y)

        # 4. Mouse Motion Execution
        if primary_hand and safety.is_active:
            norm_x, norm_y = primary_hand.index_tip_norm
            if gesture_name in (GESTURE_MOVE, GESTURE_DRAG):
                mouse_ctrl.move_to(norm_x, norm_y)

        # 5. Update GUI Video Preview & Dashboard
        fps = camera_mgr.worker.target_fps if camera_mgr.worker else 30.0
        self.page_dashboard.preview_widget.update_frame(
            annotated_frame,
            gesture_name=gesture_name,
            fps=fps
        )
        self.page_dashboard.update_gesture_status(gesture_name)

    def _on_gesture_event(self, gesture_name: str, extra_data: dict):
        """Handles discrete gesture triggers."""
        if not safety.is_active:
            return

        if gesture_name == GESTURE_LEFT_CLICK:
            mouse_ctrl.left_click()
        elif gesture_name == GESTURE_DOUBLE_CLICK:
            mouse_ctrl.double_click()
        elif gesture_name == GESTURE_RIGHT_CLICK:
            mouse_ctrl.right_click()
        elif gesture_name == "DRAG_START":
            mouse_ctrl.start_drag()
        elif gesture_name == "DRAG_END":
            mouse_ctrl.end_drag()
        elif gesture_name == GESTURE_OPEN_PALM_MENU:
            # Position floating menu near center of screen
            self.floating_menu.move(
                self.x() + (self.width() - self.floating_menu.width()) // 2,
                self.y() + (self.height() - self.floating_menu.height()) // 2
            )
            self.floating_menu.show_menu()

    def _on_clap_detected(self, count: int):
        """Executes assigned action for clap sequences."""
        self.page_clap.on_clap_detected(count)

        cfg_audio = settings.get("audio")
        actions_map = cfg_audio.get("clap_actions", {})
        action = actions_map.get(str(count), "none")

        logger.info(f"Executing action for {count} claps: '{action}'")

        if action == "toggle_mouse":
            safety.toggle_pause()
        elif action == "quick_launch":
            self.sidebar.select_page(4)
        elif action == "virtual_keyboard":
            self.sidebar.select_page(2)
        elif action == "emergency_pause":
            safety.trigger_emergency_stop()

    def _on_floating_menu_action(self, action: str):
        if action == "nav_mouse":
            self.sidebar.select_page(1)
        elif action == "nav_keyboard":
            self.sidebar.select_page(2)
        elif action == "nav_quick_launch":
            self.sidebar.select_page(4)
        elif action == "pause_all":
            safety.toggle_pause()
        elif action == "nav_settings":
            self.sidebar.select_page(5)

    def _on_navigate(self, page_idx: int):
        self.pages_stack.setCurrentIndex(page_idx)
        if page_idx == 8:
            self.page_analytics.refresh_data()

    def _on_emergency_toggle(self):
        safety.toggle_emergency_stop()

    def _on_emergency_state_changed(self, is_stopped: bool):
        if is_stopped:
            self.sidebar.btn_emergency.setText("⚡  RESUME CONTROLS")
            self.sidebar.btn_emergency.setStyleSheet("background: #00ff88; color: #000; font-weight: 800;")
        else:
            self.sidebar.btn_emergency.setText("🛑  EMERGENCY STOP")
            self.sidebar.btn_emergency.setStyleSheet("")

    def _on_pause_state_changed(self, is_paused: bool):
        mouse_ctrl.reset_filters()

    def closeEvent(self, event):
        """Clean shutdown of all threads and hooks on app exit."""
        logger.info("Closing application. Shutting down worker threads...")
        mouse_ctrl.reset_filters()
        camera_mgr.stop()
        clap_mgr.stop()
        safety.cleanup()
        event.accept()
