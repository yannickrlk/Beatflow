"""
Beatflow Sample Browser
A modern sample browser for beatmakers using CustomTkinter.
"""

import os
import json
import customtkinter as ctk
from tkinter import filedialog, messagebox
import pygame
import re
from pathlib import Path


# Set appearance and theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class SampleBrowser(ctk.CTk):
    # Supported audio formats
    AUDIO_EXTENSIONS = {'.wav', '.mp3', '.ogg', '.flac', '.aiff', '.aif'}

    # Config file for saving root folders
    CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'beatflow_config.json')

    def __init__(self):
        super().__init__()

        self.title("Beatflow")
        self.geometry("1400x800")
        self.minsize(1100, 650)

        # Custom colors
        self.colors = {
            'bg_dark': '#0a0a0a',
            'bg_main': '#111111',
            'bg_card': '#1a1a1a',
            'bg_hover': '#252525',
            'accent': '#ff6b35',
            'accent_hover': '#ff8555',
            'fg': '#ffffff',
            'fg_secondary': '#888888',
            'fg_dim': '#555555',
        }

        # Configure grid
        self.grid_columnconfigure(0, weight=0)  # Sidebar
        self.grid_columnconfigure(1, weight=0)  # Library index
        self.grid_columnconfigure(2, weight=1)  # Main content
        self.grid_rowconfigure(0, weight=1)

        # Initialize pygame mixer
        pygame.mixer.init()

        # State
        self.current_folder = None
        self.all_samples = []
        self.playing = False
        self.current_file = None
        self.current_playing_btn = None
        self.root_folders = []
        self.folder_buttons = {}
        self.sample_frames = []

        # Build UI
        self.build_sidebar()
        self.build_library_index()
        self.build_main_content()

        # Load config
        self.load_config()

        # Bind shortcuts
        self.bind('<space>', self.toggle_playback)
        self.bind('<Escape>', self.stop_playback)

    def build_sidebar(self):
        """Build the left sidebar with logo and navigation"""
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=self.colors['bg_dark'])
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)

        # Logo area
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(24, 0))

        # FLP badge
        flp_badge = ctk.CTkLabel(logo_frame, text=" FLP ", font=ctk.CTkFont(size=11, weight="bold"),
                                 fg_color=self.colors['accent'], corner_radius=4,
                                 text_color="#ffffff")
        flp_badge.pack(side="left")

        logo_text = ctk.CTkLabel(logo_frame, text="Beatflow", font=ctk.CTkFont(size=20, weight="bold"),
                                 text_color=self.colors['fg'])
        logo_text.pack(side="left", padx=(12, 0))

        # Navigation
        nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", pady=(32, 0))

        # Samples button (active)
        samples_btn = ctk.CTkButton(nav_frame, text="  ♪  Samples", font=ctk.CTkFont(size=14),
                                    fg_color=self.colors['accent'], hover_color=self.colors['accent_hover'],
                                    anchor="w", height=44, corner_radius=8)
        samples_btn.pack(fill="x", padx=12, pady=2)

        # Settings at bottom
        settings_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        settings_frame.pack(side="bottom", fill="x", pady=20)

        settings_btn = ctk.CTkButton(settings_frame, text="⚙  Settings", font=ctk.CTkFont(size=13),
                                     fg_color="transparent", hover_color=self.colors['bg_hover'],
                                     anchor="w", height=40, text_color=self.colors['fg_dim'])
        settings_btn.pack(fill="x", padx=12)

    def build_library_index(self):
        """Build the library index / folder list"""
        index_frame = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=self.colors['bg_dark'])
        index_frame.grid(row=0, column=1, sticky="nsw")
        index_frame.grid_propagate(False)

        # Header
        header = ctk.CTkFrame(index_frame, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(24, 16))

        title = ctk.CTkLabel(header, text="LIBRARY INDEX", font=ctk.CTkFont(size=11, weight="bold"),
                            text_color=self.colors['fg_dim'])
        title.pack(side="left")

        # Add folder button
        add_btn = ctk.CTkButton(header, text="+", width=32, height=32,
                               font=ctk.CTkFont(size=18, weight="bold"),
                               fg_color="transparent", hover_color=self.colors['accent'],
                               text_color=self.colors['fg_dim'],
                               command=self.browse_folder)
        add_btn.pack(side="right")

        # Scrollable folder list
        self.folder_scroll = ctk.CTkScrollableFrame(index_frame, fg_color="transparent",
                                                    scrollbar_button_color=self.colors['bg_hover'],
                                                    scrollbar_button_hover_color=self.colors['accent'])
        self.folder_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 16))

    def build_main_content(self):
        """Build the main content area"""
        content = ctk.CTkFrame(self, corner_radius=0, fg_color=self.colors['bg_main'])
        content.grid(row=0, column=2, sticky="nsew")

        # Top bar
        topbar = ctk.CTkFrame(content, fg_color="transparent", height=70)
        topbar.pack(fill="x", padx=24, pady=(20, 0))
        topbar.pack_propagate(False)

        # Breadcrumb
        self.breadcrumb = ctk.CTkLabel(topbar, text="📁 Library", font=ctk.CTkFont(size=14),
                                       text_color=self.colors['fg_secondary'])
        self.breadcrumb.pack(side="left", pady=16)

        # Search bar
        self.search_var = ctk.StringVar()
        self.search_var.trace('w', self.on_filter_change)
        search_entry = ctk.CTkEntry(topbar, textvariable=self.search_var,
                                   placeholder_text="Search samples...",
                                   width=350, height=40,
                                   font=ctk.CTkFont(size=13),
                                   fg_color=self.colors['bg_card'],
                                   border_width=0,
                                   corner_radius=20)
        search_entry.pack(side="left", padx=(32, 0), pady=12)

        # Scan folders button
        scan_btn = ctk.CTkButton(topbar, text="+ Scan Folders", font=ctk.CTkFont(size=13, weight="bold"),
                                fg_color=self.colors['bg_hover'], hover_color=self.colors['accent'],
                                height=40, corner_radius=20,
                                command=self.browse_folder)
        scan_btn.pack(side="right", pady=12)

        # Sample count
        self.sample_count = ctk.CTkLabel(topbar, text="", font=ctk.CTkFont(size=13),
                                         text_color=self.colors['fg_dim'])
        self.sample_count.pack(side="right", padx=20, pady=16)

        # Scrollable sample list
        self.sample_scroll = ctk.CTkScrollableFrame(content, fg_color="transparent",
                                                    scrollbar_button_color=self.colors['bg_hover'],
                                                    scrollbar_button_hover_color=self.colors['accent'])
        self.sample_scroll.pack(fill="both", expand=True, padx=24, pady=(8, 24))

    def create_folder_button(self, folder_path, count=0):
        """Create a folder button in the library index"""
        folder_name = os.path.basename(folder_path)
        display_text = f"📁  {folder_name}"
        if count > 0:
            display_text += f"  ({count})"

        btn_frame = ctk.CTkFrame(self.folder_scroll, fg_color="transparent")
        btn_frame.pack(fill="x", pady=2)

        btn = ctk.CTkButton(btn_frame, text=display_text, font=ctk.CTkFont(size=13),
                           fg_color="transparent", hover_color=self.colors['bg_hover'],
                           anchor="w", height=40, corner_radius=8,
                           text_color=self.colors['fg_secondary'],
                           command=lambda p=folder_path: self.select_folder(p))
        btn.pack(side="left", fill="x", expand=True)

        # Remove button
        remove_btn = ctk.CTkButton(btn_frame, text="×", width=30, height=30,
                                   font=ctk.CTkFont(size=14),
                                   fg_color="transparent", hover_color="#ff4444",
                                   text_color=self.colors['fg_dim'],
                                   command=lambda p=folder_path, f=btn_frame: self.remove_folder(p, f))
        remove_btn.pack(side="right", padx=(4, 0))

        self.folder_buttons[folder_path] = btn_frame
        return btn_frame

    def create_sample_card(self, sample):
        """Create a modern sample card"""
        # Card frame
        card = ctk.CTkFrame(self.sample_scroll, fg_color=self.colors['bg_card'],
                           corner_radius=12, height=80)
        card.pack(fill="x", pady=6)
        card.pack_propagate(False)

        # Play button
        play_btn = ctk.CTkButton(card, text="▶", width=50, height=50,
                                font=ctk.CTkFont(size=18),
                                fg_color=self.colors['bg_hover'],
                                hover_color=self.colors['accent'],
                                corner_radius=25,
                                command=lambda s=sample: self.play_sample(s, play_btn))
        play_btn.pack(side="left", padx=(16, 12), pady=15)

        # Info section
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, pady=12)

        # Top row: name + format badge
        top_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        top_row.pack(fill="x")

        name_label = ctk.CTkLabel(top_row, text=sample['name'],
                                  font=ctk.CTkFont(size=14, weight="bold"),
                                  text_color=self.colors['fg'])
        name_label.pack(side="left")

        # Format badge
        ext = os.path.splitext(sample['filename'])[1].upper()[1:]
        format_badge = ctk.CTkLabel(top_row, text=f" {ext} ",
                                    font=ctk.CTkFont(size=10),
                                    fg_color=self.colors['bg_hover'],
                                    corner_radius=4,
                                    text_color=self.colors['fg_dim'])
        format_badge.pack(side="left", padx=(10, 0))

        # Bottom row: metadata
        bottom_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        bottom_row.pack(fill="x", pady=(6, 0))

        # BPM
        if sample['bpm']:
            bpm_label = ctk.CTkLabel(bottom_row, text=f"♪ {sample['bpm']} BPM",
                                     font=ctk.CTkFont(size=12),
                                     text_color=self.colors['fg_secondary'])
            bpm_label.pack(side="left", padx=(0, 16))

        # Key
        if sample['key']:
            key_label = ctk.CTkLabel(bottom_row, text=f"◆ {sample['key']}",
                                     font=ctk.CTkFont(size=12, weight="bold"),
                                     text_color=self.colors['accent'])
            key_label.pack(side="left", padx=(0, 16))

        # Tags
        tags = self.extract_tags(sample['name'])
        for tag in tags[:3]:
            tag_label = ctk.CTkLabel(bottom_row, text=f"#{tag}",
                                     font=ctk.CTkFont(size=11),
                                     text_color=self.colors['fg_dim'])
            tag_label.pack(side="left", padx=(0, 8))

        # Waveform placeholder
        waveform = ctk.CTkLabel(card, text="▁▂▃▅▇▅▃▂▁▂▄▆▇▆▄▂",
                               font=ctk.CTkFont(family="Consolas", size=10),
                               text_color=self.colors['fg_dim'])
        waveform.pack(side="right", padx=20)

        # Store reference to play button
        sample['play_btn'] = play_btn

        self.sample_frames.append(card)
        return card

    def extract_tags(self, name):
        """Extract tags from sample name"""
        tags = []
        keywords = ['808', 'kick', 'snare', 'hihat', 'hat', 'clap', 'perc',
                   'loop', 'bass', 'pad', 'lead', 'synth', 'piano', 'guitar',
                   'trap', 'drill', 'lofi', 'ambient', 'hard', 'soft', 'dark']
        name_lower = name.lower()
        for kw in keywords:
            if kw in name_lower:
                tags.append(kw.capitalize())
        return tags

    def browse_folder(self):
        """Open folder browser"""
        folder = filedialog.askdirectory(title="Select Sample Folder")
        if folder:
            folder = os.path.normpath(folder)
            if folder in self.root_folders:
                messagebox.showinfo("Info", "This folder is already added.")
                return

            count = self.count_audio_files(folder)
            self.create_folder_button(folder, count)
            self.root_folders.append(folder)
            self.save_config()

            # Auto-select the new folder
            self.select_folder(folder)

    def select_folder(self, folder_path):
        """Select a folder and load its samples"""
        self.current_folder = folder_path
        self.breadcrumb.configure(text=f"📁 Library  ›  {os.path.basename(folder_path)}")
        self.load_samples(folder_path)

    def remove_folder(self, folder_path, frame):
        """Remove a folder from the library"""
        if folder_path in self.root_folders:
            self.root_folders.remove(folder_path)
        if folder_path in self.folder_buttons:
            del self.folder_buttons[folder_path]
        frame.destroy()
        self.save_config()

    def count_audio_files(self, folder_path):
        """Count audio files in folder"""
        count = 0
        try:
            for root, dirs, files in os.walk(folder_path):
                for item in files:
                    ext = os.path.splitext(item)[1].lower()
                    if ext in self.AUDIO_EXTENSIONS:
                        count += 1
        except Exception:
            pass
        return count

    def load_samples(self, folder_path):
        """Load samples from folder"""
        self.all_samples = []

        # Clear existing
        for frame in self.sample_frames:
            frame.destroy()
        self.sample_frames = []

        # Scan for audio files
        try:
            for root, dirs, files in os.walk(folder_path):
                # Sort files to ensure consistent order within folder
                files.sort()
                for item in files:
                    ext = os.path.splitext(item)[1].lower()
                    if ext in self.AUDIO_EXTENSIONS:
                        file_path = os.path.join(root, item)
                        sample_info = self.parse_sample_info(item, file_path)
                        self.all_samples.append(sample_info)
        except Exception:
            pass

        self.display_samples(self.all_samples)

    def parse_sample_info(self, filename, filepath):
        """Parse sample info"""
        name = os.path.splitext(filename)[0]

        # Extract BPM
        bpm = ""
        for pattern in [r'(\d{2,3})\s*bpm', r'bpm\s*(\d{2,3})', r'_(\d{2,3})_']:
            match = re.search(pattern, filename.lower())
            if match:
                bpm = match.group(1)
                break

        # Extract key
        key = ""
        match = re.search(r'\b([A-G][#b]?(?:maj|min|m)?)\b', filename, re.IGNORECASE)
        if match:
            key = match.group(1)

        return {
            'name': name,
            'bpm': bpm,
            'key': key,
            'path': filepath,
            'filename': filename
        }

    def display_samples(self, samples):
        """Display samples"""
        # Clear existing
        for frame in self.sample_frames:
            frame.destroy()
        self.sample_frames = []

        # Create sample cards
        for sample in samples:
            self.create_sample_card(sample)

        # Update count
        self.sample_count.configure(text=f"{len(samples)} samples")

    def play_sample(self, sample, play_btn):
        """Play a sample"""
        # Reset previous button
        if self.current_playing_btn and self.current_playing_btn != play_btn:
            self.current_playing_btn.configure(text="▶", fg_color=self.colors['bg_hover'])

        if self.current_file == sample['path'] and self.playing:
            # Pause
            pygame.mixer.music.pause()
            self.playing = False
            play_btn.configure(text="▶", fg_color=self.colors['bg_hover'])
        else:
            # Play
            try:
                pygame.mixer.music.load(sample['path'])
                pygame.mixer.music.play()
                self.playing = True
                self.current_file = sample['path']
                self.current_playing_btn = play_btn
                play_btn.configure(text="⏸", fg_color=self.colors['accent'])
            except Exception as e:
                print(f"Error playing: {e}")

    def toggle_playback(self, event=None):
        """Toggle play/pause"""
        if self.playing:
            pygame.mixer.music.pause()
            self.playing = False
            if self.current_playing_btn:
                self.current_playing_btn.configure(text="▶", fg_color=self.colors['bg_hover'])
        elif self.current_file:
            pygame.mixer.music.unpause()
            self.playing = True
            if self.current_playing_btn:
                self.current_playing_btn.configure(text="⏸", fg_color=self.colors['accent'])

    def stop_playback(self, event=None):
        """Stop playback"""
        pygame.mixer.music.stop()
        self.playing = False
        self.current_file = None
        if self.current_playing_btn:
            self.current_playing_btn.configure(text="▶", fg_color=self.colors['bg_hover'])
            self.current_playing_btn = None

    def on_filter_change(self, *args):
        """Handle filter change"""
        filter_text = self.search_var.get().lower().strip()

        if not filter_text:
            self.display_samples(self.all_samples)
            return

        filtered = [s for s in self.all_samples
                   if filter_text in s['name'].lower()
                   or filter_text in s.get('bpm', '').lower()
                   or filter_text in s.get('key', '').lower()]

        self.display_samples(filtered)

    def load_config(self):
        """Load config"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    for folder in config.get('root_folders', []):
                        if os.path.isdir(folder):
                            count = self.count_audio_files(folder)
                            self.create_folder_button(folder, count)
                            self.root_folders.append(folder)
            except (json.JSONDecodeError, IOError):
                pass

    def save_config(self):
        """Save config"""
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump({'root_folders': self.root_folders}, f, indent=2)
        except IOError:
            pass


def main():
    app = SampleBrowser()
    app.mainloop()


if __name__ == "__main__":
    main()
