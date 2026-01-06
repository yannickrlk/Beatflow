import os
import shutil
from pathlib import Path

# Mock functionality from sample_browser.py
AUDIO_EXTENSIONS = {'.wav', '.mp3', '.ogg', '.flac'}

def count_audio_files(folder_path):
    count = 0
    try:
        # UPDATED LOGIC (RECURSIVE)
        for root, dirs, files in os.walk(folder_path):
            for item in files:
                ext = os.path.splitext(item)[1].lower()
                if ext in AUDIO_EXTENSIONS:
                    count += 1
    except Exception as e:
        print(f"Error: {e}")
    return count

def setup_test_env():
    # larger setup
    base = Path("test_samples_root")
    if base.exists():
        shutil.rmtree(base)
    base.mkdir()
    
    # 1. Root file
    (base / "root_kick.wav").touch()
    
    # 2. Subfolder file
    sub = base / "trap_pack"
    sub.mkdir()
    (sub / "trap_snare.wav").touch()
    
    return base

def run_test():
    base = setup_test_env()
    print(f"Created test structure in {base.absolute()}")
    print("Expected: 2 audio files (one in root, one in subfolder)")
    
    # Test
    count = count_audio_files(str(base))
    print(f"Recursive Logic Found: {count} files")
    
    if count == 2:
        print("SUCCESS: recursive scanning works.")
    else:
        print(f"FAIL: expected 2, got {count}")

    # Cleanup
    shutil.rmtree(base)

if __name__ == "__main__":
    run_test()
