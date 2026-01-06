# Beatflow Sample Browser

A modern, dark-themed audio sample browser built with Python and CustomTkinter. Designed for beatmakers to quickly browse, audition, and organize their sample libraries.

## Features

- 🎵 **Format Support**: WAV, MP3, OGG, FLAC, AIFF.
- 🌑 **Modern UI**: Dark mode interface with a sleek design.
- 📁 **Library Management**: Add/Remove multiple root folders.
- 🔍 **Search & Filter**: Real-time filtering by name, BPM, or Key.
- 🏷️ **Smart Tagging**: Auto-detects tags (e.g., "Kick", "Snare", "Loop") from filenames.
- 🎹 **Metadata**: Auto-detects BPM and Key from filenames.

## Installation

### Prerequisites

- Python 3.8 or higher
- [pip](https://pip.pypa.io/en/stable/installation/)

### Steps

1. **Clone the repository** (or download the source code):
   ```bash
   git clone <repository-url>
   cd Beatflow
   ```

2. **Install dependencies**:
   It is recommended to use a virtual environment.
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

## Usage

1. **Run the application**:
   ```bash
   python sample_browser.py
   ```

2. **Add Samples**:
   - Click the **+** button in the "Library Index" sidebar or **+ Scan Folders** in the main area.
   - Select a folder on your computer containing audio samples.

3. **Browse & Play**:
   - Click on a folder in the sidebar to view samples.
   - Click the **Play (▶)** button on any sample card to preview.
   - **Spacebar**: Toggle Play/Pause.
   - **Esc**: Stop playback.

## Configuration

Configuration is saved automatically to `beatflow_config.json` in the application directory. This file stores your added root folders.

## Requirements

- `customtkinter>=5.2.0`: For the UI.
- `pygame>=2.5.0`: For audio playback.
