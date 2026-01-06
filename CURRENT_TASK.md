# Current Task: Search Enhancements (Phase 6)

## Context
The current search only filters by exact substring matching on filename, BPM, and Key.
Users need more powerful search capabilities to find samples quickly in large libraries.

## Objectives for Claude

### 1. Fuzzy Search
- **File**: `ui/library.py`
- **Task**: Implement fuzzy matching for sample search
  - Use a simple fuzzy matching algorithm (e.g., Levenshtein distance or partial matching)
  - Consider using `rapidfuzz` library for performance
  - Allow typos and partial matches

### 2. Extended Search Fields
- **File**: `ui/library.py` → `filter_samples()` method
- **Task**: Search across more metadata fields:
  - Artist
  - Album
  - Genre
  - Title (already via name)

### 3. Advanced Filter Panel (Optional)
- **File**: `ui/library.py` or new `ui/filters.py`
- **Task**: Add a collapsible filter panel with:
  - BPM range slider (e.g., 80-180 BPM)
  - Key selector (dropdown or checkboxes)
  - Format filter (WAV, MP3, etc.)
  - Duration range

## Notes
- Consider performance for large libraries (1000+ samples)
- Keep the simple search bar for quick filtering
- Advanced filters should be optional/collapsible

## Previous Phase Completed
Phase 5 - Tag Editing:
- Right-click context menu on SampleRow
- MetadataEditDialog for editing metadata
- save_metadata() function supports MP3, FLAC, OGG, AIFF
- Database cache updates after edit
