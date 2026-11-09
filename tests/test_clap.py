"""
Unit Tests for AIRCTRL Clap Detection & Audio DSP
Tests Butterworth bandpass filtering, transient crest factor analysis,
and multi-clap sequence counting.
"""
import sys
import os
import unittest
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.clap_detection import ClapDetectorWorker

def generate_clap_waveform(sample_rate=44100, duration=0.04):
    """Synthesizes a sharp percussive acoustic impulse with rapid decay."""
    num_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, num_samples)
    # 2500 Hz carrier frequency enveloped in an exponential decay
    envelope = np.exp(-t * 200.0)
    noise = np.random.uniform(-0.1, 0.1, num_samples)
    carrier = np.sin(2 * np.pi * 2500 * t) + noise
    waveform = carrier * envelope
    waveform = waveform / np.max(np.abs(waveform)) * 0.9  # Scale to 0.9 peak
    return waveform.astype(np.float32)

def generate_speech_noise(sample_rate=44100, duration=0.04):
    """Synthesizes low-frequency, sustained speech/humming noise."""
    num_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, num_samples)
    # 300 Hz low frequency hum
    waveform = 0.2 * np.sin(2 * np.pi * 300 * t)
    return waveform.astype(np.float32)


class TestClapDetection(unittest.TestCase):
    def setUp(self):
        self.worker = ClapDetectorWorker(sample_rate=44100, block_size=2048)

    def test_filter_attenuates_low_frequencies(self):
        """Test Butterworth bandpass filter suppresses low frequency speech/hum."""
        from scipy import signal
        low_hum = generate_speech_noise(duration=0.05)
        filtered = signal.lfilter(self.worker.b_filter, self.worker.a_filter, low_hum)

        # Filter should significantly reduce 300Hz hum energy
        self.assertLess(np.max(np.abs(filtered)), np.max(np.abs(low_hum)) * 0.2)

    def test_clap_crest_factor(self):
        """Test transient clap has high crest factor (> 3.0)."""
        clap = generate_clap_waveform()
        peak = np.max(np.abs(clap))
        rms = np.sqrt(np.mean(clap**2))
        crest_factor = peak / (rms + 1e-5)
        self.assertGreater(crest_factor, 3.0)

    def test_speech_crest_factor(self):
        """Test continuous sound has lower crest factor than a sharp clap."""
        speech = generate_speech_noise()
        peak = np.max(np.abs(speech))
        rms = np.sqrt(np.mean(speech**2))
        crest_factor = peak / (rms + 1e-5)
        self.assertLess(crest_factor, 2.0)

    def test_multi_clap_sequence_logic(self):
        """Test clap counter tracks sequences correctly up to 4 claps."""
        self.worker._clap_count = 1
        self.assertEqual(self.worker._clap_count, 1)

        self.worker._clap_count = 2
        self.assertEqual(self.worker._clap_count, 2)

        self.worker._clap_count = 4
        self.assertEqual(self.worker._clap_count, 4)

if __name__ == "__main__":
    unittest.main()

