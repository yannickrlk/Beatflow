# Current Task: Phase 13 - Waveform Interaction

> [!CAUTION]
> **MANDATORY: Python 3.12**
> `numba`/`librosa` crash with Access Violation (0xC0000005) on Python 3.14.
> Use `py -3.12` or install Python 3.12 from python.org.

## Status: COMPLETE

## Objective
Implement interactive waveforms that allow seeking by clicking and showing real-time playback progress with a vertical needle.

## Technical Requirements

### 1. Enhanced Footer Player (`ui/player.py`)
- [x] **Method Refactor**: Added public `seek(percentage: float)` method.
- [x] **Progress Callback**: Added `on_progress` callback parameter to `FooterPlayer.__init__`.
- [x] **Notify Progress**: In `_update_ui`, callback is invoked with progress (0.0 to 1.0).

### 2. Interactive Waveform in `SampleRow` (`ui/library.py`)
- [x] **Needle Overlay**: Added 2px wide vertical `CTkFrame` (accent color) inside `waveform_frame`.
- [x] **Click Detection**: Bound `<Button-1>` to both `waveform_label` and `waveform_frame`.
- [x] **Seek Calculation**: Click handler calculates percentage = `event.x / widget_width`.
- [x] **Seek Execution**: Calls `on_seek` callback with sample and percentage.
- [x] **Update Progress**: Implemented `set_progress(percentage)` using `place(relx=percentage)`.

### 3. Wiring in `SampleList` & `BeatflowApp`
- [x] **UI Updates**: `SampleList.update_progress()` updates the current playing row's needle.
- [x] **App Integration**: `BeatflowApp` connects `FooterPlayer.on_progress` to `SampleList.update_progress`.
- [x] **Seek Handling**: `BeatflowApp._on_seek_request()` calls `player.seek()`.

## Files Modified
- `ui/player.py` - Added `on_progress` callback, public `seek()` method
- `ui/library.py` - Added needle overlay, click detection, `set_progress()`, `update_progress()`
- `ui/app.py` - Added `_on_progress()` and `_on_seek_request()` handlers

## Verification
- Click on waveform -> Audio jumps to position.
- Look at waveform -> Needle moves as track plays.
- Switch tracks -> Needle resets/disappears on old track, appears on new one.

## Implementation Notes
- SoundCloud-style: Played portion of waveform is accent-colored, unplayed is gray
- Dual-waveform system: Generates both gray and accent versions
- Progress compositing: PIL image compositing based on progress percentage
- Click anywhere on waveform triggers seek, even if sample not currently playing
- Waveform resets to gray when track stops or changes
