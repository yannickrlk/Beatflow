"""Waveform generation for audio visualization."""

import os
import wave
import struct
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw

# Cache directory for waveform images
CACHE_DIR = Path(__file__).parent.parent / ".waveform_cache"


def _ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    CACHE_DIR.mkdir(exist_ok=True)


def _get_cache_path(file_path: str, width: int, height: int, color: str) -> Path:
    """Generate a cache path for a waveform image."""
    # Create unique hash based on file path, size, and color
    key = f"{file_path}_{width}_{height}_{color}_{os.path.getmtime(file_path)}"
    hash_key = hashlib.md5(key.encode()).hexdigest()
    return CACHE_DIR / f"{hash_key}.png"


def _read_audio_data(file_path: str) -> Optional[np.ndarray]:
    """
    Read audio file and return normalized samples as numpy array.
    Supports WAV directly, other formats via pydub if available.
    """
    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == '.wav':
            return _read_wav(file_path)
        else:
            # Try pydub for other formats (mp3, flac, ogg, etc.)
            return _read_with_pydub(file_path)
    except Exception as e:
        print(f"Error reading audio {file_path}: {e}")
        return None


def _read_wav(file_path: str) -> Optional[np.ndarray]:
    """Read WAV file and return normalized samples."""
    try:
        with wave.open(file_path, 'rb') as wav_file:
            n_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            n_frames = wav_file.getnframes()

            # Read raw data
            raw_data = wav_file.readframes(n_frames)

            # Convert to numpy array based on sample width
            if sample_width == 1:
                dtype = np.uint8
                max_val = 255
            elif sample_width == 2:
                dtype = np.int16
                max_val = 32767
            elif sample_width == 4:
                dtype = np.int32
                max_val = 2147483647
            else:
                return None

            samples = np.frombuffer(raw_data, dtype=dtype)

            # Convert to mono if stereo
            if n_channels == 2:
                samples = samples[::2]  # Take left channel

            # Normalize to -1.0 to 1.0
            samples = samples.astype(np.float32) / max_val

            return samples
    except Exception:
        return None


def _read_with_pydub(file_path: str) -> Optional[np.ndarray]:
    """Read audio file using pydub (supports mp3, flac, ogg, etc.)."""
    try:
        from pydub import AudioSegment

        audio = AudioSegment.from_file(file_path)

        # Convert to mono
        if audio.channels > 1:
            audio = audio.set_channels(1)

        # Get raw samples
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)

        # Normalize
        max_val = float(2 ** (audio.sample_width * 8 - 1))
        samples = samples / max_val

        return samples
    except Exception:
        # Fallback to librosa if pydub fails (e.g., ffmpeg not installed)
        return _read_with_librosa(file_path)


def _read_with_librosa(file_path: str) -> Optional[np.ndarray]:
    """Read audio file using librosa (fallback when pydub/ffmpeg unavailable)."""
    try:
        import librosa
        # Load audio at 22050 Hz mono (fast and sufficient for waveform)
        y, sr = librosa.load(file_path, sr=22050, mono=True)
        return y
    except ImportError:
        return None
    except Exception:
        return None


def _downsample(samples: np.ndarray, target_points: int) -> np.ndarray:
    """Downsample audio to target number of points using peak detection."""
    if len(samples) <= target_points:
        return np.abs(samples)

    # Calculate chunk size
    chunk_size = len(samples) // target_points

    # Get max absolute value in each chunk (captures peaks)
    downsampled = np.array([
        np.max(np.abs(samples[i * chunk_size:(i + 1) * chunk_size]))
        for i in range(target_points)
    ])

    return downsampled


def generate_waveform_image(
    file_path: str,
    width: int = 200,
    height: int = 40,
    color: str = "#444444",
    bg_color: str = "transparent",
    use_cache: bool = True
) -> Optional[Image.Image]:
    """
    Generate a waveform image for an audio file.

    Args:
        file_path: Path to the audio file
        width: Image width in pixels
        height: Image height in pixels
        color: Waveform color (hex string)
        bg_color: Background color or "transparent"
        use_cache: Whether to use disk cache

    Returns:
        PIL Image object or None if generation fails
    """
    # Check cache first
    if use_cache:
        _ensure_cache_dir()
        cache_path = _get_cache_path(file_path, width, height, color)
        if cache_path.exists():
            try:
                return Image.open(cache_path)
            except Exception:
                pass

    # Read audio data
    samples = _read_audio_data(file_path)
    if samples is None or len(samples) == 0:
        return None

    # Downsample to number of bars
    n_bars = width // 3  # 2px bar + 1px gap
    peaks = _downsample(samples, n_bars)

    # Normalize peaks to 0-1 range
    max_peak = np.max(peaks)
    if max_peak > 0:
        peaks = peaks / max_peak

    # Create image
    if bg_color == "transparent":
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    else:
        img = Image.new('RGBA', (width, height), bg_color)

    draw = ImageDraw.Draw(img)

    # Draw waveform bars (centered vertically)
    bar_width = 2
    gap = 1
    center_y = height // 2

    for i, peak in enumerate(peaks):
        x = i * (bar_width + gap)
        bar_height = int(peak * (height - 4))  # Leave some padding

        if bar_height < 2:
            bar_height = 2

        y1 = center_y - bar_height // 2
        y2 = center_y + bar_height // 2

        draw.rectangle([x, y1, x + bar_width - 1, y2], fill=color)

    # Save to cache
    if use_cache:
        try:
            img.save(cache_path, 'PNG')
        except Exception:
            pass

    return img


def clear_cache():
    """Clear all cached waveform images."""
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob("*.png"):
            try:
                f.unlink()
            except Exception:
                pass
