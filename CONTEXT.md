# ProducerOS Project Context
> Last updated: 2026-01-20 (Phase 26 Complete - UX Improvements)
> For collaboration between Claude (implementation) and Gemini (brainstorming)

---

> [!CAUTION]
> **MANDATORY: Python 3.12**
> This project requires **Python 3.12** (not 3.13 or 3.14).
> `numba` and `librosa` crash with **Access Violation (0xC0000005)** on Python 3.14.
> Install Python 3.12 from: https://www.python.org/downloads/release/python-3120/

---

## 1. Project Overview

**ProducerOS** (formerly Beatflow) is a desktop sample browser and productivity suite for beatmakers/music producers. Think of it as the "operating system" for your creative workflow:
- Quick preview playback with tempo sync
- Metadata extraction (BPM, Key, Tags)
- Real waveform visualization
- Visual organization with collections
- Task management (Studio Flow)
- Network/contacts management
- Non-destructive audio editing (Lab)
- Business module (invoicing, finances, product catalog)

**Brand Info:**
- **Name**: ProducerOS
- **Tagline**: "Your Creative Command Center"
- **Website**: https://produceros.app
- **Support**: support@produceros.app

**Tech Stack:**
- **Python 3.12** (required - 3.14 crashes with librosa/numba)
- CustomTkinter (modern Tkinter wrapper)
- Pygame (audio playback)
- NumPy + Pillow (waveform generation)
- Pydub + imageio-ffmpeg (MP3/FLAC/OGG support with bundled ffmpeg)
- SQLite (metadata caching + task storage)
- JSON (config persistence)
- Librosa (BPM/Key detection)
- Numba (tempo sync)

---

## 2. Current File Structure

```
ProducerOS/
├── main.py                 # Entry point
├── produceros_config.json  # Persisted root folders & settings
├── produceros.db           # SQLite database (auto-generated)
├── requirements.txt        # Dependencies
├── .waveform_cache/        # Cached waveform images (auto-generated)
│
├── core/
│   ├── __init__.py
│   ├── version.py          # Version info (v1.0.0)
│   ├── config.py           # ConfigManager - handles JSON save/load
│   ├── database.py         # DatabaseManager - SQLite caching for metadata
│   ├── scanner.py          # LibraryScanner - file scanning & metadata
│   ├── waveform.py         # Waveform image generation
│   ├── analyzer.py         # AudioAnalyzer - BPM/Key detection (librosa)
│   ├── fingerprint.py      # Sonic fingerprinting for similarity matching
│   ├── shortcuts.py        # Global keyboard shortcuts listener
│   ├── lab.py              # LabManager - non-destructive audio processing
│   ├── sync.py             # SyncManager - time-stretch/pitch-shift for tempo sync
│   ├── exporter.py         # Exporter - ZIP bundling & kit generation
│   ├── client_manager.py   # ClientManager - Network contacts CRUD
│   ├── task_manager.py     # TaskManager - Daily tasks & project management
│   ├── shell_integration.py # Windows shell "Add to ProducerOS" context menu
│   ├── metadata_architect.py # Rule engine, regex renamer, duplicate finder
│   └── business.py         # BusinessManager - Invoices, transactions, products
│
├── ui/
│   ├── __init__.py
│   ├── theme.py            # COLORS dict, shared styling constants
│   ├── app.py              # ProducerOSApp - main window, layout
│   ├── sidebar.py          # Sidebar - navigation (Browse, Network, Studio Flow, Business)
│   ├── player.py           # FooterPlayer - Global playback controls + Sync
│   ├── dialogs.py          # MetadataEditDialog + Settings + MetadataArchitect
│   ├── tree_view.py        # LibraryTreeView - folder tree, collections UI
│   ├── library.py          # SampleList + SampleRow - sample display
│   ├── lab_drawer.py       # LabDrawer - interactive waveform editor UI
│   ├── network_view.py     # NetworkView - contacts/collaborators interface
│   ├── network_card.py     # ClientCard & ClientListRow - contact display
│   ├── network_dialogs.py  # AddClientDialog & EditClientDialog
│   ├── tasks_view.py       # TasksView - Studio Flow (4-tab layout)
│   ├── today_view.py       # TodayView - Daily quick todos + Focus Mode
│   ├── projects_view.py    # ProjectsView - Project management + Kanban
│   ├── focus_mode.py       # FocusModeWindow - Pomodoro timer
│   ├── productivity_dashboard.py  # Charts and insights
│   ├── calendar_view.py    # Month calendar + .ics export (modernized)
│   ├── task_dialogs.py     # Task/Project add/edit dialogs
│   ├── date_picker.py      # DatePickerWidget + CalendarPopup
│   ├── business_view.py    # BusinessView - Main tabbed container
│   ├── business_dashboard.py # Dashboard - Stats, goals, income breakdown
│   ├── invoices_view.py    # InvoicesView - Invoice list and editor
│   ├── ledger_view.py      # LedgerView - Transaction history
│   └── catalog_view.py     # CatalogView - Product/service management
│
├── legal/
│   ├── EULA.txt            # End User License Agreement
│   └── PRIVACY.md          # Privacy Policy (100% local, no data collection)
│
├── LICENSE                 # MIT License
├── NOTICE                  # Third-party attributions
├── BUSINESS_PLAN.md        # Full commercialization strategy
└── ProducerOS_installer.iss # Inno Setup installer script
```

---

## 3. Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         ProducerOSApp                           │
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

### MetadataArchitect (`core/metadata_architect.py`)
```python
from core.metadata_architect import (
    get_rule_engine, get_regex_renamer, get_duplicate_finder,
    PRESET_RULES, RENAME_PATTERNS
)

# Rule Engine - Smart Tagging
rule_engine = get_rule_engine()
rule_engine.check_rule(rule, sample)           # Check if sample matches rule
rule_engine.apply_rules_to_sample(sample)       # Apply matching rules, returns added tags
rule_engine.apply_rules_to_folder(path, cb)     # Apply rules to all samples in folder

# Regex Renamer - Batch Rename
renamer = get_regex_renamer()
renamer.preview_rename(path, pattern, replacement)      # Preview single rename
renamer.preview_batch_rename(paths, pattern, replacement)  # Preview multiple
renamer.rename_file(path, new_filename)         # Rename single file
renamer.batch_rename(renames, progress_cb)      # Batch rename with progress
renamer.undo_last_rename()                      # Undo most recent rename

# Duplicate Finder
finder = get_duplicate_finder()
finder.calculate_checksum(path)                 # Get MD5 checksum
finder.find_exact_duplicates(paths, progress_cb)    # Find by checksum
finder.find_near_duplicates(paths, dur_tol, size_tol)  # Find by duration+size
finder.safe_delete(path)                        # Move to trash or remove from DB

# Database Methods for Tagging
db.create_tagging_rule(name, type, field, op, value, tags)  # Create rule
db.get_tagging_rules(enabled_only=False)        # Get all rules
db.toggle_tagging_rule(rule_id)                 # Toggle enabled status
db.delete_tagging_rule(rule_id)                 # Delete rule
db.add_sample_tag(path, tag, source)            # Add tag to sample
db.get_sample_tags(path)                        # Get tags for sample
db.get_all_tags()                               # Get all unique tags with counts
db.get_samples_by_tag(tag)                      # Get samples with tag
```

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
- Supports: WAV (native), MP3/FLAC/OGG (via pydub + bundled ffmpeg)
- Uses `imageio-ffmpeg` for bundled ffmpeg binary (no system install needed)
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
✅ **MP3 Waveforms**: Bundled ffmpeg via imageio-ffmpeg (no system install needed)
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
✅ **Global Shortcuts**: System-wide Ctrl+Space (Play/Pause), Ctrl+Left/Right (Prev/Next)
✅ **Customizable Shortcuts**: Change shortcuts in Settings, persisted to config
✅ **Sonic DNA Matcher**: Spectral fingerprinting to find similar-sounding samples
✅ **Find Similar Button**: ∞ button on each sample row, also in right-click menu
✅ **Matching View**: Shows top 25 similar samples with "Clear Match" button
✅ **Recursive Folder Counts**: Folder tree shows total sample count including all subfolders
✅ **Beatflow Lab**: Inline sample editor with interactive waveform
✅ **Lab Trim/Fade**: Draggable handles for trim start/end, fade in/out sliders
✅ **Lab Normalize**: Toggle switch for -0.1dB normalization
✅ **Lab Preview**: Play/pause toggle for edited audio preview
✅ **Lab Export**: Export edited sample as WAV file
✅ **Lab Persistence**: Settings saved per sample in SQLite database
✅ **Universal Sync Engine**: Time-stretch samples to match target BPM
✅ **BPM Controls**: Global BPM input field with validation (40-240 range)
✅ **Tap Tempo**: Calculate BPM from tap intervals (last 4 taps)
✅ **Metronome**: Toggle metronome with visual beat pulse on BPM field
✅ **Sync Toggle**: SYNC button to enable/disable tempo-synced playback
✅ **Sync Indicator**: ⇄ icon on sample rows when playing synced
✅ **Metadata Architect**: Rule-based automation tool for library management
✅ **Smart Tagging Rules**: "If-This-Then-Tag" rules (e.g., "If folder contains '808', add 'Bass' tag")
✅ **Preset Rules**: 8 built-in presets for common tagging scenarios
✅ **Regex Renamer**: Batch rename files with regex patterns and preview
✅ **Rename Patterns**: 6 preset patterns for common cleanup tasks
✅ **Duplicate Finder**: Find exact (checksum) and near-exact (duration+size) duplicates
✅ **Safe Delete**: Remove duplicates to trash or just remove from library
✅ **Kit Builder ZIP Export**: Export collections to ZIP files
✅ **Collection Context Menu**: Right-click collections for export/delete options
✅ **Network Manager**: Contacts/collaborators feature with role tracking (Producer, Artist, Label, Engineer, Manager, Other)
✅ **Role Badges**: Color-coded role badges on contact cards (Purple=Producer, Pink=Artist, Blue=Label, etc.)
✅ **Multi-View Navigation**: Sidebar navigation between Browse and Network views
✅ **State Preservation**: Switching views preserves search/scroll state
✅ **Studio Flow UX Enhancements**: Advanced task management features
✅ **Completion Animations**: Smooth fade-out with checkmark on task completion
✅ **Keyboard Shortcuts**: Ctrl+T to quick-add tasks
✅ **Context Tags Visual**: Color-coded chips (@Studio=purple, @Mixing=blue, @Marketing=red, @Admin=gray)
✅ **Tag Selector UI**: Clickable tag buttons below task input for easy context selection
✅ **Priority Indicators**: Color-coded dots (Red=urgent, Orange=high, Gray=normal)
✅ **Smart Placeholders**: Rotating tips in quick add input
✅ **Sample Linking**: Right-click sample → "Create Task for This" with link indicator
✅ **Collection Projects**: Right-click collection → "Create Project from Collection"
✅ **Project Templates**: Pre-built templates (Album Release, Sample Pack, Client Beat)
✅ **Template Selection Dialog**: Choose template when creating new project
✅ **Focus Mode (Pomodoro)**: Fullscreen distraction-free timer with 25-minute sessions
✅ **Productivity Dashboard**: Charts showing tasks completed over time, context breakdown
✅ **Calendar View**: Month calendar with task indicators and navigation
✅ **Calendar Export**: Export tasks to .ics file for Google Calendar/Outlook
✅ **Focus Sessions Tracking**: Database tracking of Pomodoro sessions and time spent
✅ **Business Module**: Finance and invoicing for beat producers
✅ **Invoice Generator**: Create professional PDF invoices with items from catalog
✅ **Invoice Status Workflow**: Draft → Sent → Paid with auto-transaction creation
✅ **Transaction Ledger**: Track income and expenses with category filters
✅ **Product Catalog**: Beat licenses (MP3, WAV, Trackout, Exclusive) and services
✅ **Monthly Goals**: Set income goals and track progress with visual progress bar
✅ **Income Dashboard**: Revenue stats, income breakdown by category, recent transactions
✅ **CSV Export**: Export transactions to CSV for accounting software
✅ **DatePickerWidget**: Reusable calendar popup for date inputs (invoices, transactions)
✅ **Outstanding Tooltip**: Info tooltip on dashboard explaining unpaid invoices
✅ **Modern Calendar View**: Two-column layout with hover effects, task indicators, modern styling
✅ **Visual Polish (Phase 25)**: Dense pro-style layout like Ableton/VS Code
✅ **Font Loading**: Platform-aware font loading with fallbacks (Inter, JetBrains Mono)
✅ **Compact Spacing**: 4px grid system for denser UI
✅ **Row Striping**: Alternating row colors for better readability
✅ **Hover Effects**: All sample rows highlight on mouseover
✅ **Panel Borders**: 1px borders on sidebar and library tree for pro look
✅ **Active State Indicator**: Enhanced sidebar with accent bar + background on active tab
✅ **Phase 26 (UX Improvements)**: Professional UX patterns
✅ **Sidebar Section Headers**: Organized navigation with LIBRARY, WORKFLOW, CONNECTIONS headers
✅ **Keyboard Shortcuts**: Ctrl+1/2/3/4 for quick view switching (Browse, Studio Flow, Network, Business)
✅ **Standardized Tabs**: All views use CTkSegmentedButton for consistent tab navigation
✅ **Confirmation Dialogs**: Delete confirmations for rules, duplicates, collections, and contacts
✅ **Success Toasts**: Green notification toasts after save operations (contacts, metadata)
✅ **Loading Spinners**: Visual feedback during batch analysis and duplicate scanning
✅ **Real-time Validation**: Form fields show red/green borders based on validation state

---

## 6. Not Yet Implemented

### Phase 13.5 (Global Shortcuts) - COMPLETE
- [x] System-wide Play/Pause/Skip hotkeys (Ctrl+Space, Ctrl+Left/Right)
- [x] Customizable shortcuts in Settings dialog
- [x] Shortcuts persist to config file

### Phase 14 (Sonic DNA Matcher) - COMPLETE
- [x] Spectral fingerprinting using librosa + scipy
- [x] Shazam-style landmark hashing algorithm
- [x] Time-aligned matching for accuracy
- [x] Fingerprints stored in SQLite database
- [x] "Find Similar" button and context menu
- [x] Matching view with folder paths

### Phase 14.5 (Recursive Folder Counts) - COMPLETE
- [x] `db.get_folder_sample_count(path, recursive=True)` method
- [x] Counts samples in folder + all subfolders from database cache
- [x] Count badge displayed next to each folder in tree view
- [x] Fixed layout: count label packed before folder button for proper display

### Phase 15 (Beatflow Lab) - COMPLETE
- [x] `core/lab.py` - LabManager with librosa/soundfile processing
- [x] `ui/lab_drawer.py` - Interactive Canvas waveform with draggable handles
- [x] `lab_settings` table in SQLite for per-sample persistence
- [x] 🧪 Lab button on each SampleRow
- [x] Trim handles (green start, red end) with drag support
- [x] Fade in/out sliders (0-2000ms)
- [x] Normalize toggle (-0.1dB)
- [x] Preview button (play/pause toggle)
- [x] Export to WAV functionality
- [x] Lab drawer closes on folder/sample navigation

### Phase 16 (Universal Sync Engine) - COMPLETE
- [x] `core/sync.py` - SyncManager with librosa time-stretch/pitch-shift
- [x] Time-stretching using `librosa.effects.time_stretch`
- [x] Pitch-shifting using `librosa.effects.pitch_shift`
- [x] Temp file caching with 24-hour auto-cleanup
- [x] BPM input field (40-240 range) in footer player
- [x] Tap Tempo button (calculates from last 4 taps)
- [x] Metronome with visual beat pulse
- [x] SYNC toggle button for tempo-synced playback
- [x] Sync indicator (⇄) on sample rows when synced
- [x] Auto-reload track when toggling sync on/off

### Phase 17 (Metadata Architect) - COMPLETE
- [x] `core/metadata_architect.py` - RuleEngine, RegexRenamer, DuplicateFinder
- [x] Database tables: `tagging_rules`, `sample_tags`, `rename_history`
- [x] Smart Tagging Rules with 6 operators (contains, equals, greater_than, etc.)
- [x] 8 preset rules for common scenarios (808, kicks, vocals, loops, etc.)
- [x] Regex Renamer with preview before applying
- [x] 6 preset rename patterns (copy suffixes, BPM format, underscores, etc.)
- [x] Duplicate Finder with exact (MD5 checksum) and near-exact matching
- [x] Safe delete (move to trash) with database cleanup
- [x] Tools button (lightning icon) in topbar to access dialog

### Phase 18 (Kit Builder - ZIP Export) - COMPLETE
- [x] `core/exporter.py` - CollectionExporter class with ZIP bundling
- [x] Right-click context menu on Collections: "Export to ZIP...", "Delete Collection"
- [x] Windows Save As dialog with default filename from collection name
- [x] Success/failure message boxes with file path info
- [x] Handles missing files gracefully (skips and reports count)

### Phase 21.1 (Studio Flow UX Enhancements) - COMPLETE
- [x] Completion animations with fade-out and checkmark overlay
- [x] Keyboard shortcut Ctrl+T for quick add focus
- [x] Context tags visual with color-coded chips
- [x] Priority indicators with colored dots
- [x] Smart rotating placeholder tips
- [x] Sample linking (right-click → Create Task for This)
- [x] Collection projects (right-click → Create Project from Collection)
- [x] Project templates with pre-built workflows
- [x] Template selection dialog on new project

### Phase 25 (Visual Polish) - COMPLETE
- [x] Font loading system with platform-specific fallbacks
- [x] assets/fonts/ directory with README for custom fonts
- [x] Compact 4px grid spacing (xs=2, sm=4, md=8, lg=12, xl=16)
- [x] SIZING constants for consistent component dimensions
- [x] Alternating row colors (bg_card/bg_stripe)
- [x] Hover effects on all sample rows
- [x] 1px borders on Sidebar and Library Tree View
- [x] Enhanced sidebar active state (3px accent bar + background)

### Phase 26 (UX Improvements) - COMPLETE
- [x] Sidebar section headers (LIBRARY, WORKFLOW, CONNECTIONS)
- [x] Keyboard shortcuts Ctrl+1/2/3/4 for view switching
- [x] Standardized tab controls using CTkSegmentedButton
- [x] Confirmation dialogs before delete actions
- [x] Success toast notifications after saves
- [x] Loading spinners for batch operations
- [x] Real-time form validation with color feedback

### Planned Features (Roadmap)
- [ ] **Phase 20**: DAW Kit Export (Ableton .adg, FL Studio .fpc)
- [x] **Phase 21**: Studio Flow (Task Management) - COMPLETE
- [x] **Phase 21.1**: Studio Flow UX Enhancements - COMPLETE
- [x] **Phase 21.2**: Studio Flow Advanced Features (Focus Mode, Dashboard, Calendar) - COMPLETE
- [x] **Phase 24**: Business Module (Invoices, Ledger, Catalog) - COMPLETE
- [x] **Phase 24.5**: UX Polish (DatePicker, Tooltips, Calendar Redesign) - COMPLETE
- [x] **Phase 25**: Visual Polish (Dense Pro Layout) - COMPLETE
- [x] **Phase 26**: UX Improvements (Navigation, Feedback, Validation) - COMPLETE

### Lower Priority
- [ ] VST/AU Plugin Version

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

*Last implementation: Phase 14 (Global UI Polish & Performance) - Complete*

---

## Client Manager Components

### ClientCard (`ui/network_card.py`)
```python
class ClientCard(ctk.CTkFrame):
    """Premium glass card for client display."""
    # Shows: name, email, phone, social buttons, edit button
    # Hover: accent border color change

class ClientListRow(ctk.CTkFrame):
    """Compact table row for list view."""
    # Same data in horizontal layout
```

### Client Dialogs (`ui/client_dialogs.py`)
```python
class AddClientDialog(ctk.CTkToplevel):
    """Modal for adding clients (450x500)."""
    # Scrollable form with fields: name*, email, phone, instagram, twitter, website, notes
    # Buttons outside scroll area (always visible)

class EditClientDialog(ctk.CTkToplevel):
    """Modal for editing clients (450x520)."""
    # Pre-populated fields + Delete button
```

### Social Icon Unicode
| Platform  | Char | Unicode   | Hover Color |
|-----------|------|-----------|-------------|
| Instagram | ◎    | `\u25CE`  | #E1306C     |
| Twitter/X | ╳    | `\u2573`  | #000000     |
| Website   | ↗    | `\u2197`  | accent      |
| Edit      | ✎    | `\u270E`  | bg_hover    |

---

**UI Pattern**: All views (Browse, Clients) share consistent topbar design:
- Height: 56px, Background: `COLORS['bg_dark']`
- Search input on LEFT (280x40px, corner_radius=8)
- Context toggle next to search (width=160, height=32, `dynamic_resizing=False`)
- Primary action button on RIGHT ("+ Add Folder" or "+ Add Client")
