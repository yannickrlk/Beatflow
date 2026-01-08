"""Audio fingerprinting for sonic similarity matching.

Based on the Shazam algorithm (Avery Wang):
- Compute spectrogram and find local peaks (landmarks)
- Create hashes from pairs of landmarks
- Match samples by comparing hash overlap with time alignment
"""

import hashlib
import threading
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import librosa
from scipy.ndimage import maximum_filter
from scipy.ndimage import generate_binary_structure


# Fingerprinting parameters
SAMPLE_RATE = 22050  # Downsample for speed
N_FFT = 2048  # FFT window size
HOP_LENGTH = 512  # Hop between windows
PEAK_NEIGHBORHOOD_SIZE = 20  # Size of peak detection neighborhood
MIN_PEAK_AMPLITUDE = -50  # Minimum dB for a peak
FAN_OUT = 15  # Number of target peaks per anchor
TARGET_TIME_DELTA = 200  # Max time frames between anchor and target
MAX_DURATION = 30  # Max seconds to analyze (for performance)


def _compute_spectrogram(audio_path: str) -> Optional[np.ndarray]:
    """Load audio and compute spectrogram in dB.

    Args:
        audio_path: Path to audio file

    Returns:
        2D numpy array (frequency x time) in dB, or None on error
    """
    try:
        # Load audio (mono, downsampled)
        y, sr = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True, duration=MAX_DURATION)

        # Compute STFT
        stft = librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH)

        # Convert to dB
        spectrogram = librosa.amplitude_to_db(np.abs(stft), ref=np.max)

        return spectrogram
    except Exception as e:
        print(f"Fingerprint error loading {audio_path}: {e}")
        return None


def _find_peaks(spectrogram: np.ndarray) -> List[Tuple[int, int]]:
    """Find local peaks in the spectrogram.

    Args:
        spectrogram: 2D array (frequency x time) in dB

    Returns:
        List of (frequency_bin, time_frame) tuples
    """
    # Create a binary structure for the neighborhood
    struct = generate_binary_structure(2, 1)

    # Apply maximum filter to find local maxima
    neighborhood_size = (PEAK_NEIGHBORHOOD_SIZE, PEAK_NEIGHBORHOOD_SIZE)
    local_max = maximum_filter(spectrogram, size=neighborhood_size) == spectrogram

    # Apply amplitude threshold
    threshold_mask = spectrogram > MIN_PEAK_AMPLITUDE

    # Combine masks
    peaks_mask = local_max & threshold_mask

    # Get peak coordinates
    freq_bins, time_frames = np.where(peaks_mask)

    # Return as list of tuples
    peaks = list(zip(freq_bins.tolist(), time_frames.tolist()))

    return peaks


def _create_hashes(peaks: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Create hashes from peak pairs.

    Uses anchor-target pairing with fan-out for robustness.

    Args:
        peaks: List of (frequency_bin, time_frame) tuples

    Returns:
        List of (hash_value, time_offset) tuples
    """
    # Sort peaks by time
    peaks = sorted(peaks, key=lambda p: p[1])

    hashes = []

    for i, (freq1, time1) in enumerate(peaks):
        # Find target peaks within the fan-out window
        targets_found = 0

        for j in range(i + 1, len(peaks)):
            freq2, time2 = peaks[j]
            time_delta = time2 - time1

            # Check time window
            if time_delta > TARGET_TIME_DELTA:
                break

            if time_delta <= 0:
                continue

            # Create hash from (freq1, freq2, time_delta)
            # Pack into a single integer for efficient storage
            hash_value = (freq1 << 20) | (freq2 << 10) | time_delta

            hashes.append((hash_value, time1))

            targets_found += 1
            if targets_found >= FAN_OUT:
                break

    return hashes


def generate_fingerprint(audio_path: str) -> List[Tuple[int, int]]:
    """Generate fingerprint hashes for an audio file.

    Args:
        audio_path: Path to audio file

    Returns:
        List of (hash_value, time_offset) tuples
    """
    # Compute spectrogram
    spectrogram = _compute_spectrogram(audio_path)
    if spectrogram is None:
        return []

    # Find peaks
    peaks = _find_peaks(spectrogram)
    if not peaks:
        return []

    # Create hashes
    hashes = _create_hashes(peaks)

    return hashes


def match_fingerprints(
    query_hashes: List[Tuple[int, int]],
    candidate_hashes: Dict[str, List[Tuple[int, int]]]
) -> List[Tuple[str, float]]:
    """Match query fingerprint against candidates.

    Uses time-aligned hash matching for accuracy.

    Args:
        query_hashes: List of (hash_value, time_offset) from query sample
        candidate_hashes: Dict mapping sample_path -> list of (hash, offset)

    Returns:
        List of (sample_path, similarity_score) sorted by score descending
    """
    if not query_hashes:
        return []

    # Build hash lookup for query
    query_hash_set = {h[0] for h in query_hashes}
    query_hash_times = {h[0]: h[1] for h in query_hashes}

    results = []

    for path, candidate_list in candidate_hashes.items():
        # Find matching hashes
        matches = []
        for hash_val, offset in candidate_list:
            if hash_val in query_hash_set:
                query_time = query_hash_times[hash_val]
                time_diff = offset - query_time
                matches.append(time_diff)

        if not matches:
            continue

        # Count time-aligned matches (most common time difference)
        # This filters out coincidental matches
        time_diff_counts = {}
        for td in matches:
            # Quantize to allow small variations
            td_quantized = td // 5 * 5
            time_diff_counts[td_quantized] = time_diff_counts.get(td_quantized, 0) + 1

        # Get best alignment count
        best_count = max(time_diff_counts.values()) if time_diff_counts else 0

        # Calculate similarity score (0-100)
        # Based on aligned matches relative to query size
        score = min(100, (best_count / len(query_hashes)) * 500)

        if score > 5:  # Minimum threshold
            results.append((path, score))

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)

    return results


class FingerprintGenerator:
    """Async fingerprint generator with progress tracking."""

    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._lock = threading.Lock()

    def generate_async(
        self,
        audio_path: str,
        callback: callable = None
    ):
        """Generate fingerprint asynchronously.

        Args:
            audio_path: Path to audio file
            callback: Function(path, hashes) called on completion
        """
        def task():
            hashes = generate_fingerprint(audio_path)
            if callback:
                callback(audio_path, hashes)

        self._executor.submit(task)

    def generate_batch(
        self,
        paths: List[str],
        progress_callback: callable = None,
        completion_callback: callable = None
    ):
        """Generate fingerprints for multiple files.

        Args:
            paths: List of audio file paths
            progress_callback: Function(current, total, path) for progress
            completion_callback: Function(results) when all done
        """
        results = {}
        total = len(paths)
        completed = [0]  # Use list for mutable closure

        def on_complete(path, hashes):
            with self._lock:
                results[path] = hashes
                completed[0] += 1

                if progress_callback:
                    progress_callback(completed[0], total, path)

                if completed[0] >= total and completion_callback:
                    completion_callback(results)

        for path in paths:
            self.generate_async(path, on_complete)

    def shutdown(self):
        """Shutdown the executor."""
        self._executor.shutdown(wait=False)


# Singleton instance
_generator = None


def get_fingerprint_generator() -> FingerprintGenerator:
    """Get the singleton fingerprint generator instance."""
    global _generator
    if _generator is None:
        _generator = FingerprintGenerator()
    return _generator
