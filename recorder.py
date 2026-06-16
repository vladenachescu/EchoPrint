from audio_source import AudioInputStrategy, MicrophoneInputStrategy

class AudioRecorder:
    def __init__(self, strategy: AudioInputStrategy = None, sample_rate=22050):
        self.strategy = strategy or MicrophoneInputStrategy(sample_rate=sample_rate)

    def record(self, duration_seconds=5):
        """Records audio using the injected strategy."""
        return self.strategy.record(duration_seconds)

