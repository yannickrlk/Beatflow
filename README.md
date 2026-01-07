# Beatflow Sample Browser

A modern, high-performance audio sample browser for music producers. Organize, audition, and analyze your sample library with a sleek, cyber-premium interface.

> [!CAUTION]
> **MANDATORY: Python 3.12**
> Beatflow requires Python 3.12. Higher versions (like 3.14) currently crash due to `numba` and `librosa` compatibility issues.

## 🚀 Key Features

- 🎵 **Format Support**: WAV, MP3, OGG, FLAC, AIFF.
- 🌑 **Cyber-Premium UI**: Modern dark-themed interface with 8px grid system and smooth animations.
- 📁 **Library Management**: Add/Remove root folders with non-recursive browsing and sample counts.
- 🌊 **Real-time Waveforms**: Disk-cached waveform visualization for every sample.
- 🔍 **Global Search**: Search across your entire library or stay focused on a single folder.
- 🎛️ **Advanced Filters**: Filter by BPM range, musical Key (with enharmonic support), and file format.
- 🧠 **Smart Detection**: Automatic BPM and Key detection powered by `librosa`.
- 🏷️ **Metadata Management**: Edit ID3 tags, rename files, and view technical stats (bitrate, duration).
- ⭐ **Organization**: Favorites system and custom Collections to group your best sounds.
- 🖥️ **OS Integration**: Drag & drop support and Windows context menu integration ("Add to Beatflow").

## 🛠️ Installation

### 1. Prerequisites
- **Python 3.12** ([Download here](https://www.python.org/downloads/release/python-3120/))
- Git

### 2. Setup
```bash
# Clone the repository
git clone <repository-url>
cd Beatflow

# Install dependencies
py -3.12 -m pip install -r requirements.txt
```

## ⌨️ Usage

### Running the App
```bash
py -3.12 main.py
```

### Controls
- **Space**: Play/Pause toggle.
- **Esc**: Stop playback.
- **Left/Right Arrows**: Previous/Next track in current list.
- **Drag & Drop**: Drop a folder from your OS directly into the app to add it.

## ⚙️ Configuration
Settings are persisted in `beatflow_config.json`, including your library folders and volume levels. Use the **Gear (⚙️)** icon in the top bar to toggle Windows Shell integration.

## 📦 Requirements
- `customtkinter`: Modern UI components.
- `pygame`: Robust audio engine.
- `librosa`: Professional audio analysis.
- `mutagen`: Metadata and tag editing.
- `tkinterdnd2`: Advanced drag and drop support.

