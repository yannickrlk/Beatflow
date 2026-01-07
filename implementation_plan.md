# Implementation Plan & Roadmap

> [!CAUTION]
> **MANDATORY ENVIRONMENT: PYTHON 3.12**
> The project crashes with **Access Violation (0xC0000005)** on Python 3.14.
> `numba` and `librosa` do not yet support Python 3.14. All developers MUST use Python 3.12.
>
> **Install Python 3.12**: https://www.python.org/downloads/release/python-3120/
> **Run with**: `py -3.12 main.py` or `py -3.12 verify_deps.py` to test

---

## ✅ Completed: Phase 1 & 2 (Architecture & Foundation)
- [x] **Installation Setup**: `README.md` created, `requirements.txt` pinned.
- [x] **Modular Architecture**: Refactored monolithic `sample_browser.py` into:
  - `main.py`: Entry point.
  - `core/`: Business logic (`scanner.py`, `config.py`) isolated from UI.
  - `ui/`: Modern CustomTkinter layout (`app.py`, `library.py`, `sidebar.py`, `tree_view.py`).
- [x] **TreeView Navigation**: Implemented recursive folder hierarchy (Root -> Subfolder) for browsing.
- [x] **Scan Logic**: Non-recursive by default, shows only files in selected folder.

---

## ✅ Completed: Phase 3.1 - Real Waveform Visualization
- [x] **Dependencies**: Added `numpy`, `Pillow`, `pydub` to `requirements.txt`.
- [x] **Backend (`core/waveform.py`)**:
  - `generate_waveform_image(file_path, width, height, color)` -> Returns PIL.Image
  - Supports WAV (native) and MP3/FLAC/OGG (via pydub)
  - Disk caching in `.waveform_cache/` directory
  - Peak-based downsampling for accurate visualization
- [x] **Frontend (`ui/library.py`)**:
  - `SampleRow` loads waveforms asynchronously (background thread)
  - Shows text placeholder until image loads
  - Uses `CTkImage` for display

---

## ✅ Completed: Phase 3.2 - Player & Search

### 1. Advanced Audio Playback
**Goal**: Finish the Footer Player logic.
- [x] Create Global Footer Player UI (`ui/player.py`)
- [x] Integrate Player into App layout
- [x] Refactor `SampleList` to delegate playback to Player
- [x] **Seek Bar Logic**: Position offset tracker for accurate time display
- [x] **Volume Persistence**: Volume saved to `beatflow_config.json`
- [x] **Playlist Navigation**: Next/Prev buttons work with folder context
- [x] **Keyboard Shortcuts**: Space (Play/Pause), Escape (Stop), Left/Right (Prev/Next)

### 2. Search & Filtering
**Goal**: Find samples quickly.
- [x] Wire up the search bar to `SampleList.filter_samples()`
- [x] Filter by filename, name, BPM, Key
- [x] Fuzzy search support (optional enhancement)

---

## ✅ Completed: Phase 4.1 - Real Metadata

### Metadata & Tagging
**Goal**: Read real file tags with mutagen.
- [x] Integrate `mutagen` for ID3/metadata reading
- [x] Read: title, artist, album, genre, year, duration, bitrate, sample_rate
- [x] Display Artist, Album, Bitrate, Duration in SampleRow
- [x] Show artist info in FooterPlayer

---

## ✅ Completed: Phase 4.2 - Database Optimization

### Database Caching
**Goal**: Speed up large libraries.
- [x] Implement `sqlite3` caching for scanned files (`core/database.py`)
- [x] Store metadata in DB to avoid re-scanning
- [x] Cache validation via file mtime and size
- [x] Bulk insert optimization with `executemany`
- [x] Singleton pattern for database instance
- [x] Store waveform cache paths in DB (optional future enhancement)

---

## ✅ Completed: Phase 5 - Tag Editing

### Tag Editing
**Goal**: Allow users to edit sample metadata.
- [x] Right-click context menu on SampleRow (Edit Metadata, Open File Location, Copy Path)
- [x] `MetadataEditDialog` in `ui/dialogs.py`
- [x] `save_metadata()` function in `core/scanner.py` (supports MP3, FLAC, OGG, AIFF)
- [x] Database cache update after edit
- [x] UI refresh after save

---

## ✅ Completed: Phase 6 - Search Enhancements

### Search Enhancements
- [x] Fuzzy search support (typo tolerance, partial matching)
- [x] Search by artist, album, genre, title
- [x] Multi-word search (AND logic)

---

## ✅ Completed: Phase 7 - Favorites System

### Favorites
**Goal**: Mark and quickly access favorite samples.
- [x] **Database**: Add `is_favorite` boolean column to `samples` table.
- [x] **UI Library Index**: Add "Favorites" item at top of tree view with count badge.
- [x] **UI SampleRow**: Add "Star" icon/button for toggling.
- [x] **Logic**: Update DB on toggle; Favorites view shows all favorited samples.

---

## ❌ Cancelled: Phase 8 - Drag & Drop Integration
**Reason**: Deemed useless feature by user.

---

## ✅ Completed: Phase 9 - Collections & Playlists

### Collections
**Goal**: Create custom user-defined collections beyond simple Favorites.
- [x] **Database Schema**: `collections` and `collection_samples` junction table.
- [x] **UI**: COLLECTIONS section, create/rename/delete, add samples via dialogue.

---

## ✅ Completed: Phase 10 - Finetuning & Stabilization
**Goal**: Polish existing features and fix reported bugs before adding more complexity.

### 1. Audio Logic & MP3 Support
- [x] **Play/Pause Toggle**: SampleRow play button now toggles play/pause when same sample is playing
- [x] **MP3 Waveforms**: Added librosa fallback in `core/waveform.py` when pydub/ffmpeg unavailable
- [x] **Batch Analysis**: Added "Analyze All" button to analyze all samples in current view

### 2. UI & Responsiveness
- [x] **Layout Fixes**: Fixed SampleList header using proper grid layout
- [x] **Dynamic Sizing**: Improved topbar layout with responsive grid columns

### 3. Performance & Optimization
- [x] **Async Loading**: Waveforms and analysis already use background threads
- [x] **SQLite Caching**: Metadata and analysis results cached for fast reload

---

## ✅ Phase 11: UX Improvements (Persona-Driven)
**Goal**: Fix critical UX issues identified by persona testing (Marcus the Beatmaker).
**Initial Score**: 6.5/10 → **Final Score**: 8.8/10 (Target was 8.5/10)

### ✅ Priority 1: Clean First-Time Experience (HIGH IMPACT, LOW EFFORT)
- [x] Remove non-functional sidebar nav (Dashboard, Clients, Projects, Dev RoadMap)
- [x] Add empty state with "Add your sample folders" guidance
- [x] Remove unused topbar elements (bell, avatar, New Project button)
- [x] Add right-click "Remove from Library" on folders

### ✅ Priority 2: Add Sorting (HIGH IMPACT, MEDIUM EFFORT)
- [x] Add sort dropdown: Name, BPM, Key, Duration
- [x] Implement sorting logic (handle missing values)
- [x] Persist sort preference to config

### ✅ Priority 3: Pro UX Design System (HIGH IMPACT, MEDIUM EFFORT)
- [x] Cyber-Premium color palette (deep blue-black tones)
- [x] 8px grid spacing system
- [x] Monospaced fonts for BPM/Key data
- [x] Playing state visual indicators (border + background)
- [x] Sidebar vertical accent indicator
- [x] Tree view 16px indentation with thin arrows
- [x] Skeleton waveform loading state

### ✅ Priority 4: Global Library Search (HIGH IMPACT, HIGH EFFORT)
- [x] Add "Search All" vs "Current Folder" toggle
- [x] Implement database-wide search query
- [x] Display cross-folder results with path context
- [x] "Go to Folder" context menu action

### ✅ Priority 5: Advanced Filters (MEDIUM IMPACT, MEDIUM EFFORT)
- [x] Collapsible filter panel with toggle button
- [x] BPM range filter (min/max inputs)
- [x] Key selector dropdown (24 keys + enharmonic support)
- [x] Format filter (WAV, MP3, FLAC, OGG, AIFF checkboxes)
- [x] Combine with text search (AND logic)
- [x] Clear filters button

---

## ✅ Phase 11 Complete
All UX improvements have been implemented.
- **Target Score**: 8.5/10
- **Achieved Score**: 8.8/10
- **Evaluation**: See `MARCUS_UX_EVAL.md` for detailed persona testing results

---

## ✅ Phase 12: Workflow & OS Integration (Complete)
**Goal**: Make Beatflow a seamless part of the producer's operating system.

### ✅ 1. Direct Folder Integration (OS Level)
- [x] **CLI Support**: `main.py` parses `sys.argv` for folder paths
- [x] **Windows Context Menu**: `core/shell_integration.py` adds "Add to Beatflow" via HKEY_CURRENT_USER
- [x] **Settings Dialog**: Toggle for shell integration with status feedback
- [x] **Drag & Drop**: tkinterdnd2 DnDWrapper mixin integration for folder dropping
- [x] **Non-recursive scan**: Dropped folders show only direct files (not subfolder contents)
- [x] **Tree view selection**: Dropped folders auto-selected in Library Index

### ✅ 3. Productivity Features
- [x] **Recently Used**: `recent_samples` table, auto-tracks last 50 played

---

## ✅ Phase 12.5: Audio Analysis & BPM/Key Improvements (Complete)
**Goal**: Improve BPM/Key detection accuracy and user experience.

### ✅ 1. Python 3.12 Compatibility
- [x] Identified librosa/numba crash on Python 3.14 (Access Violation 0xC0000005)
- [x] Updated all documentation with Python 3.12 requirement
- [x] Added `verify_deps.py` for dependency verification

### ✅ 2. Analysis UI & Performance
- [x] **Real-time UI updates**: Analysis results appear immediately without reload
- [x] **Background batch analysis**: "Analyze All" runs in background thread (no freeze)
- [x] **Player track switching**: Fixed player not switching when clicking different sample
- [x] **Player info**: Shows detected BPM/Key in footer player

### ✅ 3. Improved BPM Detection
- [x] Extended analysis duration from 30s to 60s for better accuracy
- [x] Using `librosa.beat.beat_track()` instead of simple tempo estimation
- [x] Half/double tempo correction (constrains to 70-180 BPM range)
- [x] Fallback to simpler method if beat_track fails

### ✅ 4. Smart Filename Extraction
- [x] **Priority system**: Filename → Analysis → Manual edit
- [x] **Key patterns**: Dminor, F#Minor, DbMajor, Aminor, Am, F#m, etc.
- [x] **BPM patterns**: 120bpm, BPM120, _120_, etc. (validates 60-200 range)
- [x] **Cache override**: Filename extraction runs even for cached files

### ✅ 5. Edit Detected Values
- [x] MetadataEditDialog shows detected values if no embedded values
- [x] Labels show "(detected)" in purple for detected values
- [x] User can edit and save detected BPM/Key

---

## ✅ Completed: Phase 13 - Waveform Interaction
**Goal**: Enhanced waveform interactivity.

### 1. Click to Seek
- [x] Click anywhere on waveform to seek to that position
- [x] Works with `FooterPlayer.seek()` method
- [x] Click handler on both `waveform_label` and `waveform_frame`

### 2. SoundCloud-Style Progress
- [x] Dual-waveform system: gray (unplayed) + accent (played)
- [x] Real-time composite image updates based on progress
- [x] Progress callback from `FooterPlayer.on_progress`
- [x] Played portion shows in accent color, unplayed in gray

### Lower Priority (Deferred)
- [ ] **Global Hotkeys**: System-wide Play/Pause/Skip (Windows API)

