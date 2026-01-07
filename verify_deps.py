import librosa
import numpy as np
import soundfile as sf
import os

def test_librosa():
    print("Testing Librosa installation...")
    try:
        # Create a 2 second silent WAV file
        sr = 44100
        duration = 2
        t = np.linspace(0, duration, sr * duration)
        # Add a tiny bit of noise to avoid perfect silence which might make tempo detection weird
        data = np.random.uniform(-0.01, 0.01, t.shape)
        
        test_file = "test_audio.wav"
        sf.write(test_file, data, sr)
        print(f"Created test file: {test_file}")
        
        # Load and analyze
        y, sr = librosa.load(test_file)
        
        # Tempo detection
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        print(f"Detected Tempo: {tempo} BPM")
        
        # Key detection (using chroma)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        key_idx = np.argmax(np.mean(chroma, axis=1))
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        print(f"Detected Key Index (Top Chroma): {keys[key_idx]}")
        
        # Clean up
        os.remove(test_file)
        print("Cleanup successful.")
        print("Verification SUCCESSFUL!")
        
    except Exception as e:
        print(f"Verification FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_librosa()
