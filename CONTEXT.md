# Beatflow Project Context
> Last updated: 2026-01-07 (Phase 13 - Waveform Interaction - Complete)
> For collaboration between Claude (implementation) and Gemini (brainstorming)

---

> [!CAUTION]
> **MANDATORY: Python 3.12**
> This project requires **Python 3.12** (not 3.13 or 3.14).
> `numba` and `librosa` crash with **Access Violation (0xC0000005)** on Python 3.14.
> Install Python 3.12 from: https://www.python.org/downloads/release/python-3120/

---

## 1. Project Overview

**Beatflow** is a desktop sample browser for beatmakers/music producers. Think of it like a file explorer specifically designed for audio samples with:
- Quick preview playback
- Metadata extraction (BPM, Key, Tags)
- Real waveform visualization
- Visual organization

**Tech Stack:**
- **Python 3.12** (required - 3.14 crashes with librosa/numba)
- CustomTkinter (modern Tkinter wrapper)
- Pygame (audio playback)
- NumPy + Pillow (waveform generation)
- Pydub (multi-format audio support)
- JSON (config persistence)

---

## 2. Current File Structure

```
Beatflow/
├── main.py                 # Entry point
├── beatflow_config.json    # Persisted root folders
├── requirements.txt        # Dependencies
├── .waveform_cache/        # Cached waveform images (auto-generated)
│
├── core/
│   ├── __init__.py
│   ├── config.py           # ConfigManager - handles JSON save/load
│   ├── database.py         # DatabaseManager - SQLite caching for metadata
│   ├── scanner.py          # LibraryScanner - file scanning & metadata
│   ├── waveform.py         # Waveform image generation
│   └── analyzer.py         # AudioAnalyzer - BPM/Key detection (librosa)
│
└── ui/
    ├── __init__.py
    ├── theme.py            # COLORS dict, shared styling constants
    ├── app.py              # BeatflowApp - main window, layout
    ├── sidebar.py          # Sidebar - navigation (Browse + Settings)
    ├── player.py           # FooterPlayer - Global playback controls
    ├── dialogs.py          # MetadataEditDialog - edit sample metadata
    ├── tree_view.py        # LibraryTreeView - folder tree with expand/collapse, context menu
    └── library.py          # SampleList + SampleRow - sample display & playback
```

---

## 3. Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         BeatflowApp                             │
│  ┌──────────┐  ┌─────────────────┐  ┌────────────────────────┐  │
│  │ Sidebar  │  │ LibraryTreeView │  │      SampleList        │  │
│  │          │  │                 │  │  ┌──────────────────┐  │  │
│  │ - Nav    │  │ - FolderNode(s) │  │  │   SampleRow(s)   │  │  │
│  │ - Logo   │  │ - Expand/Collap │  │  │   - Play btn     │  │  │
│  │          │  │ - Select folder │──┼──│   - Metadata     │  │  │
│  └──────────┘  └─────────────────┘  │  │   - Waveform img │  │  │
│                                      │  └──────────────────┘  │  │
│                                      └────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────────────┐
              │            Core Layer                 │
              │  ConfigManager | LibraryScanner |     │
              │            WaveformGenerator          │
              └───────────────────────────────────────┘
```

---

## 4. Key Components

### ConfigManager (`core/config.py`)
```python
config_manager.root_folders      # List of root folder paths
config_manager.add_folder(path)  # Add + persist
config_manager.remove_folder(path)
```

### DatabaseManager (`core/database.py`)
```python
from core.database import get_database

db = get_database()              # Singleton instance
db.get_sample(path)              # Get cached sample or None
db.get_sample_if_valid(path, mtime, size)  # Cache hit only if not modified
db.upsert_sample(sample_dict)    # Insert or update single sample
db.upsert_samples(samples_list)  # Bulk insert/update
db.remove_sample(path)           # Delete from cache
db.clear_all()                   # Clear entire cache

# Favorites
db.toggle_favorite(path)         # Toggle favorite status, returns new bool
db.get_favorites()               # Get all favorite samples as list
db.get_favorites_count()         # Get count of favorites
db.is_favorite(path)             # Check if sample is favorited
db.set_favorite(path, bool)      # Set favorite status explicitly

# Collections
db.create_collection(name)       # Create new collection, returns ID
db.get_collections()             # Get all collections with sample counts
db.get_collection(id)            # Get collection by ID
db.rename_collection(id, name)   # Rename a collection
db.delete_collection(id)         # Delete collection and associations
db.add_to_collection(id, path)   # Add sample to collection
db.remove_from_collection(id, path)  # Remove sample from collection
db.get_collection_samples(id)    # Get all samples in a collection
db.get_sample_collections(path)  # Get all collections containing a sample
db.is_in_collection(id, path)    # Check if sample is in collection
```
- Auto-creates `beatflow.db` in project root
- Cache validation via file mtime and size
- Thread-safe with `check_same_thread=False`

### LibraryScanner (`core/scanner.py`)
```python
LibraryScanner.scan_folder(path, recursive=False)  # Returns List[Dict]
LibraryScanner.get_subfolders(path)                # Returns List[str]
LibraryScanner.count_samples_shallow(path)         # Returns int
LibraryScanner.extract_tags(name)                  # Returns List[str]

# Sample dict structure:
{
    'name': 'Kick_Hard_140bpm',
    'filename': 'Kick_Hard_140bpm.wav',
    'path': 'C:/Samples/Drums/Kick_Hard_140bpm.wav',
    'bpm': '140',
    'key': '',
}
```

### WaveformGenerator (`core/waveform.py`)
```python
generate_waveform_image(
    file_path: str,
    width: int = 200,
    height: int = 40,
    color: str = "#444444",
    bg_color: str = "transparent",
    use_cache: bool = True
) -> PIL.Image

clear_cache()  # Clear all cached waveforms
```
- Supports: WAV (native), MP3/FLAC/OGG (via pydub)
- Caches images in `.waveform_cache/` directory
- Uses peak-based downsampling for visualization

### AudioAnalyzer (`core/analyzer.py`)
```python
from core.analyzer import get_analyzer, analyze_audio

# Singleton instance
analyzer = get_analyzer()

# Synchronous analysis
result = analyze_audio(filepath)  # Returns {'bpm': '120', 'key': 'Am'}

# Async analysis with callback
analyzer.analyze_file(filepath, callback=on_result)

# Batch analysis with progress
analyzer.analyze_batch(filepaths, progress_callback, completion_callback)

# Database methods
db.update_analysis(path, detected_bpm, detected_key)
db.get_analysis(path)  # Returns {detected_bpm, detected_key, analysis_date}
db.get_samples_needing_analysis(folder_path)
db.clear_analysis(path)  # Allow re-analysis
```
- Uses librosa for BPM detection (beat tracking) and Key detection (chroma features)
- Background thread processing (computationally expensive)
- Results cached in SQLite database
- Visual indicator: Purple color with ≈ symbol for detected values

### Theme (`ui/theme.py`)
```python
COLORS = {
    'bg_darkest': '#0a0a0a',   # Sidebar
    'bg_dark': '#111111',       # Tree view
    'bg_main': '#1a1a1a',       # Main content
    'bg_card': '#1e1e1e',
    'bg_hover': '#2a2a2a',
    'accent': '#ff6b35',        # Orange
    'fg': '#ffffff',
    'fg_secondary': '#b0b0b0',
    'fg_dim': '#666666',
    'fg_muted': '#444444',
}
```

### FooterPlayer (`ui/player.py`)
```python
FooterPlayer(parent, on_volume_change=None)
player.load_track(sample, playlist, index)  # Load sample with playlist context
player.play()                                # Start/resume playback
player.pause()                               # Pause playback
player.stop()                                # Stop playback
player.toggle_play_pause()                   # Toggle play/pause
player.set_volume(0.7)                       # Set volume (0.0-1.0)
```
- Seek slider with position offset tracking
- Volume slider with icon feedback
- Next/Prev buttons with playlist navigation
- Auto-advances to next track on completion

### SampleRow (`ui/library.py`)
- Single sample display row
- Play/pause button (circular)
- Filename, format badge, BPM, Key, Tags
- **Real waveform image** (loaded async via threading)

### SampleList (`ui/library.py`)
```python
SampleList(master, on_play_request=None, on_edit_request=None, on_favorite_change=None)
sample_list.load_folder(path)              # Load samples from folder
sample_list.load_favorites()               # Load all favorite samples
sample_list.filter_samples(query)          # Filter by search query
sample_list.clear_samples()                # Clear the sample list
```
- Delegates playback to FooterPlayer via callback
- Maintains filtered_samples for playlist context
- Star button on each row for toggling favorites

---

## 5. Current State (What Works)

✅ Add root folders via file dialog
✅ Folder tree with expand/collapse navigation
✅ Non-recursive folder browsing
✅ Sample count per folder
✅ Audio playback (play/pause via Pygame)
✅ Metadata extraction (BPM, Key from filename)
✅ Tag extraction (keyword-based)
✅ **Real waveform visualization with caching**
✅ **Async waveform loading (no UI freeze)**
✅ **Global Footer Player (fully functional)**
✅ **Seek bar with accurate position tracking**
✅ **Volume persistence (saved to config.json)**
✅ **Next/Prev track navigation**
✅ **Keyboard shortcuts (Space, Escape, Left, Right)**
✅ **Search bar filtering** with fuzzy matching (filename, BPM, Key, Artist, Album, Genre)
✅ **Real metadata reading (mutagen)**: Artist, Album, Genre, Year, Bitrate
✅ **Duration display** in sample rows and player
✅ **SQLite caching**: Fast re-scans via mtime/size validation
✅ **Tag editing**: Right-click → Edit Metadata (MP3, FLAC, OGG, AIFF)
✅ **Context menu**: Open File Location, Copy Path, Edit Metadata, Add to Favorites, Add to Collection, Analyze BPM/Key
✅ **Favorites system**: Star button on samples, Favorites in Library Index with count badge
✅ **Collections system**: Create collections, add samples, view collection contents
✅ **Audio Analysis**: Automatic BPM and Key detection using librosa (right-click → Analyze BPM/Key)
✅ **Batch Analysis**: "Analyze All" button to analyze all samples in current view
✅ **Visual indicator**: Purple color (≈) for detected BPM/Key vs embedded metadata
✅ **Play/Pause Toggle**: Click play button toggles pause when same sample is playing
✅ **MP3 Waveforms**: Librosa fallback when ffmpeg unavailable
✅ **Clean UI**: Simplified sidebar (Browse only), clean topbar (Search + Add Folder)
✅ **Empty state guidance**: "Add your sample folders to get started" for first-time users
✅ **Folder removal**: Right-click root folders → "Remove from Library"
✅ **Sorting**: Sort dropdown (Name A-Z/Z-A, BPM Low-High/High-Low, Key, Duration)
✅ **Pro UX Design**: Cyber-Premium color palette, 8px grid spacing, monospaced data fonts
✅ **Playing State**: Visual feedback with accent border and highlighted background
✅ **Sidebar Accent**: Vertical accent bar indicator for active navigation
✅ **Global Library Search**: Search across all folders with Folder/Library toggle
✅ **Search Result Context**: Shows folder path in global search, "Go to Folder" action
✅ **Advanced Filters**: Collapsible filter panel with BPM range, Key selector, Format filter
✅ **Filter Enhancements**: Enharmonic key support (C# = Db), AND logic with text search
✅ **CLI Folder Support**: Pass folder path via command line argument
✅ **Windows Shell Integration**: "Add to Beatflow" context menu (opt-in via Settings)
✅ **Drag & Drop**: Drop folders from Explorer to add to library
✅ **Settings Dialog**: Gear icon in topbar, shell integration toggle
✅ **Recently Played**: Tracks last 50 played samples in sidebar
✅ **Smart BPM/Key Extraction**: Priority: filename → analysis → manual edit
✅ **Improved Filename Parsing**: Handles Dminor, F#Minor, DbMajor, 120bpm, etc.
✅ **Background Batch Analysis**: "Analyze All" runs in background thread (no UI freeze)
✅ **Real-time UI Updates**: Analysis results appear immediately without reload
✅ **Edit Detected Values**: Right-click → Edit Metadata shows detected values for editing
✅ **Waveform Click-to-Seek**: Click anywhere on waveform to jump to that position
✅ **SoundCloud-style Progress**: Played portion shows in accent color, unplayed in gray (dual-waveform compositing)
✅ Dark theme UI (deep blue-black tones)
✅ Persistent config (including sort preferences)

---

## 6. Not Yet Implemented

### Lower Priority
- [ ] AI-powered sample recommendations
- [ ] Global hotkeys (system-wide)

---

## 7. How to Run

```bash
cd Beatflow

# IMPORTANT: Use Python 3.12 (not 3.14 - crashes with librosa/numba)
py -3.12 -m pip install -r requirements.txt
py -3.12 main.py

# Verify dependencies work:
py -3.12 verify_deps.py

# Or with a folder argument:
py -3.12 main.py "C:\Path\To\Samples"
```

**Note**: `mutagen` is required for metadata, `tkinterdnd2` for drag & drop.

---

## 8. Documentation Files

| File | Purpose |
|------|---------|
| `CONTEXT.md` | Full project overview (this file) |
| `CURRENT_TASK.md` | Current task + questions for Gemini |
| `implementation_plan.md` | Roadmap with completed/pending items |
| `README.md` | User-facing installation guide |

---

*Last implementation: Phase 13 (Complete) - Waveform Interaction*
