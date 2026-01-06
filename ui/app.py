"""Main application window for Beatflow."""

import os
import customtkinter as ctk
from tkinter import filedialog
from ui.theme import COLORS
from ui.sidebar import Sidebar
from ui.tree_view import LibraryTreeView
from ui.library import SampleList
from ui.player import FooterPlayer
from ui.dialogs import MetadataEditDialog
from core.config import ConfigManager
from core.scanner import LibraryScanner
from core.database import get_database


class BeatflowApp(ctk.CTk):
    """Main Beatflow application window."""

    def __init__(self):
        super().__init__()

        self.title("Beatflow")
        self.geometry("1400x850")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORS['bg_main'])

        # Initialize core
        self.config_manager = ConfigManager()

        # Grid configuration (3 columns, 3 rows)
        self.grid_columnconfigure(0, weight=0, minsize=180)  # Sidebar
        self.grid_columnconfigure(1, weight=0, minsize=200)  # Library Index
        self.grid_columnconfigure(2, weight=1)               # Main content
        self.grid_rowconfigure(0, weight=0)                  # Top bar
        self.grid_rowconfigure(1, weight=1)                  # Content
        self.grid_rowconfigure(2, weight=0)                  # Footer player

        self._build_ui()
        self._bind_shortcuts()

    def _build_ui(self):
        """Build the main UI layout."""
        # Top bar (spans columns 1-2)
        self._build_topbar()

        # Sidebar (column 0, spans all rows)
        self.sidebar = Sidebar(self, on_nav_change=self._on_nav_change)
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsew")

        # Library Index (column 1)
        self.tree_view = LibraryTreeView(
            self,
            root_folders=self.config_manager.root_folders,
            command=self._on_folder_select,
            on_favorites=self._on_favorites_select
        )
        self.tree_view.grid(row=1, column=1, sticky="nsew")

        # Sample List (column 2)
        self.sample_list = SampleList(
            self,
            on_play_request=self._on_play_request,
            on_edit_request=self._on_edit_request,
            on_favorite_change=self._on_favorite_change
        )
        self.sample_list.grid(row=1, column=2, sticky="nsew")

        # Footer Player (spans columns 1-2)
        self.player = FooterPlayer(self, on_volume_change=self._on_volume_change)
        self.player.grid(row=2, column=1, columnspan=2, sticky="ew")

        # Set initial volume from config
        self.player.set_volume(self.config_manager.volume)

    def _build_topbar(self):
        """Build the top bar with search and actions."""
        topbar = ctk.CTkFrame(self, height=56, fg_color=COLORS['bg_dark'], corner_radius=0)
        topbar.grid(row=0, column=1, columnspan=2, sticky="ew")
        topbar.grid_propagate(False)

        # Search bar
        search_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        search_frame.pack(side="left", fill="y", padx=20)

        self.search_var = ctk.StringVar()
        self.search_var.trace('w', self._on_search_change)
        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Search samples...",
            width=350,
            height=36,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['bg_input'],
            border_width=0,
            corner_radius=18
        )
        search_entry.pack(side="left", pady=10)

        # Right side actions
        actions_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        actions_frame.pack(side="right", fill="y", padx=20)

        # Profile avatar placeholder
        avatar = ctk.CTkLabel(
            actions_frame,
            text="",
            width=36,
            height=36,
            fg_color=COLORS['bg_hover'],
            corner_radius=18
        )
        avatar.pack(side="right", pady=10)

        # New Project button
        new_btn = ctk.CTkButton(
            actions_frame,
            text="+ New Project",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            height=36,
            corner_radius=8,
            text_color="#ffffff"
        )
        new_btn.pack(side="right", padx=(0, 12), pady=10)

        # Notification bell
        bell_btn = ctk.CTkButton(
            actions_frame,
            text="\U0001f514",
            width=36,
            height=36,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            corner_radius=18,
            text_color=COLORS['fg_secondary']
        )
        bell_btn.pack(side="right", padx=(0, 8), pady=10)

        # Add folder button
        add_btn = ctk.CTkButton(
            topbar,
            text="+ Add Folder",
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['accent'],
            height=32,
            corner_radius=6,
            text_color=COLORS['fg_secondary'],
            command=self._add_folder
        )
        add_btn.pack(side="left", padx=(0, 10), pady=12)

    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        self.bind('<space>', self._on_space)
        self.bind('<Escape>', self._on_escape)
        self.bind('<Left>', self._on_left)
        self.bind('<Right>', self._on_right)

    def _on_space(self, event=None):
        """Toggle play/pause on Space key."""
        # Don't trigger if focus is in an entry widget
        if isinstance(self.focus_get(), ctk.CTkEntry):
            return
        self.player.toggle_play_pause()

    def _on_escape(self, event=None):
        """Stop playback on Escape key."""
        self.player.stop()

    def _on_left(self, event=None):
        """Previous track on Left arrow."""
        if isinstance(self.focus_get(), ctk.CTkEntry):
            return
        self.player._on_prev()

    def _on_right(self, event=None):
        """Next track on Right arrow."""
        if isinstance(self.focus_get(), ctk.CTkEntry):
            return
        self.player._on_next()

    def _add_folder(self):
        """Open folder browser and add selected folder."""
        folder = filedialog.askdirectory(title="Select Sample Folder")
        if folder:
            if self.config_manager.add_folder(folder):
                self.tree_view.update_roots(self.config_manager.root_folders)

    def _on_folder_select(self, path):
        """Handle folder selection from tree view."""
        self.sample_list.load_folder(path)

    def _on_play_request(self, sample, playlist, index):
        """Handle play request from sample list."""
        self.player.load_track(sample, playlist, index)
        self.player.play()

    def _on_volume_change(self, volume):
        """Handle volume change - persist to config."""
        self.config_manager.set_volume(volume)

    def _on_search_change(self, *args):
        """Handle search text change."""
        self.sample_list.filter_samples(self.search_var.get())

    def _on_nav_change(self, nav_id):
        """Handle navigation change."""
        if nav_id == "samples":
            # Clear sample list and let user select a folder from tree
            self.sample_list.clear_samples()
            self.sample_list.breadcrumb.configure(text="\U0001f4c1 Library")

    def _on_favorites_select(self):
        """Handle favorites selection from tree view."""
        self.sample_list.load_favorites()

    def _on_favorite_change(self, sample, is_favorite):
        """Handle favorite status change."""
        # Refresh tree view to update favorites count
        self.tree_view.refresh()

    def _on_edit_request(self, sample, row):
        """Handle metadata edit request from sample list."""
        def on_save(new_metadata):
            import pygame

            filepath = sample['path']
            old_path = filepath
            renamed = False

            # Handle file rename if requested
            new_filename = new_metadata.pop('new_filename', None)
            if new_filename:
                folder = os.path.dirname(filepath)
                new_path = os.path.join(folder, new_filename)

                # Check if new filename already exists
                if os.path.exists(new_path) and new_path.lower() != filepath.lower():
                    print(f"Cannot rename: {new_filename} already exists")
                    new_filename = None
                else:
                    # Stop playback if this file is playing (releases file lock)
                    if self.player.current_sample and self.player.current_sample.get('path') == filepath:
                        self.player.stop()
                        pygame.mixer.music.unload()

                    try:
                        os.rename(filepath, new_path)
                        filepath = new_path
                        sample['path'] = new_path
                        sample['filename'] = new_filename
                        sample['name'] = os.path.splitext(new_filename)[0]
                        renamed = True

                        # Remove old entry from database
                        db = get_database()
                        db.remove_sample(old_path)
                    except PermissionError:
                        print(f"Cannot rename: file is in use")
                        new_filename = None
                    except OSError as e:
                        print(f"Error renaming file: {e}")
                        new_filename = None

            # Save metadata to file (skip for WAV since it has limited support)
            ext = os.path.splitext(filepath)[1].lower()
            if ext != '.wav':
                LibraryScanner.save_metadata(filepath, new_metadata)

            # Update sample dict with new values
            sample.update(new_metadata)

            # Update name if title changed (and not already set by rename)
            if new_metadata.get('title') and not renamed:
                sample['name'] = new_metadata['title']

            # Update file stats for cache
            try:
                stat = os.stat(filepath)
                sample['mtime'] = stat.st_mtime
                sample['size'] = stat.st_size
            except OSError:
                pass

            # Update database cache
            db = get_database()
            db.upsert_sample(sample)

            # Refresh the sample list to show updated metadata
            if self.sample_list.current_path:
                self.sample_list.load_folder(self.sample_list.current_path)

        # Open edit dialog
        MetadataEditDialog(self, sample, on_save=on_save)


if __name__ == "__main__":
    app = BeatflowApp()
    app.mainloop()
