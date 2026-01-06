# Implementation Plan & Roadmap

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
  - Schema migration for existing databases
  - `toggle_favorite()`, `get_favorites()`, `get_favorites_count()`, `is_favorite()`, `set_favorite()` methods
- [x] **UI Library Index**: Add "Favorites" item at top of tree view with count badge.
- [x] **UI SampleRow**: Add "Star" icon/button for toggling.
  - Empty star (unfavorited) / Filled orange star (favorited)
  - Context menu options
- [x] **Logic**:
  - Update DB on toggle.
  - Favorites view shows all favorited samples.
  - Unfavoriting in favorites view removes from list.

---

## ❌ Cancelled: Phase 8 - Drag & Drop Integration
**Reason**: Deemed useless feature by user.
- [ ] ~~Research: Evaluate `tkinterdnd2` vs native solutions~~
- [ ] ~~Implementation: Enable drag source on SampleRow~~

## ✅ Completed: Phase 9 - Collections & Playlists

### Collections
**Goal**: Create custom user-defined collections beyond simple Favorites.
- [x] **Database Schema**:
  - `collections` table (id, name, created_at)
  - `collection_samples` junction table (collection_id, sample_path)
- [x] **Database Methods**:
  - `create_collection()`, `get_collections()`, `get_collection()`
  - `rename_collection()`, `delete_collection()`
  - `add_to_collection()`, `remove_from_collection()`
  - `get_collection_samples()`, `get_sample_collections()`
  - `is_in_collection()`
- [x] **UI**:
  - "COLLECTIONS" section in Library Index with sample counts
  - "+" button to create new collection
  - `NewCollectionDialog` for creating collections
  - `AddToCollectionDialog` for adding samples
  - Context menu: "Add to Collection..."
  - Click collection to view samples

---

## 📅 Phase 10: Advanced Audio Analysis
**Goal**: Automatically detect BPM and Key for samples missing this metadata.

- [ ] **Dependencies**: Integrate `librosa` or lighter alternative (consider performance impact).
- [ ] **Backend**:
  - `analyze_audio(path)` function.
  - Run analysis in background thread/process (computationally expensive).
  - Cache results in DB.
- [ ] **UI**:
  - "Analyze Missing Metadata" button/option.
  - Visual indicator for detected vs tag metadata.

## 📅 Phase 11: Advanced Filter Panel
**Goal**: complex filtering for heavy power users.

- [ ] **UI Components**:
  - Collapsible Filter Panel above sample list.
  - BPM Range Slider (Min-Max).
  - Key Selector (e.g., Cm, F#maj).
  - Duration Range.
- [ ] **Logic**:
  - Construct complex SQL queries or filter in-memory results effectively.
