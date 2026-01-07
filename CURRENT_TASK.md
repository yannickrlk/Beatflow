# Current Task: Phase 13.5 - Global Shortcuts

> [!CAUTION]
> **MANDATORY: Python 3.12**
> `numba`/`librosa` crash with Access Violation (0xC0000005) on Python 3.14.
> Use `py -3.12` or install Python 3.12 from python.org.

## Status: IN PROGRESS

## Objective
Implement system-wide global hotkeys for controlling playback (Play/Pause, Skip) even when the application is not in focus.

## Technical Requirements
- [ ] **Global Hotkeys**: Use `pynput` or `keyboard` library to listen for media keys.
- [ ] **Shortcut Mapping**:
    - `Media Play/Pause`: Toggle play/pause
    - `Media Next`: Next track
    - `Media Prev`: Previous track
- [ ] **Integration**: Connect global listeners to `FooterPlayer` methods.
- [ ] **Windows Support**: Ensure it works reliably on Windows 10/11.

## Files to Modify
- `core/shortcuts.py` (NEW) - Global listener logic
- `main.py` - Initialize shortcut listener
- `requirements.txt` - Add shortcut library dependency

## Notes
- Be careful with background thread safety when calling UI methods from the shortcut thread.
- Ensure shortcuts are cleaned up properly on app exit.
