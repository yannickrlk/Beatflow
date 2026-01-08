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

### 3. MP3 Waveform Fix (2026-01-07)
- [x] Added `imageio-ffmpeg` dependency (bundles ffmpeg binary)
- [x] Updated `core/waveform.py` to configure pydub with bundled ffmpeg
- [x] MP3/FLAC/OGG waveforms work out of the box (no system ffmpeg needed)

---

## ✅ Completed: Phase 13.5 - Global Shortcuts
**Goal**: System-wide hotkeys for playback control.

### Implementation (2026-01-07)
- [x] Created `core/shortcuts.py` with `GlobalShortcutListener` class
- [x] Default shortcuts: Ctrl+Space (Play/Pause), Ctrl+Left (Prev), Ctrl+Right (Next)
- [x] Used `pynput` library for global keyboard hook
- [x] Thread-safe UI updates via `app.after()`
- [x] Shortcuts configurable in Settings dialog
- [x] Shortcuts persist to `beatflow_config.json`
- [x] "Reset" button to restore defaults
- [x] Updated `main.py` for lifecycle management

---

## ✅ Completed: Phase 14 - Sonic DNA Matcher (DSP Similarity)
**Goal**: Instant sonic matching using traditional Digital Signal Processing.

### Implementation (2026-01-07)
- [x] Created `core/fingerprint.py` with Shazam-style landmark hashing
- [x] FFT spectrogram via `librosa.stft` + `librosa.amplitude_to_db`
- [x] Peak detection via `scipy.ndimage.maximum_filter`
- [x] Anchor-target pairing with fan-out for robustness
- [x] Time-aligned matching algorithm for accuracy
- [x] Added `fingerprints` table to SQLite database (indexed)
- [x] `db.save_fingerprints()`, `db.find_similar_samples()` methods
- [x] ∞ (Match) button added to each SampleRow
- [x] "Find Similar" option in right-click context menu
- [x] Matching view with "Clear Match" button
- [x] Background thread for fingerprint generation (no UI freeze)
- [x] Fingerprints cached in database for fast subsequent matches

---

## ✅ Completed: Phase 14.5 - Recursive Folder Counts
**Goal**: Show total sample count (including subfolders) next to each folder in the tree view.

### Implementation (2026-01-07)
- [x] Added `db.get_folder_sample_count(path, recursive=True)` to `core/database.py`
- [x] Uses SQL `LIKE` pattern matching with OS-native path separator
- [x] Counts samples from database cache (fast, no disk I/O)
- [x] Fixed tree view layout: count label packed before folder button
- [x] Count badge now properly visible even for long folder names

---

## ✅ Completed: Phase 15 - The "Beatflow Lab" (Sample Editor)
**Goal**: Basic non-destructive editing for quick preparation.

### Implementation (2026-01-07)
- [x] Created `core/lab.py` with `LabManager` class
  - Uses `librosa` + `soundfile` for audio processing (not pydub)
  - `apply_edits()` - trim, fade in/out, normalize
  - `export_temp()` - exports to timestamped temp WAV files
  - ffmpeg PATH configured via `imageio_ffmpeg` in `main.py`
- [x] Created `ui/lab_drawer.py` with interactive waveform
  - Draggable trim handles (green=start, red=end)
  - Fade in/out sliders (0-2000ms range)
  - Normalize toggle (-0.1dB peak normalization)
  - Preview button with play/pause toggle
  - Export button with file save dialog
  - Reset button to restore defaults
- [x] Added `lab_settings` table to `core/database.py`
- [x] Modified `ui/library.py` to add 🧪 Lab button

---

## ✅ Completed: Phase 16 - Universal Sync Engine (DSP)
**Goal**: Audition samples in context of the project's tempo and key.

### Implementation (2026-01-07)
- [x] Created `core/sync.py` with `SyncManager` class
- [x] Time-stretching via `librosa.effects.time_stretch` (phase vocoder)
- [x] Pitch-shifting via `librosa.effects.pitch_shift`
- [x] Temp file caching in `%TEMP%/beatflow_sync/` with 24-hour auto-cleanup
- [x] BPM input field (40-240 range) with validation
- [x] Tap Tempo button (calculates BPM from last 4 tap intervals)
- [x] Metronome toggle with visual beat pulse on BPM field
- [x] SYNC button to enable/disable tempo-synced playback
- [x] Sync indicator (⇄) on sample rows when playing synced
- [x] Auto-reload track when toggling sync state

---

## ✅ Completed: Phase 17 - The "Metadata Architect" (Rule-Based Automation)
**Goal**: Logic-driven library enrichment without AI.

### Implementation (2026-01-08)
- [x] Created `core/metadata_architect.py` with three main classes:
  - `RuleEngine` - Apply "If-This-Then-Tag" rules to samples
  - `RegexRenamer` - Batch rename files with regex patterns
  - `DuplicateFinder` - Find exact and near-exact duplicates
- [x] Database tables: `tagging_rules`, `sample_tags`, `rename_history`
- [x] **Smart Tagging Rules**: 6 operators, 8 preset rules
- [x] **Regex Renamer**: Preview + apply, 6 preset patterns
- [x] **Duplicate Finder**: MD5 checksum + duration/size matching
- [x] UI: MetadataArchitectDialog with 3 tabs (Rules, Renamer, Duplicates)
- [x] Tools button (lightning icon) in topbar for quick access

---

## ✅ Completed: Phase 18 - The "Kit Builder" (ZIP Export)
**Goal**: Export collections as ZIP archives for sharing and backup.

### Implementation (2026-01-08)
- [x] Created `core/exporter.py` with `CollectionExporter` class
  - `export_to_zip(collection_id, output_path)` - Export collection to ZIP
  - `export_samples_to_zip(paths, output_path)` - Export arbitrary sample list
  - `validate_files(samples)` - Check which files exist on disk
- [x] Right-click context menu on collections: "Export to ZIP...", "Delete Collection"
- [x] Windows Save As dialog with default filename from collection name
- [x] Success/failure message boxes with file path info
- [x] ZIP compression using `zipfile.ZIP_DEFLATED`

---

## 🔄 Planned: Phase 19 - DAW Kit Export
**Goal**: Create drum kit presets for popular DAWs.
- [ ] **Ableton Live**: Create `.adg` Drum Rack files
- [ ] **FL Studio**: Create `.fpc` presets
- [ ] **Logic Pro**: Create `.patch` files for Drum Machine Designer
