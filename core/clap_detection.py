"""
AIRCTRL Real-Time Clap Detection Module
Captures microphone audio via SoundDevice, applies SciPy bandpass filtering and
transient acoustic analysis to detect distinctive hand claps (1, 2, 3, or 4 claps)
while rejecting speech and ambient background noise.
"""
import time
import threading
import numpy as np
from scipy import signal
import sounddevice as sd
from PySide6.QtCore import QThread, Signal

from utils.logger import get_logger
from utils.settings_manager import settings
from utils.helpers import play_feedback_sound
from database.history_manager import history

logger = get_logger("ClapDetection")

class ClapDetectorWorker(QThread):
    """Background worker processing audio buffers for clap detection."""
    clap_detected = Signal(int)         # clap count (1, 2, 3, 4)
    level_updated = Signal(float)       # normalized level 0.0 to 1.0 for UI audio meter
    status_changed = Signal(bool, str)  # is_active, message

    def __init__(self, sample_rate: int = 44100, block_size: int = 2048):
        super().__init__()
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.running = False
        self._stream = None

        # Filter design (Bandpass: 1500 Hz to 4500 Hz for clap transient isolation)
        nyquist = sample_rate * 0.5
        low = 1500.0 / nyquist
        high = min(0.95, 4500.0 / nyquist)
        self.b_filter, self.a_filter = signal.butter(3, [low, high], btype='band')

        # Background noise tracking
        self.noise_floor = 0.02
        self.noise_alpha = 0.05

        # Clap sequence state machine
        self._clap_count = 0
        self._last_clap_time = 0.0
        self._cooldown_until = 0.0
        self._lock = threading.Lock()

    def run(self):
        self.running = True
        logger.info("Starting audio clap detection worker...")

        cfg_audio = settings.get("audio")
        device_idx = cfg_audio.get("device_index", -1)
        if device_idx < 0:
            device_idx = None  # default system input

        try:
            self._stream = sd.InputStream(
                device=device_idx,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                callback=self._audio_callback
            )
            self._stream.start()
            self.status_changed.emit(True, "Microphone Active (Listening for claps)")
            logger.info("SoundDevice audio stream started.")
        except Exception as e:
            logger.error(f"Failed to open microphone: {e}")
            self.status_changed.emit(False, f"Microphone Error: {str(e)[:40]}")
            self.running = False
            return

        # Sequence evaluator loop
        while self.running:
            now = time.time()
            with self._lock:
                if self._clap_count > 0:
                    cfg_audio = settings.get("audio")
                    timing_window = cfg_audio.get("clap_timing_window", 1.0)
                    time_since_last = now - self._last_clap_time

                    # If sequence has finished waiting or reached max 4 claps
                    if self._clap_count >= 4 or (time_since_last >= 0.75 and self._clap_count > 0):
                        detected_claps = min(4, self._clap_count)
                        cooldown_sec = cfg_audio.get("action_cooldown", 0.6)
                        self._cooldown_until = now + cooldown_sec
                        self._clap_count = 0

                        logger.info(f"CLAP SEQUENCE CONFIRMED: {detected_claps} claps!")
                        play_feedback_sound("clap")
                        history.record_event("clap", f"{detected_claps} Claps", detected_claps)
                        self.clap_detected.emit(detected_claps)

            time.sleep(0.04)

        self._cleanup()
        logger.info("Clap detector worker stopped.")

    def _audio_callback(self, indata, frames, time_info, status):
        """Processes each audio chunk."""
        if not self.running:
            return

        audio_data = indata[:, 0]
        peak = float(np.max(np.abs(audio_data)))
        rms = float(np.sqrt(np.mean(audio_data**2)))

        # Update live audio level for meter (normalized 0.0 - 1.0)
        norm_level = min(1.0, peak * 2.5)
        self.level_updated.emit(norm_level)

        now = time.time()
        if now < self._cooldown_until:
            return

        # Update dynamic background noise floor
        self.noise_floor = (1.0 - self.noise_alpha) * self.noise_floor + self.noise_alpha * rms

        cfg_audio = settings.get("audio")
        sensitivity = cfg_audio.get("clap_sensitivity", 0.7)
        # Threshold scales with sensitivity and ambient noise
        base_threshold = 0.08 * (1.2 - sensitivity)
        active_threshold = max(base_threshold, self.noise_floor * 3.5)

        # Apply bandpass filter
        try:
            filtered = signal.lfilter(self.b_filter, self.a_filter, audio_data)
            filt_peak = float(np.max(np.abs(filtered)))
            filt_rms = float(np.sqrt(np.mean(filtered**2)))
        except Exception:
            filt_peak = peak
            filt_rms = rms

        # Acoustic transient verification:
        # Claps have:
        # 1. High peak amplitude above active threshold
        # 2. High crest factor (filt_peak / (filt_rms + 1e-5) > 3.5)
        # 3. Minimum 0.18s separation between consecutive claps
        crest_factor = filt_peak / (filt_rms + 1e-5)

        if filt_peak > active_threshold and crest_factor > 3.2:
            with self._lock:
                min_interval = 0.18
                if now - self._last_clap_time > min_interval:
                    self._clap_count += 1
                    self._last_clap_time = now
                    logger.debug(f"Transient clap pulse detected! Count in sequence: {self._clap_count}")

    def _cleanup(self):
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def stop(self):
        self.running = False
        self.wait(1500)


class ClapManager:
    """High-level Clap Detection Controller."""
    def __init__(self):
        self.worker: ClapDetectorWorker = None

    def start(self) -> ClapDetectorWorker:
        self.stop()
        self.worker = ClapDetectorWorker()
        self.worker.start()
        return self.worker

    def stop(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker = None

    @staticmethod
    def get_available_mics() -> list:
        devices = []
        try:
            for idx, dev in enumerate(sd.query_devices()):
                if dev.get("max_input_channels", 0) > 0:
                    devices.append((idx, dev.get("name", f"Microphone {idx}")))
        except Exception as e:
            logger.warning(f"Error querying microphones: {e}")
        return devices

clap_mgr = ClapManager()

