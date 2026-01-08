"""Beatflow Sync Engine - Time-stretching and pitch-shifting for tempo sync."""

import os
import hashlib
import tempfile
import time
from typing import Optional, Dict
from pathlib import Path

import numpy as np

# librosa/soundfile for time-stretching and pitch shifting
try:
    import librosa
    import soundfile as sf
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


class SyncManager:
    """Manages time-stretching and pitch-shifting for tempo synchronization."""

    def __init__(self):
        """Initialize the Sync Manager."""
        self._cache: Dict[str, str] = {}  # hash -> temp file path
        self._cache_timestamps: Dict[str, float] = {}  # hash -> creation time
        self._cache_max_age = 24 * 60 * 60  # 24 hours in seconds
        self._temp_dir = Path(tempfile.gettempdir()) / "beatflow_sync"
        self._temp_dir.mkdir(exist_ok=True)
        self._cleanup_old_cache()

    def _get_cache_key(self, source_path: str, ratio: float = 1.0, semitones: int = 0) -> str:
        """Generate a unique cache key for the processed audio."""
        try:
            mtime = os.path.getmtime(source_path)
        except OSError:
            mtime = 0

        key_str = f"{source_path}_{mtime}_{ratio:.4f}_{semitones}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _cleanup_old_cache(self):
        """Remove cache files older than max age."""
        if not self._temp_dir.exists():
            return

        current_time = time.time()
        for cache_file in self._temp_dir.glob("*.wav"):
            try:
                file_age = current_time - cache_file.stat().st_mtime
                if file_age > self._cache_max_age:
                    cache_file.unlink()
            except Exception:
                pass

    def get_cached_path(self, source_path: str, ratio: float = 1.0, semitones: int = 0) -> Optional[str]:
        """Check if a processed version exists in cache."""
        cache_key = self._get_cache_key(source_path, ratio, semitones)
        if cache_key in self._cache:
            cached_path = self._cache[cache_key]
            if os.path.exists(cached_path):
                return cached_path
            else:
                del self._cache[cache_key]
        return None

    def stretch_audio(self, source_path: str, ratio: float) -> Optional[str]:
        """Time-stretch audio by the given ratio using librosa.

        Args:
            source_path: Path to the source audio file.
            ratio: Stretch ratio (e.g., 1.5 = 50% slower, 0.75 = 25% faster).
                   Clamped to 0.5-2.0 range.

        Returns:
            Path to the stretched audio file, or None on error.
        """
        if not LIBROSA_AVAILABLE:
            return None

        # Clamp ratio to reasonable range
        ratio = max(0.5, min(2.0, ratio))

        # Check if ratio is close to 1.0 (no change needed)
        if abs(ratio - 1.0) < 0.01:
            return source_path

        # Check cache first
        cached = self.get_cached_path(source_path, ratio=ratio)
        if cached:
            return cached

        try:
            # Generate output path
            cache_key = self._get_cache_key(source_path, ratio=ratio)
            output_path = str(self._temp_dir / f"{cache_key}.wav")

            # Load audio with librosa
            y, sr = librosa.load(source_path, sr=None, mono=False)

            # Handle mono/stereo
            if y.ndim == 1:
                # Mono - time stretch directly
                # librosa.effects.time_stretch uses rate (inverse of ratio)
                # rate > 1 = faster, rate < 1 = slower
                # We want ratio > 1 = faster (higher BPM), so rate = ratio
                y_stretched = librosa.effects.time_stretch(y, rate=ratio)
            else:
                # Stereo - process each channel
                stretched_channels = []
                for channel in y:
                    stretched = librosa.effects.time_stretch(channel, rate=ratio)
                    stretched_channels.append(stretched)
                y_stretched = np.array(stretched_channels)

            # Export to WAV
            if y_stretched.ndim == 1:
                sf.write(output_path, y_stretched, sr)
            else:
                sf.write(output_path, y_stretched.T, sr)

            # Add to cache
            self._cache[cache_key] = output_path
            self._cache_timestamps[cache_key] = time.time()

            return output_path

        except Exception as e:
            print(f"[SYNC] Error stretching audio: {e}")
            return None

    def shift_pitch(self, source_path: str, semitones: int) -> Optional[str]:
        """Pitch-shift audio by the given number of semitones.

        Args:
            source_path: Path to the source audio file.
            semitones: Number of semitones to shift (-12 to +12).

        Returns:
            Path to the pitch-shifted audio file, or None on error.
        """
        if not LIBROSA_AVAILABLE:
            return None

        # Clamp semitones to reasonable range
        semitones = max(-12, min(12, semitones))

        # Check if no shift needed
        if semitones == 0:
            return source_path

        # Check cache first
        cached = self.get_cached_path(source_path, semitones=semitones)
        if cached:
            return cached

        try:
            # Load audio
            y, sr = librosa.load(source_path, sr=None, mono=False)

            # Handle mono/stereo
            if y.ndim == 1:
                y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=semitones)
            else:
                shifted_channels = []
                for channel in y:
                    shifted = librosa.effects.pitch_shift(channel, sr=sr, n_steps=semitones)
                    shifted_channels.append(shifted)
                y_shifted = np.array(shifted_channels)

            # Generate output path
            cache_key = self._get_cache_key(source_path, semitones=semitones)
            output_path = str(self._temp_dir / f"{cache_key}.wav")

            # Export
            if y_shifted.ndim == 1:
                sf.write(output_path, y_shifted, sr)
            else:
                sf.write(output_path, y_shifted.T, sr)

            # Add to cache
            self._cache[cache_key] = output_path
            self._cache_timestamps[cache_key] = time.time()

            return output_path

        except Exception:
            return None

    def process_for_sync(
        self,
        source_path: str,
        original_bpm: float,
        target_bpm: float,
        semitones: int = 0
    ) -> Optional[str]:
        """Process audio for tempo sync with optional pitch shift.

        Args:
            source_path: Path to the source audio file.
            original_bpm: Original BPM of the sample.
            target_bpm: Target BPM to sync to.
            semitones: Optional pitch shift in semitones.

        Returns:
            Path to the processed audio file, or None on error.
        """
        if original_bpm <= 0 or target_bpm <= 0:
            return source_path

        # Calculate stretch ratio
        ratio = target_bpm / original_bpm

        # Clamp to reasonable range
        if ratio < 0.5 or ratio > 2.0:
            # Try halving or doubling the original BPM for better ratio
            if ratio < 0.5:
                original_bpm *= 2
                ratio = target_bpm / original_bpm
            elif ratio > 2.0:
                original_bpm /= 2
                ratio = target_bpm / original_bpm

        # Check combined cache
        cached = self.get_cached_path(source_path, ratio=ratio, semitones=semitones)
        if cached:
            return cached

        # Process: stretch first, then pitch shift if needed
        result_path = source_path

        # Time stretch
        if abs(ratio - 1.0) >= 0.01:
            stretched = self.stretch_audio(source_path, ratio)
            if stretched:
                result_path = stretched
            else:
                return None

        # Pitch shift if requested
        if semitones != 0:
            shifted = self.shift_pitch(result_path, semitones)
            if shifted:
                result_path = shifted

        return result_path

    def clear_cache(self):
        """Clear all cached files."""
        self._cache.clear()
        self._cache_timestamps.clear()

        if self._temp_dir.exists():
            for cache_file in self._temp_dir.glob("*.wav"):
                try:
                    cache_file.unlink()
                except Exception:
                    pass

    def is_available(self) -> bool:
        """Check if sync engine is available."""
        return LIBROSA_AVAILABLE


# Singleton instance
_sync_manager = None


def get_sync_manager() -> SyncManager:
    """Get the singleton SyncManager instance."""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = SyncManager()
    return _sync_manager
