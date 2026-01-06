# Current Task: Phase 10 - Advanced Audio Analysis

## Objective
Implement automatic BPM and Key detection for audio samples that are missing this metadata.

## Context
Many samples don't have BPM or Key embedded in their metadata or filename. Automatic detection would help users organize and find samples more effectively.

## Requirements
- **Library**: `librosa` (primary candidate) or lighter alternative
- **Performance**: Run analysis in background thread (computationally expensive)
- **Storage**: Cache results in SQLite database

## Plan
1. [ ] Research and choose audio analysis library (librosa vs alternatives)
2. [ ] Implement `analyze_audio(path)` function for BPM/Key detection
3. [ ] Add background thread processing for analysis
4. [ ] Add "Analyze" button/option in UI
5. [ ] Update database schema if needed for detected metadata
6. [ ] Add visual indicator for detected vs embedded metadata
