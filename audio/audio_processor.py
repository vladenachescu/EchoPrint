import librosa
import numpy as np
import scipy.ndimage as ndimage
import hashlib

# Configuration for fingerprinting
DEFAULT_FS = 22050          # Standard sampling rate
WINDOW_SIZE = 4096          # Size of the FFT window
OVERLAP_RATIO = 0.5         # Overlap between windows
FAN_VALUE = 15              # Degree to which a fingerprint can be paired with its neighbors
PEAK_NEIGHBORHOOD_SIZE = 20 # Minimum distance between peaks
MIN_HASH_TIME_DELTA = 0
MAX_HASH_TIME_DELTA = 200
PEAK_SORT = True            # Sort peaks by time before hashing

class AudioProcessor:
    @staticmethod
    def load_audio(file_path):
        """Loads audio and returns the waveform and sampling rate."""
        # y is the audio time series, sr is the sampling rate
        y, sr = librosa.load(file_path, sr=DEFAULT_FS)
        return y, sr

    @staticmethod
    def get_spectrogram(y):
        """Generates a spectrogram."""
        n_fft = WINDOW_SIZE
        hop_length = int(WINDOW_SIZE * (1 - OVERLAP_RATIO))
        
        # Compute short-time Fourier transform
        stft = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)
        
        # Convert to magnitude (absolute value)
        S = np.abs(stft)
        
        # Convert to dB (log scale)
        S_db = librosa.amplitude_to_db(S, ref=np.max)
        return S_db

    @staticmethod
    def get_constellation_map(spectrogram):
        """Finds local maxima (peaks) in the spectrogram."""
        # Using maximum filter to find local peaks
        struct = ndimage.generate_binary_structure(2, 1)
        neighborhood = ndimage.iterate_structure(struct, PEAK_NEIGHBORHOOD_SIZE)
        
        local_max = ndimage.maximum_filter(spectrogram, footprint=neighborhood) == spectrogram
        
        # We only keep local maxima that are strong enough. 
        # Since spectrogram is in dB relative to max (values from -80 to 0)
        # Let's keep peaks that are in the top 5% of energy.
        threshold = np.percentile(spectrogram, 95) 
        
        peaks = local_max & (spectrogram > threshold)
        
        # Extract coordinates of the peaks
        frequencies, times = np.where(peaks)
        return list(zip(frequencies, times))

    @staticmethod
    def generate_hashes(peaks):
        """Generates hashes from the constellation map."""
        if PEAK_SORT:
            # Sort by time
            peaks.sort(key=lambda x: x[1])
            
        hashes = []
        for i in range(len(peaks)):
            for j in range(1, FAN_VALUE):
                if (i + j) < len(peaks):
                    freq1, time1 = peaks[i]
                    freq2, time2 = peaks[i + j]
                    
                    time_delta = time2 - time1
                    
                    if MIN_HASH_TIME_DELTA <= time_delta <= MAX_HASH_TIME_DELTA:
                        # Bin the values to reduce hash fragility due to recording noise
                        f1_binned = freq1 - (freq1 % 2)
                        f2_binned = freq2 - (freq2 % 2)
                        t_binned = time_delta - (time_delta % 2)
                        
                        # Create a string representation to hash
                        hash_str = f"{f1_binned}|{f2_binned}|{t_binned}"
                        
                        # Use SHA1 and take the first 20 characters to save space
                        h = hashlib.sha1(hash_str.encode('utf-8'))
                        hash_val = h.hexdigest()[:20]
                        
                        # Store hash and the anchor time
                        hashes.append((hash_val, int(time1)))
        return hashes

    @staticmethod
    def fingerprint_file(file_path):
        """High-level function to process a file and return its hashes."""
        y, sr = AudioProcessor.load_audio(file_path)
        spectrogram = AudioProcessor.get_spectrogram(y)
        peaks = AudioProcessor.get_constellation_map(spectrogram)
        hashes = AudioProcessor.generate_hashes(peaks)
        return hashes

    @staticmethod
    def fingerprint_audio_data(y):
        """High-level function to process raw audio data array."""
        spectrogram = AudioProcessor.get_spectrogram(y)
        peaks = AudioProcessor.get_constellation_map(spectrogram)
        hashes = AudioProcessor.generate_hashes(peaks)
        return hashes
