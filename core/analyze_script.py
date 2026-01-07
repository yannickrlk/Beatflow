"""Standalone script for audio analysis - runs in separate process."""
import sys
import json

def analyze(filepath):
    """Analyze audio file for BPM and Key."""
    result = {'bpm': '', 'key': ''}

    try:
        import librosa
        import numpy as np

        # Load audio (first 60 seconds for better accuracy)
        y, sr = librosa.load(filepath, sr=22050, duration=60, mono=True)

        if len(y) == 0:
            return result

        # BPM Detection - use beat_track for better accuracy
        # Constrain to typical music BPM range (70-180)
        try:
            tempo, beat_frames = librosa.beat.beat_track(
                y=y, sr=sr,
                start_bpm=120,  # Start guess
                tightness=100   # How tightly to adhere to tempo estimate
            )
            if isinstance(tempo, np.ndarray):
                tempo = tempo[0]

            # Correct half/double tempo detection
            # Most music samples are between 70-180 BPM
            if tempo > 0:
                # If tempo is too low, try doubling it
                if tempo < 70:
                    tempo = tempo * 2
                # If tempo is too high, try halving it
                elif tempo > 180:
                    tempo = tempo / 2

                result['bpm'] = str(int(round(tempo)))
        except Exception:
            # Fallback to simpler tempo estimation
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            tempo = librosa.feature.tempo(onset_envelope=onset_env, sr=sr)
            if isinstance(tempo, np.ndarray):
                tempo = tempo[0]
            if tempo > 0:
                if tempo < 70:
                    tempo = tempo * 2
                elif tempo > 180:
                    tempo = tempo / 2
                result['bpm'] = str(int(round(tempo)))

        # Key Detection
        KEY_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        try:
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            chroma_avg = np.mean(chroma, axis=1)

            major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
            minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

            major_profile = (major_profile - np.mean(major_profile)) / np.std(major_profile)
            minor_profile = (minor_profile - np.mean(minor_profile)) / np.std(minor_profile)
            chroma_norm = (chroma_avg - np.mean(chroma_avg)) / (np.std(chroma_avg) + 1e-6)

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
            pass

    except Exception as e:
        result['error'] = str(e)

    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'No file path provided'}))
        sys.exit(1)

    filepath = sys.argv[1]
    result = analyze(filepath)
    print(json.dumps(result))
