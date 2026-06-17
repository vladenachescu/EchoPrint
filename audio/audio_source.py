from abc import ABC, abstractmethod
import numpy as np
import librosa
import sounddevice as sd

class AudioInputStrategy(ABC):
    @abstractmethod
    def record(self, duration_seconds: int) -> np.ndarray:
        """Records or fetches a 1D numpy array of audio samples."""
        pass

class MicrophoneInputStrategy(AudioInputStrategy):
    def __init__(self, sample_rate=22050):
        self.sample_rate = sample_rate

    def record(self, duration_seconds=5) -> np.ndarray:
        print(f"[*] Recording started from microphone... ({duration_seconds} seconds)")
        # Record audio
        recording = sd.rec(int(duration_seconds * self.sample_rate), 
                           samplerate=self.sample_rate, 
                           channels=1, 
                           dtype='float32')
        # Wait until recording is finished
        sd.wait()
        print("[*] Recording finished.")
        # Flatten shape (samples, channels) to 1D array
        return recording.flatten()

class FileInputStrategy(AudioInputStrategy):
    def __init__(self, file_path: str, sample_rate=22050):
        self.file_path = file_path
        self.sample_rate = sample_rate

    def record(self, duration_seconds=5) -> np.ndarray:
        print(f"[*] Loading audio from file: {self.file_path}")
        # Load audio file, crop/take only duration_seconds
        y, sr = librosa.load(self.file_path, sr=self.sample_rate, duration=duration_seconds)
        return y

class MockInputStrategy(AudioInputStrategy):
    def __init__(self, sample_rate=22050):
        self.sample_rate = sample_rate

    def record(self, duration_seconds=5) -> np.ndarray:
        print(f"[*] Generating simulated audio signal (Mock)...")
        # Generate a dummy sine wave signal + white noise
        num_samples = int(duration_seconds * self.sample_rate)
        t = np.linspace(0, duration_seconds, num_samples, endpoint=False)
        sine = 0.5 * np.sin(2 * np.pi * 440 * t) # A440 tone
        noise = 0.1 * np.random.randn(num_samples)
        return (sine + noise).astype(np.float32)
