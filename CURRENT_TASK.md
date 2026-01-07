# Current Task: Phase 13.5 - Global Shortcuts

> [!CAUTION]
> **MANDATORY: Python 3.12**
> `numba`/`librosa` crash with Access Violation (0xC0000005) on Python 3.14.
> Use `py -3.12` or install Python 3.12 from python.org.

## Status: IN PROGRESS

## Objective
Implement system-wide hotkeys (Play/Pause, Previous, Next) so users can control Beatflow even when it's not the active window.

## Technical Requirements

### 1. Global Hotkey Implementation
- [ ] **Library Selection**: Research `pynput` or `keyboard` library for cross-platform (or Windows-specific `ctypes`) hotkey support.
- [ ] **Key Mapping**:
    - `Media Play/Pause` or `Ctrl+Alt+Space` -> Play/Pause
    - `Media Previous` or `Ctrl+Alt+Left` -> Previous Track
    - `Media Next` or `Ctrl+Alt+Right` -> Next Track
- [ ] **Integration**: Connect hotkey listeners to `BeatflowApp` playback methods.
- [ ] **Cleanup**: Ensure listeners are properly stopped when the application closes.

## Completed Tasks (Phase 13 Core)
- [x] **Waveform Click-to-Seek**: Click anywhere on waveform to jump to position.
- [x] **SoundCloud-style Progress**: Visual feedback with dual-waveform compositing.
- [x] **Progress Needle**: (Implemented via composite image).

## Files to Modify
- `ui/app.py` (Add listener setup/cleanup)
- `requirements.txt` (Add new dependency if needed)

## Verification
- Minimize Beatflow.
- Press Global Hotkey -> Track pauses/plays.
- Press Next Hotkey -> App switches to next track (verify via audio).
