# AIRCTRL – AI-Powered Virtual Mouse, Keyboard & Clap-Controlled Desktop Assistant

> **Your Hands. Your Voice. Your Control.**

AIRCTRL is a professional, production-grade Python desktop application for Windows that allows you to control your PC or laptop completely hands-free. Powered by real-time computer vision, MediaPipe hand landmark tracking, digital signal processing (DSP) acoustic clap recognition, and safe operating system automation, AIRCTRL transforms your webcam and microphone into an intelligent spatial controller.

---

## Key Features

1. **AI Virtual Mouse**:
   - Move the actual Windows mouse cursor with index finger tracking.
   - Anti-tremor **1-Euro Filter** and Exponential Moving Average (EMA) smoothing.
   - Configurable sensitivity, acceleration, and interactive **4-corner calibration**.
   - Left click (pinch), right click (index + middle fingers), double click (two rapid pinches), and drag & drop (pinch and hold).

2. **Full Virtual Keyboard**:
   - Complete on-screen QWERTY layout with numbers, symbols, Shift, Caps Lock, Space, Enter, Backspace, Esc, Del, and Arrow keys.
   - Real system typing into any active Windows application (Notepad, browser, text editors).
   - Typing preview buffer with clipboard copy and clear functions.

3. **DSP Clap Detection**:
   - Butterworth bandpass filtering (1.5 kHz – 4.5 kHz) and transient crest factor analysis to reject speech and background noise.
   - 1 Clap: Toggle virtual mouse ON/OFF.
   - 2 Claps: Open Quick Launch menu.
   - 3 Claps: Open Virtual Keyboard.
   - 4 Claps: Emergency Pause all virtual controls.

4. **Quick Website Launcher**:
   - Instant launch for **YouTube**, **Google Docs**, **ChatGPT**, **Claude**, and **GitHub**.
   - Add, edit, remove, and pin custom websites.
   - Automatic usage frequency tracking and local SQLite history.

5. **Floating Gesture Menu**:
   - Hold an Open Palm gesture for 0.8s to summon a sleek HUD control menu.

6. **Safety & Fail-Safe Mechanisms**:
   - Global emergency stop shortcut (`Ctrl + Shift + Q`).
   - Physical mouse and keyboard always retain overriding priority.
   - Automatic camera and microphone disconnect recovery with synthetic test mode.

7. **Windows Startup & Autostart Management**:
   - Option to automatically launch AIRCTRL upon Windows boot.
   - Toggleable from the **Camera & System Preferences** page.
   - Integrates with `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run` and the user's Startup folder.
   - Optional "Start Minimized" mode to launch quietly in the background.

---

## Technology Stack

- **Python**: 3.10 / 3.11 / 3.12 / 3.14 (64-bit)
- **Computer Vision**: OpenCV (`cv2`) & MediaPipe Tasks HandLandmarker (`hand_landmarker.task`)
- **Desktop GUI**: PySide6 (Qt for Python)
- **Automation**: Win32 API (`ctypes.windll.user32`), Pynput, PyAutoGUI
- **Audio DSP**: SoundDevice, SciPy (Butterworth bandpass filter) & NumPy
- **Persistence**: SQLite3 database (`airctrl.db`) & JSON settings (`config.json`)
- **Packaging**: PyInstaller (`airctrl.spec`)

---

## Installation & Setup on Windows

### Prerequisites
1. Windows 10 or Windows 11 (64-bit).
2. Python installed and added to system PATH ([python.org](https://www.python.org/)).
3. A built-in or USB webcam and microphone.

### Quick Automatic Setup
1. Clone or download the repository to your computer:
   ```cmd
   cd c:\Users\Lenovo\Desktop\AIRCTRL
   ```
2. Double-click **`setup.bat`** (or run in terminal):
   ```cmd
   setup.bat
   ```
   This will install all required Python packages and verify the MediaPipe model asset.

### Manual Setup
If you prefer setting up manually:
```cmd
pip install -r requirements.txt
```

---

## Running AIRCTRL

Double-click **`run_airctrl.bat`** or execute:
```cmd
python main.py
```

### Webcam & Microphone Permissions
- Ensure Windows Settings (`Settings > Privacy & Security > Camera / Microphone`) allows desktop apps to access the camera and microphone.
- If no webcam is connected, AIRCTRL automatically enters **Virtual Test Feed Mode** with an animated hand HUD so all features and gestures remain fully functional and testable.

---

## Hand Gesture Reference

| Gesture | Hand Pose | Windows Action |
|---------|-----------|----------------|
| **Cursor Move** | Index finger pointing up | Smooth cursor movement across screen |
| **Left Click** | Thumb + Index finger pinch | Left mouse click |
| **Double Click** | Two quick pinches in succession | Double mouse click |
| **Drag & Drop** | Thumb + Index pinch held > 0.35s | Holds left mouse button down for dragging |
| **Right Click** | Index + Middle fingers together | Right mouse click |
| **Floating Menu** | Open palm held for 0.8s | Opens floating HUD navigation menu |
| **Safety Stop** | Closed fist | Temporarily pauses cursor motion |

---

## Acoustic Clap Actions

- **1 Clap**: Toggle virtual mouse control ON / OFF.
- **2 Claps**: Open the Quick Launch menu.
- **3 Claps**: Open the Virtual Keyboard.
- **4 Claps**: Emergency stop / halt all automation immediately.
- **Emergency Shortcut**: Press **`Ctrl + Shift + Q`** anywhere in Windows.

---

## Running Unit & Integration Tests

Run the full test suite from the project root:

```cmd
python -m unittest discover tests/
```

Individual test modules:
```cmd
python tests/test_gestures.py
python tests/test_mouse.py
python tests/test_clap.py
python tests/test_launcher.py
python tests/test_integration.py
```

See [TESTING.md](file:///c:/Users/Lenovo/Desktop/AIRCTRL/TESTING.md) for full test reports.

---

## Building Standalone Windows Executable

To package AIRCTRL into a standalone `.exe`:

1. Run the build script:
   ```cmd
   build_exe.bat
   ```
2. The standalone binary distribution will be generated in:
   ```
   dist\AIRCTRL\AIRCTRL.exe
   ```

---

## Project Structure

```
AIRCTRL/
│
├── main.py                  # Application entry point
├── requirements.txt         # Package dependencies
├── config.json              # Persistent user preferences
├── airctrl.db               # Local SQLite activity database
├── airctrl.spec             # PyInstaller build specification
├── setup.bat                # Automated Windows environment setup
├── run_airctrl.bat          # Desktop launch batch script
├── build_exe.bat            # Executable packaging script
├── README.md                # Documentation & User Guide
├── TESTING.md               # Test verification matrix
├── .gitignore
│
├── assets/
│   ├── icons/               # Vector & graphic UI icons
│   ├── images/              # Graphic assets
│   ├── sounds/              # Audio feedback tones
│   └── models/
│       └── hand_landmarker.task  # MediaPipe 21-landmark neural model
│
├── app/
│   ├── __init__.py
│   ├── application.py       # Qt application manager & DPI configuration
│   ├── main_window.py       # Core QMainWindow coordinator
│   ├── navigation.py        # 10-Item Sidebar navigation
│   └── theme.py             # Dark & Light futuristic UI stylesheets
│
├── core/
│   ├── camera_manager.py    # Asynchronous camera thread & synthetic fallback
│   ├── hand_tracking.py     # MediaPipe 21-landmark detector & HUD renderer
│   ├── gesture_recognition.py # State machine for 7 hand gestures
│   ├── mouse_controller.py  # Win32 OS mouse cursor & click automation
│   ├── keyboard_controller.py # Real OS keystroke injection & debouncer
│   ├── clap_detection.py    # SciPy Butterworth DSP clap recognition
│   ├── quick_launcher.py    # Browser bookmark manager & URL opener
│   ├── calibration.py       # 4-corner screen active area calibration
│   └── safety_manager.py    # Global hotkey listener & emergency halt
│
├── ui/
│   ├── dashboard.py         # Main dashboard with live preview & cards
│   ├── virtual_mouse.py     # Mouse sensitivity & calibration wizard
│   ├── virtual_keyboard.py  # Full QWERTY on-screen keyboard
│   ├── clap_settings.py     # Live audio meter & clap action mapping
│   ├── quick_launch.py      # Bookmarks (YouTube, Google Docs, AI tools)
│   ├── gesture_settings.py  # Gesture enable/disable matrix & timings
│   ├── camera_settings.py   # Webcam device & resolution configuration
│   ├── audio_settings.py    # Microphone device & sound feedback settings
│   ├── analytics.py         # Interactive usage charts & audit log table
│   ├── about.py             # About AIRCTRL & full user guide
│   └── components/
│       ├── webcam_widget.py # Video HUD preview widget
│       ├── floating_menu.py # Floating gesture HUD overlay
│       ├── audio_meter.py   # Glowing LED audio level bar
│       └── stat_card.py     # Modern KPI metric card
│
├── database/
│   ├── database.py          # SQLite connection & schema initialization
│   └── history_manager.py   # Audit log & daily aggregation API
│
├── utils/
│   ├── autostart.py         # Windows Startup Registry & autostart manager
│   ├── settings_manager.py  # Thread-safe JSON settings manager
│   ├── logger.py            # Rotating file & console logging
│   └── helpers.py           # 1-Euro & EMA filters, math & sound helpers
│
└── tests/
    ├── test_gestures.py     # 7 Gestures unit tests
    ├── test_mouse.py        # Mouse positioning & filters tests
    ├── test_clap.py         # Audio DSP & clap tests
    ├── test_launcher.py     # Quick launch CRUD tests
    ├── test_autostart.py    # Windows autostart unit tests
    └── test_integration.py  # 13 Required scenario integration tests
```

