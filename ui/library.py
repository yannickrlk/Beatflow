"""Sample list component for Beatflow."""

import os
import subprocess
import threading
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import pygame
from ui.theme import COLORS, SPACING
from core.scanner import LibraryScanner
from core.waveform import generate_waveform_image
from core.database import get_database
from core.config import ConfigManager

# Audio analyzer (optional - may not be installed)
try:
    from core.analyzer import get_analyzer, AudioAnalyzer
    ANALYZER_AVAILABLE = AudioAnalyzer.is_available()
except ImportError:
    ANALYZER_AVAILABLE = False


class SampleRow(ctk.CTkFrame):
    """A single sample row with play button, metadata, and waveform."""

    WAVEFORM_WIDTH = 180
    WAVEFORM_HEIGHT = 32

    def __init__(self, parent, sample, on_play, on_edit=None, on_favorite=None,
                 on_add_to_collection=None, on_analyze=None, show_folder_path=False,
                 on_go_to_folder=None, on_seek=None, **kwargs):
        # Adjust height if showing folder path
        row_height = 88 if show_folder_path else 72  # Extra height for folder path

        super().__init__(
            parent,
            fg_color=COLORS['bg_card'],
            height=row_height,
            corner_radius=4,
            border_width=0,
            border_color=COLORS['border'],
            **kwargs
        )
        self.pack_propagate(False)

        self.sample = sample
        self.on_play = on_play
        self.on_edit = on_edit  # Callback for edit metadata
        self.on_favorite = on_favorite  # Callback for favorite toggle
        self.on_add_to_collection = on_add_to_collection  # Callback for add to collection
        self.on_analyze = on_analyze  # Callback for analyze sample
        self.show_folder_path = show_folder_path  # Show folder context in global search
        self.on_go_to_folder = on_go_to_folder  # Callback for "Go to Folder" action
        self.on_seek = on_seek  # Callback for waveform click-to-seek
        self.is_playing = False
        self.is_favorite = sample.get('is_favorite', False) or get_database().is_favorite(sample['path'])
        self.is_analyzing = False  # Track if analysis is in progress
        self.waveform_image = None  # CTkImage reference to prevent garbage collection
        self.waveform_gray = None   # PIL Image: gray waveform (unplayed)
        self.waveform_accent = None # PIL Image: accent waveform (played)

        self._build_ui()
        self._load_waveform_async()
        self._bind_context_menu()

    def _build_ui(self):
        """Build the sample row UI."""
        # Play button (circular) - 8px grid spacing
        self.play_btn = ctk.CTkButton(
            self,
            text="\u25b6",
            width=40,  # 8px grid: 40 = 5*8
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['accent'],
            corner_radius=20,
            command=self._handle_play
        )
        self.play_btn.pack(side="left", padx=(SPACING['md'], SPACING['sm']), pady=SPACING['md'])

        # Info container
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, pady=SPACING['sm'])

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

        # Folder path row (only in global search mode)
        if self.show_folder_path:
            folder_path = os.path.dirname(self.sample['path'])
            # Get relative folder name (last 2 parts of path)
            path_parts = folder_path.replace('\\', '/').split('/')
            display_path = '/'.join(path_parts[-2:]) if len(path_parts) >= 2 else folder_path

            folder_row = ctk.CTkFrame(info_frame, fg_color="transparent")
            folder_row.pack(fill="x", anchor="w", pady=(2, 0))

            folder_label = ctk.CTkLabel(
                folder_row,
                text=f"\U0001f4c1 {display_path}",
                font=ctk.CTkFont(size=10),
                text_color=COLORS['fg_dim']
            )
            folder_label.pack(side="left")

        # Bottom row: Artist/Album | BPM | Key | Tags
        self.bottom_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        self.bottom_row.pack(fill="x", anchor="w", pady=(4, 0))

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
                self.bottom_row,
                text=artist_album,
                font=ctk.CTkFont(size=11),
                text_color=COLORS['fg_secondary']
            )
            artist_label.pack(side="left", padx=(0, 12))

        # BPM - show embedded or detected (with indicator)
        bpm_value = self.sample.get('bpm') or self.sample.get('detected_bpm', '')
        is_bpm_detected = not self.sample.get('bpm') and self.sample.get('detected_bpm')
        self.bpm_label = None
        self.bpm_unit_label = None
        if bpm_value:
            self._create_bpm_label(bpm_value, is_bpm_detected)

        # Key - show embedded or detected (with indicator)
        key_value = self.sample.get('key') or self.sample.get('detected_key', '')
        is_key_detected = not self.sample.get('key') and self.sample.get('detected_key')
        self.key_icon_label = None
        self.key_label = None
        if key_value:
            self._create_key_label(key_value, is_key_detected)

        # Genre (if available)
        if self.sample.get('genre'):
            genre_label = ctk.CTkLabel(
                self.bottom_row,
                text=f"#{self.sample['genre']}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS['fg_dim']
            )
            genre_label.pack(side="left", padx=(0, 6))

        # Tags (from filename)
        tags = LibraryScanner.extract_tags(self.sample['name'])
        for tag in tags[:2]:  # Limit to 2 tags to save space
            tag_label = ctk.CTkLabel(
                self.bottom_row,
                text=f"#{tag}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS['fg_dim']
            )
            tag_label.pack(side="left", padx=(0, 6))

        # Waveform container (right side) - skeleton loading state
        self.waveform_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS['bg_hover'],
            width=self.WAVEFORM_WIDTH,
            height=self.WAVEFORM_HEIGHT,
            corner_radius=2
        )
        self.waveform_frame.pack(side="right", padx=SPACING['md'])
        self.waveform_frame.pack_propagate(False)

        self.waveform_label = ctk.CTkLabel(
            self.waveform_frame,
            text="",
            width=self.WAVEFORM_WIDTH,
            height=self.WAVEFORM_HEIGHT
        )
        self.waveform_label.pack(fill="both", expand=True)

        # Bind click event to waveform for seeking
        self.waveform_label.bind("<Button-1>", self._on_waveform_click)
        self.waveform_frame.bind("<Button-1>", self._on_waveform_click)

        # Star/Favorite button
        self.star_btn = ctk.CTkButton(
            self,
            text="\u2605" if self.is_favorite else "\u2606",  # Filled or empty star
            width=32,
            height=32,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            text_color=COLORS['accent'] if self.is_favorite else COLORS['fg_dim'],
            corner_radius=16,
            command=self._toggle_favorite
        )
        self.star_btn.pack(side="right", padx=(0, 8))

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in seconds to M:SS format."""
        if seconds <= 0:
            return ""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"

    def _load_waveform_async(self):
        """Load waveform images in background thread (gray + accent for SoundCloud-style progress)."""
        def load():
            try:
                # Generate gray waveform (unplayed portion)
                gray_img = generate_waveform_image(
                    self.sample['path'],
                    width=self.WAVEFORM_WIDTH,
                    height=self.WAVEFORM_HEIGHT,
                    color=COLORS['fg_muted']
                )
                # Generate accent waveform (played portion)
                accent_img = generate_waveform_image(
                    self.sample['path'],
                    width=self.WAVEFORM_WIDTH,
                    height=self.WAVEFORM_HEIGHT,
                    color=COLORS['accent']
                )
                if gray_img and accent_img:
                    # Schedule UI update on main thread
                    self.after(0, lambda: self._set_waveform_images(gray_img, accent_img))
            except Exception as e:
                print(f"Waveform error: {e}")

        thread = threading.Thread(target=load, daemon=True)
        thread.start()

    def _set_waveform_images(self, gray_img, accent_img):
        """Set both waveform images and display the gray one initially."""
        try:
            if not self.winfo_exists():
                return

            # Store both PIL images for progress compositing
            self.waveform_gray = gray_img.copy()
            self.waveform_accent = accent_img.copy()

            # Initially display the gray waveform
            self.waveform_image = ctk.CTkImage(
                light_image=self.waveform_gray,
                dark_image=self.waveform_gray,
                size=(self.WAVEFORM_WIDTH, self.WAVEFORM_HEIGHT)
            )
            self.waveform_label.configure(image=self.waveform_image, text="")
        except Exception:
            pass

    def _update_waveform_progress(self, percentage: float):
        """Composite gray and accent waveforms based on progress (SoundCloud-style)."""
        if not self.waveform_gray or not self.waveform_accent:
            return

        try:
            if not self.winfo_exists():
                return

            # Calculate split point
            split_x = int(percentage * self.WAVEFORM_WIDTH)

            # Create composite image
            composite = self.waveform_gray.copy()

            if split_x > 0:
                # Paste the accent (played) portion on the left
                accent_crop = self.waveform_accent.crop((0, 0, split_x, self.WAVEFORM_HEIGHT))
                composite.paste(accent_crop, (0, 0))

            # Update the display
            self.waveform_image = ctk.CTkImage(
                light_image=composite,
                dark_image=composite,
                size=(self.WAVEFORM_WIDTH, self.WAVEFORM_HEIGHT)
            )
            self.waveform_label.configure(image=self.waveform_image)
        except Exception:
            pass

    def _handle_play(self):
        """Handle play button click - toggle play/pause if already playing."""
        self.on_play(self, toggle=self.is_playing)

    def set_playing(self, is_playing):
        """Update visual state for playing/paused."""
        self.is_playing = is_playing
        if is_playing:
            # Playing state: highlight background and add accent border
            self.configure(fg_color=COLORS['bg_playing'], border_width=1, border_color=COLORS['accent'])
            self.play_btn.configure(text="\u23f8", fg_color=COLORS['accent'])
            # Reset waveform progress to start
            self.set_progress(0)
        else:
            # Normal state: card background, no border
            self.configure(fg_color=COLORS['bg_card'], border_width=0)
            self.play_btn.configure(text="\u25b6", fg_color=COLORS['bg_hover'])
            # Reset waveform to gray (no progress)
            self._update_waveform_progress(0)

    def set_progress(self, percentage: float):
        """Update the waveform progress display (SoundCloud-style).

        Args:
            percentage: Progress as 0.0-1.0
        """
        if not self.is_playing:
            return

        # Clamp percentage
        percentage = max(0.0, min(1.0, percentage))

        # Update waveform composite
        self._update_waveform_progress(percentage)

    def _on_waveform_click(self, event):
        """Handle click on waveform for seeking."""
        if not self.on_seek:
            return

        # Calculate percentage from click position
        widget_width = event.widget.winfo_width()
        if widget_width <= 0:
            widget_width = self.WAVEFORM_WIDTH

        percentage = event.x / widget_width
        percentage = max(0.0, min(1.0, percentage))

        # Call seek callback with this sample and percentage
        self.on_seek(self, percentage)

    def _toggle_favorite(self):
        """Toggle favorite status."""
        db = get_database()
        self.is_favorite = db.toggle_favorite(self.sample['path'])

        # Update UI
        if self.is_favorite:
            self.star_btn.configure(text="\u2605", text_color=COLORS['accent'])
        else:
            self.star_btn.configure(text="\u2606", text_color=COLORS['fg_dim'])

        # Notify callback
        if self.on_favorite:
            self.on_favorite(self.sample, self.is_favorite)

    def set_favorite(self, is_favorite: bool):
        """Set the favorite state visually."""
        self.is_favorite = is_favorite
        if self.is_favorite:
            self.star_btn.configure(text="\u2605", text_color=COLORS['accent'])
        else:
            self.star_btn.configure(text="\u2606", text_color=COLORS['fg_dim'])

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

        # Favorite toggle
        fav_label = "Remove from Favorites" if self.is_favorite else "Add to Favorites"
        menu.add_command(label=fav_label, command=self._toggle_favorite)
        menu.add_command(label="Add to Collection...", command=self._on_add_to_collection)
        menu.add_separator()

        # Analyze option (only if librosa is available)
        if ANALYZER_AVAILABLE:
            if self.is_analyzing:
                menu.add_command(label="Analyzing...", state="disabled")
            else:
                menu.add_command(label="Analyze BPM/Key", command=self._on_analyze)

        menu.add_command(label="Edit Metadata", command=self._on_edit_metadata)
        menu.add_separator()

        # "Go to Folder" option (useful in global search)
        if self.on_go_to_folder:
            menu.add_command(label="Go to Folder", command=self._on_go_to_folder)

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

    def _on_go_to_folder(self):
        """Navigate to the folder containing this sample."""
        if self.on_go_to_folder:
            folder_path = os.path.dirname(self.sample['path'])
            self.on_go_to_folder(folder_path)

    def _on_add_to_collection(self):
        """Handle Add to Collection menu click."""
        if self.on_add_to_collection:
            self.on_add_to_collection(self)

    def _on_analyze(self):
        """Handle Analyze BPM/Key menu click."""
        if self.on_analyze:
            self.is_analyzing = True
            self.on_analyze(self)

    def set_analyzing(self, is_analyzing: bool):
        """Set the analyzing state."""
        self.is_analyzing = is_analyzing

    def _create_bpm_label(self, bpm_value: str, is_detected: bool):
        """Create BPM label in bottom row."""
        bpm_icon = "\u2248" if is_detected else "\u266a"  # ≈ for detected, ♪ for embedded
        bpm_color = COLORS['accent_secondary'] if is_detected else COLORS['fg_secondary']

        self.bpm_label = ctk.CTkLabel(
            self.bottom_row,
            text=f"{bpm_icon} {bpm_value}",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=bpm_color
        )
        self.bpm_label.pack(side="left")

        self.bpm_unit_label = ctk.CTkLabel(
            self.bottom_row,
            text=" BPM",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_dim']
        )
        self.bpm_unit_label.pack(side="left", padx=(0, SPACING['sm']))

    def _create_key_label(self, key_value: str, is_detected: bool):
        """Create Key label in bottom row."""
        key_icon_char = "\u2248" if is_detected else "\u25c7"  # ≈ for detected, ◇ for embedded
        key_color = COLORS['accent_secondary'] if is_detected else COLORS['accent']

        self.key_icon_label = ctk.CTkLabel(
            self.bottom_row,
            text=key_icon_char,
            font=ctk.CTkFont(size=10),
            text_color=key_color
        )
        self.key_icon_label.pack(side="left")

        self.key_label = ctk.CTkLabel(
            self.bottom_row,
            text=f" {key_value}",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=key_color
        )
        self.key_label.pack(side="left", padx=(0, SPACING['sm']))

    def update_analysis_result(self, detected_bpm: str, detected_key: str):
        """Update the display with analysis results."""
        self.is_analyzing = False
        # Update sample data
        self.sample['detected_bpm'] = detected_bpm
        self.sample['detected_key'] = detected_key

        # Update or create BPM label
        if detected_bpm:
            if self.bpm_label:
                self.bpm_label.configure(text=f"\u2248 {detected_bpm}", text_color=COLORS['accent_secondary'])
            else:
                self._create_bpm_label(detected_bpm, is_detected=True)

        # Update or create Key label
        if detected_key:
            if self.key_label:
                self.key_label.configure(text=f" {detected_key}", text_color=COLORS['accent_secondary'])
                if self.key_icon_label:
                    self.key_icon_label.configure(text="\u2248", text_color=COLORS['accent_secondary'])
            else:
                self._create_key_label(detected_key, is_detected=True)

    def update_sample(self, new_sample):
        """Update the sample data and refresh display."""
        self.sample = new_sample


class SampleList(ctk.CTkFrame):
    """Main sample list view with header and scrollable list."""

    # Sort option mapping: display name -> (sort_by, sort_order)
    SORT_OPTIONS = {
        "Name (A-Z)": ("name", "asc"),
        "Name (Z-A)": ("name", "desc"),
        "BPM (Low-High)": ("bpm", "asc"),
        "BPM (High-Low)": ("bpm", "desc"),
        "Key": ("key", "asc"),
        "Duration": ("duration", "asc"),
    }

    # Musical keys for filter dropdown (12 major + 12 minor)
    MUSICAL_KEYS = [
        "All Keys",
        "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B",
        "Cm", "C#m", "Dm", "D#m", "Em", "Fm", "F#m", "Gm", "G#m", "Am", "A#m", "Bm"
    ]

    # Audio formats for filter
    AUDIO_FORMATS = ["WAV", "MP3", "FLAC", "OGG", "AIFF"]

    def __init__(self, master, on_play_request=None, on_edit_request=None,
                 on_favorite_change=None, on_add_to_collection=None,
                 on_analysis_complete=None, on_add_folder=None,
                 on_seek_request=None, config_manager=None, **kwargs):
        super().__init__(master, fg_color=COLORS['bg_main'], corner_radius=0, **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Topbar
        self.grid_rowconfigure(1, weight=0)  # Filter panel (collapsible)
        self.grid_rowconfigure(2, weight=1)  # Sample list

        self.on_play_request = on_play_request  # Callback: (sample, playlist, index)
        self.on_seek_request = on_seek_request  # Callback: (sample, percentage)
        self.on_edit_request = on_edit_request  # Callback: (sample, row)
        self.on_favorite_change = on_favorite_change  # Callback: (sample, is_favorite)
        self.on_add_to_collection = on_add_to_collection  # Callback: (sample)
        self.on_analysis_complete = on_analysis_complete  # Callback: (sample, result)
        self.on_add_folder = on_add_folder  # Callback for empty state Add Folder button
        self.config_manager = config_manager  # For persisting sort preferences
        self.sample_rows = []
        self.all_samples = []  # All samples in current folder
        self.filtered_samples = []  # Samples after search filter
        self.current_playing_row = None
        self.current_path = None
        self.search_query = ""
        self.is_favorites_view = False  # Track if showing favorites
        self.is_collection_view = False  # Track if showing a collection
        self.is_global_search = False  # Track if showing global search results
        self.current_collection_id = None  # Current collection ID
        self.last_folder_path = None  # Store last folder for returning from global search

        # Filter state
        self.filters_visible = False
        self.filter_bpm_min = None  # Min BPM filter (None = no filter)
        self.filter_bpm_max = None  # Max BPM filter
        self.filter_key = None  # Key filter (None = all keys)
        self.filter_formats = set(self.AUDIO_FORMATS)  # Active format filters (all by default)

        self._build_ui()
        self._show_empty_state()  # Show empty state initially

    def _build_ui(self):
        """Build the sample list UI."""
        # Top bar - use grid layout for proper responsive behavior
        topbar = ctk.CTkFrame(self, fg_color="transparent", height=50)
        topbar.grid(row=0, column=0, sticky="ew", padx=20, pady=(12, 0))
        topbar.grid_propagate(False)
        topbar.grid_columnconfigure(0, weight=1)  # Breadcrumb expands
        topbar.grid_columnconfigure(1, weight=0)  # Actions fixed
        topbar.grid_rowconfigure(0, weight=1)

        # Breadcrumb (left side)
        self.breadcrumb = ctk.CTkLabel(
            topbar,
            text="\U0001f4c1 Library",
            font=ctk.CTkFont(size=13),
            text_color=COLORS['fg_secondary'],
            anchor="w"
        )
        self.breadcrumb.grid(row=0, column=0, sticky="w", pady=12)

        # Action buttons (right side) - use horizontal frame
        actions_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        actions_frame.grid(row=0, column=1, sticky="e", pady=8)

        # Sample count (leftmost in actions)
        self.count_label = ctk.CTkLabel(
            actions_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_dim']
        )
        self.count_label.pack(side="left", padx=(0, 16))

        # Analyze All button (only shown if librosa available)
        if ANALYZER_AVAILABLE:
            self.analyze_btn = ctk.CTkButton(
                actions_frame,
                text="Analyze All",
                font=ctk.CTkFont(size=12),
                fg_color=COLORS['bg_hover'],
                hover_color='#8B5CF6',  # Purple for analysis
                height=32,
                corner_radius=6,
                text_color=COLORS['fg'],
                command=self._on_analyze_all
            )
            self.analyze_btn.pack(side="left", padx=(0, 8))

        # Sort dropdown
        self.sort_var = ctk.StringVar(value=self._get_current_sort_label())
        self.sort_dropdown = ctk.CTkOptionMenu(
            actions_frame,
            variable=self.sort_var,
            values=list(self.SORT_OPTIONS.keys()),
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['bg_hover'],
            button_color=COLORS['bg_hover'],
            button_hover_color=COLORS['accent'],
            dropdown_fg_color=COLORS['bg_card'],
            dropdown_hover_color=COLORS['accent'],
            height=32,
            width=130,
            corner_radius=6,
            command=self._on_sort_change
        )
        self.sort_dropdown.pack(side="left", padx=(0, 8))

        # Filter toggle button
        self.filter_btn = ctk.CTkButton(
            actions_frame,
            text="\u2630",  # Filter/hamburger icon
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['accent'],
            height=32,
            width=32,
            corner_radius=6,
            command=self._toggle_filters
        )
        self.filter_btn.pack(side="left")

        # Filter panel (collapsible)
        self.filter_panel = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], height=56, corner_radius=0)
        self.filter_panel.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        self.filter_panel.grid_remove()  # Hidden by default
        self.filter_panel.grid_propagate(False)

        # Filter panel content
        filter_content = ctk.CTkFrame(self.filter_panel, fg_color="transparent")
        filter_content.pack(fill="both", expand=True, padx=SPACING['lg'], pady=SPACING['sm'])

        # BPM Range Filter
        bpm_frame = ctk.CTkFrame(filter_content, fg_color="transparent")
        bpm_frame.pack(side="left", padx=(0, SPACING['lg']))

        bpm_label = ctk.CTkLabel(
            bpm_frame,
            text="BPM:",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_secondary']
        )
        bpm_label.pack(side="left", padx=(0, SPACING['xs']))

        self.bpm_min_var = ctk.StringVar()
        self.bpm_min_var.trace('w', self._on_filter_change)
        self.bpm_min_entry = ctk.CTkEntry(
            bpm_frame,
            textvariable=self.bpm_min_var,
            placeholder_text="Min",
            width=60,
            height=28,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=COLORS['bg_input'],
            border_width=1,
            border_color=COLORS['border'],
            corner_radius=4
        )
        self.bpm_min_entry.pack(side="left", padx=(0, 4))

        dash_label = ctk.CTkLabel(
            bpm_frame,
            text="-",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_dim']
        )
        dash_label.pack(side="left", padx=2)

        self.bpm_max_var = ctk.StringVar()
        self.bpm_max_var.trace('w', self._on_filter_change)
        self.bpm_max_entry = ctk.CTkEntry(
            bpm_frame,
            textvariable=self.bpm_max_var,
            placeholder_text="Max",
            width=60,
            height=28,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=COLORS['bg_input'],
            border_width=1,
            border_color=COLORS['border'],
            corner_radius=4
        )
        self.bpm_max_entry.pack(side="left")

        # Key Filter
        key_frame = ctk.CTkFrame(filter_content, fg_color="transparent")
        key_frame.pack(side="left", padx=(0, SPACING['lg']))

        key_label = ctk.CTkLabel(
            key_frame,
            text="Key:",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_secondary']
        )
        key_label.pack(side="left", padx=(0, SPACING['xs']))

        self.key_var = ctk.StringVar(value="All Keys")
        self.key_dropdown = ctk.CTkOptionMenu(
            key_frame,
            variable=self.key_var,
            values=self.MUSICAL_KEYS,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS['bg_hover'],
            button_color=COLORS['bg_hover'],
            button_hover_color=COLORS['accent'],
            dropdown_fg_color=COLORS['bg_card'],
            dropdown_hover_color=COLORS['accent'],
            height=28,
            width=90,
            corner_radius=4,
            command=self._on_key_filter_change
        )
        self.key_dropdown.pack(side="left")

        # Format Filter
        format_frame = ctk.CTkFrame(filter_content, fg_color="transparent")
        format_frame.pack(side="left", padx=(0, SPACING['lg']))

        format_label = ctk.CTkLabel(
            format_frame,
            text="Format:",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_secondary']
        )
        format_label.pack(side="left", padx=(0, SPACING['xs']))

        # Format checkboxes
        self.format_vars = {}
        for fmt in self.AUDIO_FORMATS:
            var = ctk.BooleanVar(value=True)
            var.trace('w', self._on_filter_change)
            self.format_vars[fmt] = var

            cb = ctk.CTkCheckBox(
                format_frame,
                text=fmt,
                variable=var,
                font=ctk.CTkFont(size=10),
                fg_color=COLORS['accent'],
                hover_color=COLORS['accent_hover'],
                border_color=COLORS['border'],
                checkmark_color="#ffffff",
                height=24,
                width=24,
                corner_radius=4
            )
            cb.pack(side="left", padx=(0, 8))

        # Clear filters button
        self.clear_filters_btn = ctk.CTkButton(
            filter_content,
            text="Clear",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            height=28,
            width=60,
            corner_radius=4,
            text_color=COLORS['fg_dim'],
            command=self._clear_filters
        )
        self.clear_filters_btn.pack(side="right")

        # Scrollable sample list
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS['bg_hover'],
            scrollbar_button_hover_color=COLORS['accent']
        )
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(16, 12))

        # Empty state (shown when no folder selected)
        self.empty_state_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.empty_state_frame.grid(row=2, column=0, sticky="nsew")

        # Center container for empty state content
        empty_center = ctk.CTkFrame(self.empty_state_frame, fg_color="transparent")
        empty_center.place(relx=0.5, rely=0.4, anchor="center")

        # Folder icon
        folder_icon = ctk.CTkLabel(
            empty_center,
            text="\U0001f4c1",
            font=ctk.CTkFont(size=48),
            text_color=COLORS['fg_dim']
        )
        folder_icon.pack(pady=(0, 16))

        # Message
        empty_label = ctk.CTkLabel(
            empty_center,
            text="Add your sample folders to get started",
            font=ctk.CTkFont(size=14),
            text_color=COLORS['fg_secondary']
        )
        empty_label.pack(pady=(0, 20))

        # Add Folder button
        self.empty_add_btn = ctk.CTkButton(
            empty_center,
            text="+ Add Folder",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            height=44,
            width=160,
            corner_radius=8,
            text_color="#ffffff",
            command=self._on_empty_add_folder
        )
        self.empty_add_btn.pack()

    def _on_empty_add_folder(self):
        """Handle Add Folder button click from empty state."""
        if self.on_add_folder:
            self.on_add_folder()

    def _show_empty_state(self):
        """Show the empty state, hide sample list."""
        self.scroll_frame.grid_remove()
        self.empty_state_frame.grid(row=2, column=0, sticky="nsew")

    def _hide_empty_state(self):
        """Hide the empty state, show sample list."""
        self.empty_state_frame.grid_remove()
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(16, 12))

    def load_folder(self, folder_path):
        """Load samples from a folder and display them."""
        self._hide_empty_state()  # Hide empty state when loading folder
        self.current_path = folder_path
        self.last_folder_path = folder_path  # Track for returning from global search
        self.is_favorites_view = False
        self.is_collection_view = False
        self.is_global_search = False
        self.current_collection_id = None
        folder_name = os.path.basename(folder_path)
        self.breadcrumb.configure(text=f"\U0001f4c1 Library  \u203a  {folder_name}")

        # Scan folder and store samples (non-recursive - only files in this folder)
        self.all_samples = LibraryScanner.scan_folder(folder_path)
        self.search_query = ""

        # Apply filter and display
        self._refresh_display()

    def filter_samples(self, query: str, global_search: bool = False):
        """Filter displayed samples by search query.

        Args:
            query: Search query string.
            global_search: If True, search across entire library via database.
        """
        self.search_query = query.lower().strip()

        if global_search and self.search_query:
            # Global search - query database for all matching samples
            self._hide_empty_state()
            self.is_global_search = True
            self.is_favorites_view = False
            self.is_collection_view = False
            self.current_collection_id = None

            # Get results from database
            db = get_database()
            self.all_samples = db.search_samples(self.search_query)

            # Update breadcrumb for global search
            self.breadcrumb.configure(text=f"\U0001f50d Global Search: \"{query.strip()}\"")

            # Clear search_query since we already filtered via database
            self.search_query = ""
            self._refresh_display()

        elif not global_search and self.is_global_search:
            # Switching back from global to folder search
            self.is_global_search = False

            # Return to last folder if available
            if self.last_folder_path and os.path.exists(self.last_folder_path):
                self.load_folder(self.last_folder_path)
                self.search_query = query.lower().strip()
                self._refresh_display()
            else:
                # No folder to return to, just clear
                self.clear_samples()
        else:
            # Normal folder search
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

        # Filter samples - apply text search
        if self.search_query:
            self.filtered_samples = [
                s for s in self.all_samples
                if self._matches_search(s, self.search_query)
            ]
        else:
            self.filtered_samples = self.all_samples.copy()

        # Apply advanced filters (BPM, Key, Format)
        self.filtered_samples = [
            s for s in self.filtered_samples
            if self._passes_filters(s)
        ]

        # Sort samples based on current sort settings
        self._sort_samples()

        self.count_label.configure(text=f"{len(self.filtered_samples)} samples")

        # Create sample rows
        for sample in self.filtered_samples:
            row = SampleRow(
                self.scroll_frame, sample, self._on_play, self._on_edit,
                self._on_favorite, self._on_add_to_collection, self._on_analyze,
                show_folder_path=self.is_global_search,
                on_go_to_folder=self._on_go_to_folder if self.is_global_search else None,
                on_seek=self._on_seek
            )
            row.pack(fill="x", pady=2)
            self.sample_rows.append(row)

    def _on_play(self, row, toggle=False):
        """Handle play request from a sample row."""
        # If toggle mode and this row is already playing, just toggle (pause/resume)
        if toggle and self.current_playing_row == row:
            # Toggle the visual state - let the player handle actual pause/resume
            row.set_playing(not row.is_playing)
            if self.on_play_request:
                # Pass None to signal toggle request
                self.on_play_request(None, None, None, toggle=True)
            return

        # Update visual state for new track
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

    def _on_favorite(self, sample, is_favorite):
        """Handle favorite change from a sample row."""
        # If in favorites view and sample was unfavorited, remove it from view
        if self.is_favorites_view and not is_favorite:
            # Remove from filtered_samples and refresh
            self.all_samples = [s for s in self.all_samples if s['path'] != sample['path']]
            self._refresh_display()

        # Notify callback
        if self.on_favorite_change:
            self.on_favorite_change(sample, is_favorite)

    def _on_add_to_collection(self, row):
        """Handle add to collection request from a sample row."""
        if self.on_add_to_collection:
            self.on_add_to_collection(row.sample)

    def _on_go_to_folder(self, folder_path):
        """Handle 'Go to Folder' request - load the folder containing the sample."""
        if folder_path and os.path.exists(folder_path):
            self.is_global_search = False
            self.load_folder(folder_path)

    def _on_analyze(self, row):
        """Handle analyze request from a sample row."""
        if not ANALYZER_AVAILABLE:
            return

        def on_result(filepath, result):
            # Schedule UI update on main thread
            self.after(0, lambda: self._handle_analysis_result(row, result))

        # Start async analysis
        analyzer = get_analyzer()
        analyzer.analyze_file(row.sample['path'], callback=on_result)

    def _handle_analysis_result(self, row, result):
        """Handle analysis result on main thread."""
        if result.get('error'):
            print(f"Analysis error: {result['error']}")
            row.set_analyzing(False)
            return

        detected_bpm = result.get('bpm', '')
        detected_key = result.get('key', '')

        # Update source data in all_samples (so refresh doesn't lose it)
        sample_path = row.sample['path']
        for sample in self.all_samples:
            if sample['path'] == sample_path:
                sample['detected_bpm'] = detected_bpm
                sample['detected_key'] = detected_key
                break

        # Update row display
        row.update_analysis_result(detected_bpm, detected_key)

        # Notify callback
        if self.on_analysis_complete:
            self.on_analysis_complete(row.sample, result)

    def _on_analyze_all(self):
        """Analyze all samples in current view that are missing BPM/Key."""
        if not ANALYZER_AVAILABLE or not self.filtered_samples:
            return

        # Find samples needing analysis (no embedded BPM/Key and not already analyzed)
        samples_to_analyze = []
        for sample in self.filtered_samples:
            has_bpm = sample.get('bpm') or sample.get('detected_bpm')
            has_key = sample.get('key') or sample.get('detected_key')
            if not has_bpm or not has_key:
                samples_to_analyze.append(sample['path'])

        if not samples_to_analyze:
            self.analyze_btn.configure(text="All Analyzed")
            self.after(2000, lambda: self.analyze_btn.configure(text="Analyze All"))
            return

        # Update button to show progress
        total = len(samples_to_analyze)
        self.analyze_btn.configure(text=f"0/{total}", state="disabled")

        def on_progress(current, total, filepath):
            # Schedule UI update on main thread
            self.after(0, lambda: self.analyze_btn.configure(text=f"{current}/{total}"))

        def on_complete(results):
            # Schedule UI update on main thread
            def finish():
                self.analyze_btn.configure(text="Analyze All", state="normal")
                # Update all_samples with detected values from results
                for result in results:
                    if result.get('path'):
                        for sample in self.all_samples:
                            if sample['path'] == result['path']:
                                sample['detected_bpm'] = result.get('bpm', '')
                                sample['detected_key'] = result.get('key', '')
                                break
                self._refresh_display()
            self.after(0, finish)

        # Start batch analysis
        analyzer = get_analyzer()
        analyzer.analyze_batch(
            samples_to_analyze,
            progress_callback=on_progress,
            completion_callback=on_complete
        )

    def load_favorites(self):
        """Load all favorite samples and display them."""
        self._hide_empty_state()
        self.current_path = None
        self.is_favorites_view = True
        self.is_collection_view = False
        self.current_collection_id = None
        self.breadcrumb.configure(text="\u2605 Favorites")

        # Get favorites from database
        db = get_database()
        self.all_samples = db.get_favorites()
        self.search_query = ""

        # Apply filter and display
        self._refresh_display()

    def load_collection(self, collection_id: int):
        """Load all samples in a collection and display them."""
        self._hide_empty_state()
        self.current_path = None
        self.is_favorites_view = False
        self.is_collection_view = True
        self.current_collection_id = collection_id

        # Get collection info
        db = get_database()
        collection = db.get_collection(collection_id)
        collection_name = collection['name'] if collection else "Collection"
        self.breadcrumb.configure(text=f"\u25A1 {collection_name}")

        # Get collection samples
        self.all_samples = db.get_collection_samples(collection_id)
        self.search_query = ""

        # Apply filter and display
        self._refresh_display()

    def load_recent(self):
        """Load recently played samples and display them."""
        self._hide_empty_state()
        self.current_path = None
        self.is_favorites_view = False
        self.is_collection_view = False
        self.is_global_search = False
        self.current_collection_id = None
        self.breadcrumb.configure(text="\U0001f552 Recent")

        # Get recent samples from database
        db = get_database()
        self.all_samples = db.get_recent_samples()
        self.search_query = ""

        # Apply filter and display
        self._refresh_display()

    def clear_samples(self):
        """Clear the sample list display."""
        for row in self.sample_rows:
            row.destroy()
        self.sample_rows = []
        self.all_samples = []
        self.filtered_samples = []
        self.current_playing_row = None
        self.is_favorites_view = False
        self.is_collection_view = False
        self.is_global_search = False
        self.current_collection_id = None
        self.count_label.configure(text="")

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

    def update_progress(self, percentage: float):
        """Update the progress needle on the currently playing sample row.

        Args:
            percentage: Progress as 0.0-1.0
        """
        if self.current_playing_row:
            self.current_playing_row.set_progress(percentage)

    def _on_seek(self, row, percentage: float):
        """Handle seek request from a sample row's waveform click.

        Args:
            row: The SampleRow that was clicked
            percentage: Click position as 0.0-1.0
        """
        # If clicking on a different sample than currently playing, start playing it first
        if self.current_playing_row != row:
            # Start playing this sample
            self._on_play(row, toggle=False)

        # Request seek via callback
        if self.on_seek_request:
            self.on_seek_request(row.sample, percentage)

    def _get_current_sort_label(self) -> str:
        """Get the display label for current sort setting from config."""
        if not self.config_manager:
            return "Name (A-Z)"

        sort_by = self.config_manager.sort_by
        sort_order = self.config_manager.sort_order

        # Find matching label
        for label, (sb, so) in self.SORT_OPTIONS.items():
            if sb == sort_by and so == sort_order:
                return label

        return "Name (A-Z)"  # Default

    def _on_sort_change(self, selected: str):
        """Handle sort dropdown change."""
        if selected in self.SORT_OPTIONS:
            sort_by, sort_order = self.SORT_OPTIONS[selected]

            # Persist to config
            if self.config_manager:
                self.config_manager.set_sort(sort_by, sort_order)

            # Refresh display with new sort
            self._refresh_display()

    def _toggle_filters(self):
        """Toggle the filter panel visibility."""
        self.filters_visible = not self.filters_visible
        if self.filters_visible:
            self.filter_panel.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
            self.filter_btn.configure(fg_color=COLORS['accent'])
        else:
            self.filter_panel.grid_remove()
            self.filter_btn.configure(fg_color=COLORS['bg_hover'])

    def _on_filter_change(self, *args):
        """Handle filter value changes (BPM entries, format checkboxes)."""
        # Parse BPM min
        try:
            bpm_min_str = self.bpm_min_var.get().strip()
            self.filter_bpm_min = float(bpm_min_str) if bpm_min_str else None
        except ValueError:
            self.filter_bpm_min = None

        # Parse BPM max
        try:
            bpm_max_str = self.bpm_max_var.get().strip()
            self.filter_bpm_max = float(bpm_max_str) if bpm_max_str else None
        except ValueError:
            self.filter_bpm_max = None

        # Update format filters
        self.filter_formats = {fmt for fmt, var in self.format_vars.items() if var.get()}

        # Refresh display
        self._refresh_display()

    def _on_key_filter_change(self, selected: str):
        """Handle key filter dropdown change."""
        if selected == "All Keys":
            self.filter_key = None
        else:
            self.filter_key = selected
        self._refresh_display()

    def _clear_filters(self):
        """Clear all filter values."""
        self.bpm_min_var.set("")
        self.bpm_max_var.set("")
        self.key_var.set("All Keys")
        self.filter_key = None
        for var in self.format_vars.values():
            var.set(True)
        self.filter_bpm_min = None
        self.filter_bpm_max = None
        self.filter_formats = set(self.AUDIO_FORMATS)
        self._refresh_display()

    def _passes_filters(self, sample: dict) -> bool:
        """Check if a sample passes all active filters."""
        # BPM filter
        if self.filter_bpm_min is not None or self.filter_bpm_max is not None:
            bpm_str = sample.get('bpm') or sample.get('detected_bpm', '')
            if bpm_str:
                try:
                    bpm = float(bpm_str)
                    if self.filter_bpm_min is not None and bpm < self.filter_bpm_min:
                        return False
                    if self.filter_bpm_max is not None and bpm > self.filter_bpm_max:
                        return False
                except (ValueError, TypeError):
                    # Can't parse BPM, exclude if filter is active
                    return False
            else:
                # No BPM data, exclude if filter is active
                return False

        # Key filter
        if self.filter_key is not None:
            key = sample.get('key') or sample.get('detected_key', '')
            if key != self.filter_key:
                # Also check enharmonic equivalents (e.g., C# = Db)
                enharmonic = {
                    'C#': 'Db', 'Db': 'C#', 'D#': 'Eb', 'Eb': 'D#',
                    'F#': 'Gb', 'Gb': 'F#', 'G#': 'Ab', 'Ab': 'G#',
                    'A#': 'Bb', 'Bb': 'A#',
                    'C#m': 'Dbm', 'Dbm': 'C#m', 'D#m': 'Ebm', 'Ebm': 'D#m',
                    'F#m': 'Gbm', 'Gbm': 'F#m', 'G#m': 'Abm', 'Abm': 'G#m',
                    'A#m': 'Bbm', 'Bbm': 'A#m',
                }
                if key != enharmonic.get(self.filter_key, ''):
                    return False

        # Format filter
        if self.filter_formats and len(self.filter_formats) < len(self.AUDIO_FORMATS):
            ext = os.path.splitext(sample.get('filename', ''))[1].upper().lstrip('.')
            if ext not in self.filter_formats:
                return False

        return True

    def _sort_samples(self):
        """Sort filtered_samples based on current sort settings."""
        if not self.config_manager:
            return

        sort_by = self.config_manager.sort_by
        sort_order = self.config_manager.sort_order
        reverse = (sort_order == "desc")

        # Musical key order for sorting
        KEY_ORDER = {
            'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
            'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8,
            'A': 9, 'A#': 10, 'Bb': 10, 'B': 11,
            'Cm': 12, 'C#m': 13, 'Dbm': 13, 'Dm': 14, 'D#m': 15, 'Ebm': 15,
            'Em': 16, 'Fm': 17, 'F#m': 18, 'Gbm': 18, 'Gm': 19, 'G#m': 20, 'Abm': 20,
            'Am': 21, 'A#m': 22, 'Bbm': 22, 'Bm': 23,
        }

        def get_sort_key(sample):
            if sort_by == "name":
                return (sample.get('name') or sample.get('filename', '')).lower()

            elif sort_by == "bpm":
                # Get BPM (embedded or detected)
                bpm = sample.get('bpm') or sample.get('detected_bpm', '')
                try:
                    return float(bpm) if bpm else float('inf')  # Missing values at end
                except (ValueError, TypeError):
                    return float('inf')

            elif sort_by == "key":
                # Get Key (embedded or detected)
                key = sample.get('key') or sample.get('detected_key', '')
                if key:
                    # Try to get musical order, fallback to alphabetical
                    return KEY_ORDER.get(key, 100 + ord(key[0]) if key else 999)
                return 999  # Missing values at end

            elif sort_by == "duration":
                duration = sample.get('duration', 0)
                try:
                    return float(duration) if duration else float('inf')
                except (ValueError, TypeError):
                    return float('inf')

            return ""

        self.filtered_samples.sort(key=get_sort_key, reverse=reverse)
