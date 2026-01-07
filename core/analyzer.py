"""Audio analysis module for BPM and Key detection."""

import os
import sys
import json
import subprocess
import threading
from typing import Dict, Optional, Callable, List
from concurrent.futures import ThreadPoolExecutor, Future

# Check if librosa is available (but don't import it here - import in subprocess)
try:
    import importlib.util
    LIBROSA_AVAILABLE = importlib.util.find_spec("librosa") is not None
except Exception:
    LIBROSA_AVAILABLE = False

# numpy is needed for key detection
try:
    import numpy as np
except ImportError:
    pass

# Database access
try:
    from core.database import get_database
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


# Musical key mapping (Krumhansl-Schmuckler key profiles)
KEY_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def _analyze_in_process(filepath: str, queue):
    """
    Perform audio analysis in a separate process.
    This function is called via multiprocessing to isolate librosa from main app.
    """
    result = {'bpm': '', 'key': ''}

    try:
        # Import librosa only in this subprocess
        import librosa
        import numpy as np

        # Load audio file (first 30 seconds for faster analysis)
        y, sr = librosa.load(filepath, sr=22050, duration=30, mono=True)

        if len(y) == 0:
            queue.put(result)
            return

        # BPM Detection using onset envelope + tempo estimation
        # (avoids beat_track which crashes with numba on some systems)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo = librosa.feature.tempo(onset_envelope=onset_env, sr=sr)
        if isinstance(tempo, np.ndarray):
            tempo = tempo[0]
        if tempo > 0:
            result['bpm'] = str(int(round(tempo)))

        # Key Detection using chroma features
        try:
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            chroma_avg = np.mean(chroma, axis=1)

            # Krumhansl-Schmuckler key profiles
            major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
            minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

            # Normalize
            major_profile = (major_profile - np.mean(major_profile)) / np.std(major_profile)
            minor_profile = (minor_profile - np.mean(minor_profile)) / np.std(minor_profile)
            chroma_norm = (chroma_avg - np.mean(chroma_avg)) / (np.std(chroma_avg) + 1e-6)

            # Correlate with all keys
            correlations = []
            for i in range(12):
                major_rot = np.roll(major_profile, i)
                minor_rot = np.roll(minor_profile, i)
                corr_major = np.corrcoef(chroma_norm, major_rot)[0, 1]
                corr_minor = np.corrcoef(chroma_norm, minor_rot)[0, 1]
                correlations.append((corr_major, i, 'major'))
                correlations.append((corr_minor, i, 'minor'))

            best = max(correlations, key=lambda x: x[0])
            correlation, key_idx, mode = best

            if correlation > 0.3:
                key_name = KEY_NAMES[key_idx]
                result['key'] = f"{key_name}m" if mode == 'minor' else key_name
        except Exception:
            pass  # Key detection failed, continue with BPM only

    except Exception as e:
        result['error'] = str(e)

    queue.put(result)


class AudioAnalyzer:
    """Handles BPM and Key detection for audio files."""

    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="analyzer")
        self._active_tasks: Dict[str, Future] = {}
        self._callbacks: Dict[str, Callable] = {}

    @staticmethod
    def is_available() -> bool:
        """Check if librosa is available for analysis."""
        return LIBROSA_AVAILABLE

    def analyze_file(self, filepath: str, callback: Callable[[str, Dict], None] = None) -> Optional[Dict]:
        """
        Analyze a single audio file for BPM and Key.

        Args:
            filepath: Path to the audio file.
            callback: Optional callback(filepath, result) called when done.

        Returns:
            Dict with 'bpm' and 'key' if synchronous (no callback),
            None if async (with callback).
        """
        if not LIBROSA_AVAILABLE:
            result = {'bpm': '', 'key': '', 'error': 'librosa not installed'}
            if callback:
                callback(filepath, result)
            return result

        # Run synchronously to avoid threading issues with numba
        # (Threading with numba can cause segfaults)
        result = self._do_analysis(filepath)
        if DB_AVAILABLE and (result.get('bpm') or result.get('key')):
            db = get_database()
            db.update_analysis(filepath, result.get('bpm', ''), result.get('key', ''))

        if callback:
            callback(filepath, result)

        return result

    def _do_analysis(self, filepath: str) -> Dict:
        """
        Perform audio analysis in a separate process to avoid conflicts.

        Args:
            filepath: Path to the audio file.

        Returns:
            Dict with 'bpm' and 'key' values.
        """
        result = {'bpm': '', 'key': ''}

        try:
            print(f"[ANALYZER] Starting analysis for: {filepath}", flush=True)

            # Get the path to analyze_script.py
            script_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(script_dir, 'analyze_script.py')

            # Run analysis in a completely separate subprocess
            proc = subprocess.run(
                [sys.executable, script_path, filepath],
                capture_output=True,
                text=True,
                timeout=60
            )

            print(f"[ANALYZER] Subprocess returned: {proc.returncode}", flush=True)

            if proc.returncode == 0 and proc.stdout.strip():
                try:
                    result = json.loads(proc.stdout.strip())
                    print(f"[ANALYZER] Got result: {result}", flush=True)
                except json.JSONDecodeError as e:
                    print(f"[ANALYZER] JSON error: {e}, stdout: {proc.stdout}", flush=True)
                    result['error'] = f'JSON decode error: {proc.stdout}'
            else:
                print(f"[ANALYZER] Subprocess failed, stderr: {proc.stderr}", flush=True)
                result['error'] = proc.stderr or f'Exit code: {proc.returncode}'

        except subprocess.TimeoutExpired:
            result['error'] = 'Analysis timeout'
            print(f"[ANALYZER] Timeout!", flush=True)
        except Exception as e:
            result['error'] = str(e)
            print(f"[ANALYZER] Exception: {e}", flush=True)

        return result

    def _detect_key(self, y: np.ndarray, sr: int) -> str:
        """
        Detect musical key using chroma features and Krumhansl-Schmuckler algorithm.

        Args:
            y: Audio time series.
            sr: Sample rate.

        Returns:
            Key string (e.g., 'Am', 'C') or empty string.
        """
        try:
            # Compute chroma features
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)

            # Average chroma across time
            chroma_avg = np.mean(chroma, axis=1)

            # Krumhansl-Schmuckler key profiles
            major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
            minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

            # Normalize profiles
            major_profile = (major_profile - np.mean(major_profile)) / np.std(major_profile)
            minor_profile = (minor_profile - np.mean(minor_profile)) / np.std(minor_profile)
            chroma_norm = (chroma_avg - np.mean(chroma_avg)) / (np.std(chroma_avg) + 1e-6)

            # Correlate with all possible keys (12 major + 12 minor)
            correlations = []
            for i in range(12):
                # Rotate profiles to each key
                major_rot = np.roll(major_profile, i)
                minor_rot = np.roll(minor_profile, i)

                # Pearson correlation
                corr_major = np.corrcoef(chroma_norm, major_rot)[0, 1]
                corr_minor = np.corrcoef(chroma_norm, minor_rot)[0, 1]

                correlations.append((corr_major, i, 'major'))
                correlations.append((corr_minor, i, 'minor'))

            # Find best match
            best = max(correlations, key=lambda x: x[0])
            correlation, key_idx, mode = best

            # Only return if correlation is strong enough
            if correlation > 0.3:
                key_name = KEY_NAMES[key_idx]
                if mode == 'minor':
                    return f"{key_name}m"
                else:
                    return key_name

        except Exception:
            pass

        return ''

    def analyze_batch(
        self,
        filepaths: List[str],
        progress_callback: Callable[[int, int, str], None] = None,
        completion_callback: Callable[[List[Dict]], None] = None
    ):
        """
        Analyze multiple files with progress reporting.
        Runs in a background thread to avoid blocking the UI.

        Args:
            filepaths: List of file paths to analyze.
            progress_callback: Called with (current, total, filepath) for each file.
            completion_callback: Called with list of results when all done.
        """
        def run_batch():
            results = []
            total = len(filepaths)

            for i, filepath in enumerate(filepaths):
                result = self._do_analysis(filepath)
                result['path'] = filepath
                results.append(result)

                # Update database
                if DB_AVAILABLE and (result.get('bpm') or result.get('key')):
                    db = get_database()
                    db.update_analysis(filepath, result.get('bpm', ''), result.get('key', ''))

                if progress_callback:
                    progress_callback(i + 1, total, filepath)

            if completion_callback:
                completion_callback(results)

        # Run in background thread
        thread = threading.Thread(target=run_batch, daemon=True)
        thread.start()

    def cancel_all(self):
        """Cancel all pending analysis tasks."""
        for filepath, future in list(self._active_tasks.items()):
            future.cancel()
        self._active_tasks.clear()
        self._callbacks.clear()

    def shutdown(self):
        """Shutdown the executor."""
        self.cancel_all()
        self._executor.shutdown(wait=False)


# Global analyzer instance (singleton pattern)
_analyzer_instance: Optional[AudioAnalyzer] = None


def get_analyzer() -> AudioAnalyzer:
    """Get the global analyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = AudioAnalyzer()
    return _analyzer_instance


def analyze_audio(filepath: str) -> Dict:
    """
    Convenience function to analyze a single file synchronously.

    Args:
        filepath: Path to the audio file.

    Returns:
        Dict with 'bpm' and 'key' values.
    """
    analyzer = get_analyzer()
    return analyzer.analyze_file(filepath)
