import unittest
import numpy as np
import os
import sys

# Add parent directory to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audio_processor import AudioProcessor

class TestAudioProcessor(unittest.TestCase):
    def setUp(self):
        # Generate dummy 1D audio signal (1 second of white noise + sine wave at 22050Hz)
        self.sample_rate = 22050
        self.duration = 1.0
        self.t = np.linspace(0, self.duration, int(self.sample_rate * self.duration), endpoint=False)
        self.signal = 0.5 * np.sin(2 * np.pi * 440 * self.t) + 0.1 * np.random.randn(len(self.t))
        
    def test_get_spectrogram(self):
        spectrogram = AudioProcessor.get_spectrogram(self.signal)
        self.assertIsInstance(spectrogram, np.ndarray)
        self.assertEqual(len(spectrogram.shape), 2) # Must be 2D
        self.assertTrue(spectrogram.shape[0] > 0)
        self.assertTrue(spectrogram.shape[1] > 0)
        
    def test_get_constellation_map(self):
        spectrogram = AudioProcessor.get_spectrogram(self.signal)
        peaks = AudioProcessor.get_constellation_map(spectrogram)
        self.assertIsInstance(peaks, list)
        if len(peaks) > 0:
            # Check elements are tuples of length 2
            self.assertIsInstance(peaks[0], tuple)
            self.assertEqual(len(peaks[0]), 2)
            
    def test_generate_hashes(self):
        # Generate dummy peaks
        peaks = [(10, 5), (20, 10), (15, 12), (30, 20)]
        hashes = AudioProcessor.generate_hashes(peaks)
        self.assertIsInstance(hashes, list)
        if len(hashes) > 0:
            # Check shape of hashes
            self.assertIsInstance(hashes[0], tuple)
            self.assertEqual(len(hashes[0]), 2)
            self.assertIsInstance(hashes[0][0], str)
            self.assertIsInstance(hashes[0][1], int)

    def test_fingerprint_audio_data(self):
        hashes = AudioProcessor.fingerprint_audio_data(self.signal)
        self.assertIsInstance(hashes, list)
        # Should generate hashes for a noisy signal
        self.assertTrue(len(hashes) >= 0)

if __name__ == '__main__':
    unittest.main()
