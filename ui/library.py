"""Sample list component for Beatflow."""

import os
import subprocess
import threading
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import pygame
from ui.theme import COLORS
from core.scanner import LibraryScanner
from core.waveform import generate_waveform_image


class SampleRow(ctk.CTkFrame):
    """A single sample row with play button, metadata, and waveform."""

    WAVEFORM_WIDTH = 180
    WAVEFORM_HEIGHT = 35

    def __init__(self, parent, sample, on_play, on_edit=None, **kwargs):
        super().__init__(parent, fg_color="transparent", height=70, **kwargs)
        self.pack_propagate(False)

        self.sample = sample
        self.on_play = on_play
        self.on_edit = on_edit  # Callback for edit metadata
        self.is_playing = False
        self.waveform_image = None  # Keep reference to prevent garbage collection

        self._build_ui()
        self._load_waveform_async()
        self._bind_context_menu()

    def _build_ui(self):
        """Build the sample row UI."""
        # Play button (circular)
        self.play_btn = ctk.CTkButton(
            self,
            text="\u25b6",
            width=44,
            height=44,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['accent'],
            corner_radius=22,
            command=self._handle_play
        )
        self.play_btn.pack(side="left", padx=(16, 12), pady=13)

        # Info container
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, pady=10)

        # Top row: Title/filename + format badge + duration
        top_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        top_row.pack(fill="x", anchor="w")

        # Title (use metadata title if available, otherwise filename)
        display_name = self.sample.get('title') or self.sample['filename']
        name_label = ctk.CTkLabel(
            top_row,
            text=display_name,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['accent']
        )
        name_label.pack(side="left")

        # Format badge
        ext = os.path.splitext(self.sample['filename'])[1].upper()[1:]
        format_badge = ctk.CTkLabel(
            top_row,
            text=f" {ext} ",
            font=ctk.CTkFont(size=10),
            fg_color=COLORS['bg_hover'],
            corner_radius=4,
            text_color=COLORS['fg_dim']
        )
        format_badge.pack(side="left", padx=(10, 0))

        # Bitrate badge (if available)
        if self.sample.get('bitrate') and self.sample['bitrate'] > 0:
            bitrate_badge = ctk.CTkLabel(
                top_row,
                text=f" {self.sample['bitrate']}k ",
                font=ctk.CTkFont(size=10),
                fg_color=COLORS['bg_hover'],
                corner_radius=4,
                text_color=COLORS['fg_dim']
            )
            bitrate_badge.pack(side="left", padx=(6, 0))

        # Duration (if available)
        if self.sample.get('duration') and self.sample['duration'] > 0:
            duration_str = self._format_duration(self.sample['duration'])
            duration_label = ctk.CTkLabel(
                top_row,
                text=duration_str,
                font=ctk.CTkFont(size=11),
                text_color=COLORS['fg_dim']
            )
            duration_label.pack(side="left", padx=(10, 0))

        # Bottom row: Artist/Album | BPM | Key | Tags
        bottom_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        bottom_row.pack(fill="x", anchor="w", pady=(4, 0))

        # Artist - Album (if available)
        artist = self.sample.get('artist', '')
        album = self.sample.get('album', '')
        if artist or album:
            artist_album = artist
            if artist and album:
                artist_album = f"{artist} - {album}"
            elif album:
                artist_album = album

            artist_label = ctk.CTkLabel(
                bottom_row,
                text=artist_album,
                font=ctk.CTkFont(size=11),
                text_color=COLORS['fg_secondary']
            )
            artist_label.pack(side="left", padx=(0, 12))

        # BPM
        if self.sample.get('bpm'):
            bpm_label = ctk.CTkLabel(
                bottom_row,
                text=f"\u266a {self.sample['bpm']}",
                font=ctk.CTkFont(size=12),
                text_color=COLORS['fg_secondary']
            )
            bpm_label.pack(side="left")

            bpm_unit = ctk.CTkLabel(
                bottom_row,
                text=" BPM",
                font=ctk.CTkFont(size=12),
                text_color=COLORS['fg_dim']
            )
            bpm_unit.pack(side="left", padx=(0, 12))

        # Key
        if self.sample.get('key'):
            key_icon = ctk.CTkLabel(
                bottom_row,
                text="\u25c7",
                font=ctk.CTkFont(size=10),
                text_color=COLORS['accent']
            )
            key_icon.pack(side="left")

            key_label = ctk.CTkLabel(
                bottom_row,
                text=f" {self.sample['key']}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS['accent']
            )
            key_label.pack(side="left", padx=(0, 12))

        # Genre (if available)
        if self.sample.get('genre'):
            genre_label = ctk.CTkLabel(
                bottom_row,
                text=f"#{self.sample['genre']}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS['fg_dim']
            )
            genre_label.pack(side="left", padx=(0, 6))

        # Tags (from filename)
        tags = LibraryScanner.extract_tags(self.sample['name'])
        for tag in tags[:2]:  # Limit to 2 tags to save space
            tag_label = ctk.CTkLabel(
                bottom_row,
                text=f"#{tag}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS['fg_dim']
            )
            tag_label.pack(side="left", padx=(0, 6))

        # Waveform container (right side) - placeholder initially
        self.waveform_label = ctk.CTkLabel(
            self,
            text="\u2581\u2582\u2583\u2585\u2587\u2585\u2583\u2582\u2581\u2582\u2584\u2586\u2587\u2586\u2584\u2582",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=COLORS['fg_muted'],
            width=self.WAVEFORM_WIDTH,
            height=self.WAVEFORM_HEIGHT
        )
        self.waveform_label.pack(side="right", padx=20)

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in seconds to M:SS format."""
        if seconds <= 0:
            return ""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"

    def _load_waveform_async(self):
        """Load waveform image in background thread."""
        def load():
            try:
                img = generate_waveform_image(
                    self.sample['path'],
                    width=self.WAVEFORM_WIDTH,
                    height=self.WAVEFORM_HEIGHT,
                    color=COLORS['fg_muted']
                )
                if img:
                    # Schedule UI update on main thread
                    self.after(0, lambda: self._set_waveform_image(img))
            except Exception as e:
                print(f"Waveform error: {e}")

        thread = threading.Thread(target=load, daemon=True)
        thread.start()

    def _set_waveform_image(self, pil_image):
        """Set the waveform image (called on main thread)."""
        try:
            # Convert PIL image to CTkImage
            self.waveform_image = ctk.CTkImage(
                light_image=pil_image,
                dark_image=pil_image,
                size=(self.WAVEFORM_WIDTH, self.WAVEFORM_HEIGHT)
            )
            self.waveform_label.configure(image=self.waveform_image, text="")
        except Exception as e:
            print(f"Error setting waveform: {e}")

    def _handle_play(self):
        """Handle play button click."""
        self.on_play(self)

    def set_playing(self, is_playing):
        """Update visual state for playing/paused."""
        self.is_playing = is_playing
        if is_playing:
            self.play_btn.configure(text="\u23f8", fg_color=COLORS['accent'])
        else:
            self.play_btn.configure(text="\u25b6", fg_color=COLORS['bg_hover'])

    def _bind_context_menu(self):
        """Bind right-click context menu to the row."""
        self.bind("<Button-3>", self._show_context_menu)
        # Bind to all children as well
        for child in self.winfo_children():
            child.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        """Show the right-click context menu."""
        menu = tk.Menu(self, tearoff=0, bg=COLORS['bg_card'], fg=COLORS['fg'],
                       activebackground=COLORS['accent'], activeforeground='white',
                       font=('Segoe UI', 10))

        menu.add_command(label="Edit Metadata", command=self._on_edit_metadata)
        menu.add_separator()
        menu.add_command(label="Open File Location", command=self._on_open_location)
        menu.add_command(label="Copy Path", command=self._on_copy_path)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _on_edit_metadata(self):
        """Handle Edit Metadata menu click."""
        if self.on_edit:
            self.on_edit(self)

    def _on_open_location(self):
        """Open the file's folder in file explorer."""
        folder = os.path.dirname(self.sample['path'])
        if os.path.exists(folder):
            # Windows
            subprocess.run(['explorer', '/select,', self.sample['path']])

    def _on_copy_path(self):
        """Copy the file path to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.sample['path'])

    def update_sample(self, new_sample):
        """Update the sample data and refresh display."""
        self.sample = new_sample


class SampleList(ctk.CTkFrame):
    """Main sample list view with header and scrollable list."""

    def __init__(self, master, on_play_request=None, on_edit_request=None, **kwargs):
        super().__init__(master, fg_color=COLORS['bg_main'], corner_radius=0, **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.on_play_request = on_play_request  # Callback: (sample, playlist, index)
        self.on_edit_request = on_edit_request  # Callback: (sample, row)
        self.sample_rows = []
        self.all_samples = []  # All samples in current folder
        self.filtered_samples = []  # Samples after search filter
        self.current_playing_row = None
        self.current_path = None
        self.search_query = ""

        self._build_ui()

    def _build_ui(self):
        """Build the sample list UI."""
        # Top bar
        topbar = ctk.CTkFrame(self, fg_color="transparent", height=60)
        topbar.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 0))
        topbar.grid_propagate(False)

        # Breadcrumb (left side)
        breadcrumb_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        breadcrumb_frame.pack(side="left", fill="y")

        self.breadcrumb = ctk.CTkLabel(
            breadcrumb_frame,
            text="\U0001f4c1 Library",
            font=ctk.CTkFont(size=13),
            text_color=COLORS['fg_secondary']
        )
        self.breadcrumb.pack(side="left", pady=18)

        # Action buttons (right side)
        actions_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        actions_frame.pack(side="right", fill="y")

        # Scan Folders button
        scan_btn = ctk.CTkButton(
            actions_frame,
            text="Scan Folders",
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['bg_card'],
            height=32,
            corner_radius=6,
            text_color=COLORS['fg']
        )
        scan_btn.pack(side="left", padx=(0, 8), pady=14)

        # Index AI button (outline style)
        index_btn = ctk.CTkButton(
            actions_frame,
            text="Index AI",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=COLORS['accent'],
            border_width=1,
            border_color=COLORS['accent'],
            height=32,
            corner_radius=6,
            text_color=COLORS['accent']
        )
        index_btn.pack(side="left", pady=14)

        # Sample count
        self.count_label = ctk.CTkLabel(
            actions_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_dim']
        )
        self.count_label.pack(side="right", padx=(20, 0), pady=18)

        # Scrollable sample list
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS['bg_hover'],
            scrollbar_button_hover_color=COLORS['accent']
        )
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(8, 16))

    def load_folder(self, folder_path):
        """Load samples from a folder and display them."""
        self.current_path = folder_path
        folder_name = os.path.basename(folder_path)
        self.breadcrumb.configure(text=f"\U0001f4c1 Library  \u203a  {folder_name}")

        # Scan folder and store samples
        self.all_samples = LibraryScanner.scan_folder(folder_path)
        self.search_query = ""

        # Apply filter and display
        self._refresh_display()

    def filter_samples(self, query: str):
        """Filter displayed samples by search query."""
        self.search_query = query.lower().strip()
        self._refresh_display()

    def _matches_search(self, sample: dict, query: str) -> bool:
        """Check if sample matches search query with fuzzy matching."""
        # Fields to search in
        searchable_fields = [
            sample.get('filename', ''),
            sample.get('name', ''),
            sample.get('title', ''),
            sample.get('artist', ''),
            sample.get('album', ''),
            sample.get('genre', ''),
            sample.get('bpm', ''),
            sample.get('key', ''),
        ]

        # Combine all fields into one searchable string
        combined = ' '.join(str(f).lower() for f in searchable_fields if f)

        # Split query into words for multi-word search
        query_words = query.split()

        # All query words must match somewhere (AND logic)
        for word in query_words:
            if word not in combined:
                # Try fuzzy match - check if word is similar to any word in combined
                if not self._fuzzy_word_match(word, combined):
                    return False
        return True

    def _fuzzy_word_match(self, query_word: str, text: str) -> bool:
        """Simple fuzzy matching - allows partial matches and minor typos."""
        # Direct substring match
        if query_word in text:
            return True

        # Check each word in text for partial match (at least 70% of query chars match)
        text_words = text.split()
        min_match_len = max(2, int(len(query_word) * 0.7))

        for text_word in text_words:
            # Partial match at start of word
            if text_word.startswith(query_word[:min_match_len]):
                return True
            # Partial match at start of query
            if query_word.startswith(text_word[:min(len(text_word), min_match_len)]):
                return True
            # Check for 1-character difference (simple Levenshtein approximation)
            if len(query_word) >= 3 and len(text_word) >= 3:
                if abs(len(query_word) - len(text_word)) <= 1:
                    matches = sum(1 for a, b in zip(query_word, text_word) if a == b)
                    if matches >= len(query_word) - 1:
                        return True

        return False

    def _refresh_display(self):
        """Refresh the sample list display based on current filter."""
        # Clear existing rows
        for row in self.sample_rows:
            row.destroy()
        self.sample_rows = []
        self.current_playing_row = None

        # Filter samples
        if self.search_query:
            self.filtered_samples = [
                s for s in self.all_samples
                if self._matches_search(s, self.search_query)
            ]
        else:
            self.filtered_samples = self.all_samples.copy()

        self.count_label.configure(text=f"{len(self.filtered_samples)} samples")

        # Create sample rows
        for sample in self.filtered_samples:
            row = SampleRow(self.scroll_frame, sample, self._on_play, self._on_edit)
            row.pack(fill="x", pady=2)
            self.sample_rows.append(row)

    def _on_play(self, row):
        """Handle play request from a sample row."""
        # Update visual state
        if self.current_playing_row and self.current_playing_row != row:
            self.current_playing_row.set_playing(False)

        row.set_playing(True)
        self.current_playing_row = row

        # Delegate to FooterPlayer via callback
        if self.on_play_request:
            # Find index in filtered samples
            try:
                index = self.filtered_samples.index(row.sample)
            except ValueError:
                index = 0
            self.on_play_request(row.sample, self.filtered_samples, index)

    def _on_edit(self, row):
        """Handle edit request from a sample row."""
        if self.on_edit_request:
            self.on_edit_request(row.sample, row)

    def _stop_playback(self):
        """Stop current playback visual state."""
        if self.current_playing_row:
            self.current_playing_row.set_playing(False)
            self.current_playing_row = None

    def set_playing_sample(self, sample_path: str):
        """Update visual state to show which sample is playing."""
        for row in self.sample_rows:
            if row.sample['path'] == sample_path:
                row.set_playing(True)
                self.current_playing_row = row
            else:
                row.set_playing(False)
