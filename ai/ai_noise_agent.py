import numpy as np
import librosa

class AINoiseAgent:
    def __init__(self, sample_rate=22050):
        self.sample_rate = sample_rate

    def assess_quality(self, y: np.ndarray) -> dict:
        """
        Analyzes the quality of the input audio.
        Returns a dictionary with SNR estimate, clipping percentage, and a quality rating.
        """
        if len(y) == 0:
            return {"rating": "EMPTY", "snr": 0.0, "clipping": 0.0, "reason": "No audio data received"}

        # 1. Check signal level (RMS)
        rms = np.sqrt(np.mean(y**2))
        
        # 2. Check clipping (samples at max amplitude)
        max_val = np.max(np.abs(y))
        clipping_samples = np.sum(np.abs(y) >= 0.99)
        clipping_pct = (clipping_samples / len(y)) * 100.0

        # 3. Estimate SNR (Signal-to-Noise Ratio)
        # We estimate noise power from the 10% lowest energy frames
        frame_length = 2048
        hop_length = 512
        rms_frames = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
        
        if len(rms_frames) > 0:
            sorted_rms = np.sort(rms_frames)
            # Take lowest 10% as noise floor estimation
            noise_idx = max(1, int(len(sorted_rms) * 0.1))
            noise_est = np.mean(sorted_rms[:noise_idx])
            signal_est = np.mean(sorted_rms[noise_idx:])
            
            if noise_est > 0:
                snr = 20 * np.log10(signal_est / noise_est)
            else:
                snr = 100.0 # Virtual infinite SNR
        else:
            snr = 0.0

        # Rating logic
        if rms < 0.005:
            rating = "TOO_LOW"
            reason = "Volume is way too low or the microphone is muted"
        elif clipping_pct > 5.0:
            rating = "DISTORTED"
            reason = "Sound is distorted (clipping). Reduce volume or distance"
        elif snr < 10.0:
            rating = "NOISY"
            reason = "High background noise"
        else:
            rating = "EXCELLENT"
            reason = "Excellent quality for recognition"

        return {
            "rating": rating,
            "snr": float(snr),
            "clipping": float(clipping_pct),
            "rms": float(rms),
            "reason": reason
        }

    def denoise(self, y: np.ndarray) -> np.ndarray:
        """
        Applies a simple spectral subtraction (spectral gating) to denoise the audio signal.
        """
        if len(y) == 0:
            return y

        # Compute Short-Time Fourier Transform (STFT)
        stft = librosa.stft(y, n_fft=2048, hop_length=512)
        magnitude = np.abs(stft)
        phase = np.angle(stft)

        # Estimate noise profile from the lowest energy parts of the spectrogram
        # Calculate mean energy per frame
        frame_energies = np.mean(magnitude, axis=0)
        # Find 10% frames with lowest energy
        lowest_energy_indices = np.argsort(frame_energies)[:max(1, int(len(frame_energies) * 0.1))]
        
        # Calculate noise mean spectrum
        noise_profile = np.mean(magnitude[:, lowest_energy_indices], axis=1, keepdims=True)

        # Subtract noise from signal magnitude
        # We use a noise subtraction factor of 1.5 and a spectral floor coefficient of 0.02
        subtracted = magnitude - 1.5 * noise_profile
        subtracted = np.maximum(subtracted, 0.02 * magnitude)

        # Reconstruct complex spectrogram and apply inverse STFT
        stft_denoised = subtracted * np.exp(1j * phase)
        y_denoised = librosa.istft(stft_denoised, hop_length=512, length=len(y))

        return y_denoised
