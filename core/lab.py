"""ProducerOS Lab - Non-destructive audio processing engine."""

import os
import tempfile
from typing import Dict, Optional, Tuple
import numpy as np

# Configure ffmpeg from imageio_ffmpeg BEFORE importing audio libraries
# This ensures librosa/audioread can find ffmpeg for MP3 decoding
try:
    import imageio_ffmpeg
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = os.path.dirname(ffmpeg_path)
    # Add ffmpeg directory to PATH so audioread can find it
    os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False

# Librosa for audio loading and processing
try:
    import librosa
    import soundfile as sf
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

# Pydub as fallback (configure with bundled ffmpeg)
try:
    from pydub import AudioSegment
    if FFMPEG_AVAILABLE:
        AudioSegment.converter = ffmpeg_path
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


class LabManager:
    """Manages non-destructive audio processing for the ProducerOS Lab."""

    def __init__(self):
        """Initialize the Lab Manager."""
        self._temp_files = []  # Track temp files for cleanup

    def get_duration_ms(self, source_path: str) -> int:
        """Get the duration of an audio file in milliseconds.

        Args:
            source_path: Path to the audio file.

        Returns:
            Duration in milliseconds.
        """
        # Try librosa first (more reliable for various formats)
        if LIBROSA_AVAILABLE:
            try:
                duration = librosa.get_duration(path=source_path)
                return int(duration * 1000)
            except Exception:
                pass  # Fall through to pydub

        # Fallback to pydub
        try:
            audio = AudioSegment.from_file(source_path)
            return len(audio)
        except Exception as e:
            print(f"Error getting duration for {source_path}: {e}")
            return 0

    def apply_edits(self, source_path: str, settings: Dict) -> Optional[Tuple[np.ndarray, int]]:
        """Apply non-destructive edits to an audio file.

        Args:
            source_path: Path to the source audio file.
            settings: Dictionary with edit settings:
                - trim_start_ms: Start trim point in milliseconds
                - trim_end_ms: End trim point in milliseconds
                - fade_in_ms: Fade in duration in milliseconds
                - fade_out_ms: Fade out duration in milliseconds
                - normalize: Boolean, whether to normalize to -0.1dB

        Returns:
            Tuple of (audio_array, sample_rate), or None on error.
        """
        if not LIBROSA_AVAILABLE:
            print("Error: librosa not available for audio processing")
            return None

        try:
            # Load audio with librosa
            y, sr = librosa.load(source_path, sr=None, mono=False)

            # Handle mono/stereo
            if y.ndim == 1:
                y = y.reshape(1, -1)  # Make it 2D for consistent processing

            duration_samples = y.shape[1]
            duration_ms = (duration_samples / sr) * 1000

            # Get settings with defaults
            trim_start_ms = settings.get('trim_start_ms', 0)
            trim_end_ms = settings.get('trim_end_ms', duration_ms)
            fade_in_ms = settings.get('fade_in_ms', 0)
            fade_out_ms = settings.get('fade_out_ms', 0)
            normalize = settings.get('normalize', False)

            # Convert ms to samples
            trim_start = int((trim_start_ms / 1000) * sr)
            trim_end = int((trim_end_ms / 1000) * sr)

            # Validate trim points
            trim_start = max(0, min(trim_start, duration_samples))
            trim_end = max(trim_start, min(trim_end, duration_samples))

            # Apply trim
            y = y[:, trim_start:trim_end]

            # Apply fade in
            if fade_in_ms > 0:
                fade_in_samples = int((fade_in_ms / 1000) * sr)
                fade_in_samples = min(fade_in_samples, y.shape[1])
                fade_curve = np.linspace(0, 1, fade_in_samples)
                y[:, :fade_in_samples] *= fade_curve

            # Apply fade out
            if fade_out_ms > 0:
                fade_out_samples = int((fade_out_ms / 1000) * sr)
                fade_out_samples = min(fade_out_samples, y.shape[1])
                fade_curve = np.linspace(1, 0, fade_out_samples)
                y[:, -fade_out_samples:] *= fade_curve

            # Apply normalization
            if normalize:
                max_val = np.max(np.abs(y))
                if max_val > 0:
                    # Normalize to -0.1 dB (about 0.989)
                    target = 10 ** (-0.1 / 20)
                    y = y * (target / max_val)

            # Return as (channels, samples) with sample rate
            return (y, sr)

        except Exception as e:
            print(f"Error applying edits to {source_path}: {e}")
            return None

    def export_temp(self, source_path: str, settings: Dict) -> Optional[str]:
        """Apply edits and export to a temporary WAV file.

        Args:
            source_path: Path to the source audio file.
            settings: Dictionary with edit settings.

        Returns:
            Path to the temporary WAV file, or None on error.
        """
        result = self.apply_edits(source_path, settings)
        if result is None:
            return None

        y, sr = result

        try:
            # Create temp file with unique name (include timestamp to avoid lock issues)
            import time
            base_name = os.path.splitext(os.path.basename(source_path))[0]
            timestamp = int(time.time() * 1000) % 100000  # Last 5 digits of ms timestamp
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"produceros_lab_{base_name}_{timestamp}.wav")

            # Transpose for soundfile (expects samples x channels)
            audio_data = y.T if y.ndim > 1 else y

            # Export as WAV using soundfile
            sf.write(temp_path, audio_data, sr)

            # Track for cleanup
            self._temp_files.append(temp_path)

            return temp_path

        except Exception as e:
            print(f"Error exporting temp file for {source_path}: {e}")
            return None

    def preview_audio(self, source_path: str, settings: Dict) -> Optional[str]:
        """Export a preview version for playback.

        Same as export_temp but may use different naming.

        Args:
            source_path: Path to the source audio file.
            settings: Dictionary with edit settings.

        Returns:
            Path to the preview WAV file, or None on error.
        """
        return self.export_temp(source_path, settings)

    def cleanup_temp_files(self):
        """Remove all temporary files created by the Lab."""
        for temp_path in self._temp_files:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                print(f"Error cleaning up temp file {temp_path}: {e}")

        self._temp_files = []

    def get_default_settings(self, source_path: str) -> Dict:
        """Get default settings for a sample.

        Args:
            source_path: Path to the audio file.

        Returns:
            Default settings dictionary.
        """
        duration = self.get_duration_ms(source_path)
        return {
            'trim_start_ms': 0,
            'trim_end_ms': duration,
            'fade_in_ms': 0,
            'fade_out_ms': 0,
            'normalize': False
        }


# Singleton instance
_lab_manager = None


def get_lab_manager() -> LabManager:
    """Get the singleton LabManager instance."""
    global _lab_manager
    if _lab_manager is None:
        _lab_manager = LabManager()
    return _lab_manager
