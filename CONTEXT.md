# Beatflow Project Context
> Last updated: 2026-01-06
> For collaboration between Claude (implementation) and Gemini (brainstorming)

---

## 1. Project Overview

**Beatflow** is a desktop sample browser for beatmakers/music producers. Think of it like a file explorer specifically designed for audio samples with:
- Quick preview playback
- Metadata extraction (BPM, Key, Tags)
- Real waveform visualization
- Visual organization

**Tech Stack:**
- Python 3.11+
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
│   └── waveform.py         # Waveform image generation
│
└── ui/
    ├── __init__.py
    ├── theme.py            # COLORS dict, shared styling constants
    ├── app.py              # BeatflowApp - main window, layout
    ├── sidebar.py          # Sidebar - navigation (Dashboard, Samples, etc.)
    ├── player.py           # FooterPlayer - Global playback controls
    ├── dialogs.py          # MetadataEditDialog - edit sample metadata
    ├── tree_view.py        # LibraryTreeView - folder tree with expand/collapse
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

### WaveformGenerator (`core/waveform.py`) - NEW
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
✅ **Context menu**: Open File Location, Copy Path, Edit Metadata, Add to Favorites
✅ **Favorites system**: Star button on samples, Favorites in Library Index with count badge
✅ Dark theme UI
✅ Persistent config

---

## 6. Not Yet Implemented

### Medium Priority
- [ ] Drag & drop to DAW
- [ ] Advanced filter panel (BPM range, Key selector)

### Lower Priority
- [ ] AI-powered sample recommendations
- [ ] Auto BPM/Key detection

---

## 7. How to Run

```bash
cd Beatflow
pip install -r requirements.txt
python main.py
```

**Note**: `mutagen` is now required for metadata.

---

## 8. Documentation Files

| File | Purpose |
|------|---------|
| `CONTEXT.md` | Full project overview (this file) |
| `CURRENT_TASK.md` | Current task + questions for Gemini |
| `implementation_plan.md` | Roadmap with completed/pending items |
| `README.md` | User-facing installation guide |

---

*Last implementation: Favorites System (Phase 7 completed)*
