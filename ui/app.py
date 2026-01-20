"""Main application window for ProducerOS."""

import os
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Optional drag & drop support
try:
    import tkinterdnd2
    from tkinterdnd2 import TkinterDnD
    TKDND_AVAILABLE = True
except ImportError:
    TKDND_AVAILABLE = False
    tkinterdnd2 = None
    TkinterDnD = None

from ui.theme import COLORS, SPACING
from ui.sidebar import Sidebar
from ui.tree_view import LibraryTreeView
from ui.library import SampleList
from ui.player import FooterPlayer
# STARTUP OPTIMIZATION: Dialogs imported lazily when needed
# from ui.dialogs import MetadataEditDialog, NewCollectionDialog, AddToCollectionDialog, SettingsDialog, MetadataArchitectDialog
# STARTUP OPTIMIZATION: Secondary views imported lazily when first accessed
# from ui.network_view import ClientsView
# from ui.tasks_view import TasksView
# from ui.business_view import BusinessView
from core.config import ConfigManager
# STARTUP OPTIMIZATION: Scanner imported lazily when needed
# from core.scanner import LibraryScanner
from core.database import get_database


# Create base class with drag & drop support if available
if TKDND_AVAILABLE:
    class _DnDMixin(TkinterDnD.DnDWrapper):
        """Mixin to add drag & drop methods to CTk."""
        pass

    class ProducerOSAppBase(ctk.CTk, _DnDMixin):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)
else:
    class ProducerOSAppBase(ctk.CTk):
        pass


class ProducerOSApp(ProducerOSAppBase):
    """Main ProducerOS application window."""

    def __init__(self, folder_to_add=None):
        super().__init__()

        self.folder_to_add = folder_to_add  # CLI argument

        self.title("ProducerOS")
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
        self._setup_drag_drop()

        # Process CLI folder argument after UI is ready
        if self.folder_to_add:
            self.after(100, self._process_cli_folder)

    def _process_cli_folder(self):
        """Process folder passed via command line."""
        if self.folder_to_add and os.path.isdir(self.folder_to_add):
            # Add folder if not already in library
            if self.config_manager.add_folder(self.folder_to_add):
                self.tree_view.update_roots(self.config_manager.root_folders)
            # Load the folder
            self.sample_list.load_folder(self.folder_to_add)

    def _setup_drag_drop(self):
        """Setup drag and drop for folders."""
        if not TKDND_AVAILABLE:
            return
        try:
            # Register as drop target for files
            self.drop_target_register(tkinterdnd2.DND_FILES)

            # Bind the drop event
            self.dnd_bind('<<Drop>>', self._on_drop)
            print("Drag & drop enabled successfully")
        except Exception as e:
            print(f"Drag & drop setup failed: {e}")

    def _on_drop(self, event):
        """Handle dropped files/folders (tkinterdnd2 event)."""
        self._process_dropped_paths(event.data)

    def _process_dropped_paths(self, data):
        """Process dropped path data."""
        if isinstance(data, (list, tuple)):
            paths = list(data)
        elif isinstance(data, str):
            # Parse dropped paths (may be space-separated or in braces)
            if data.startswith('{') and data.endswith('}'):
                # Single path with spaces
                paths = [data[1:-1]]
            elif '{' in data:
                # Multiple paths with braces
                import re
                paths = re.findall(r'\{([^}]+)\}|(\S+)', data)
                paths = [p[0] or p[1] for p in paths]
            else:
                # Multiple paths or single path without spaces
                paths = data.split()
        else:
            return

        for path in paths:
            path = str(path).strip('{}')
            if os.path.isdir(path):
                # Always add to library and refresh tree view
                was_added = self.config_manager.add_folder(path)
                if was_added:
                    # Refresh tree view to show the new folder
                    self.tree_view.update_roots(self.config_manager.root_folders)

                # Load the folder (shows only files in this folder, not subfolders)
                self.sample_list.load_folder(path)

                # Select the folder in the tree view for visual feedback
                self.tree_view.select_folder(path)
                break  # Only process first valid folder

    def _build_ui(self):
        """Build the main UI layout."""
        # Track current view
        self.current_view = "browse"

        # Sidebar (column 0, spans all rows)
        self.sidebar = Sidebar(self, on_nav_change=self._on_nav_change)
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsew")

        # ==================== Browse View Components ====================
        # Top bar (spans columns 1-2)
        self._build_topbar()

        # Library Index (column 1)
        self.tree_view = LibraryTreeView(
            self,
            root_folders=self.config_manager.root_folders,
            command=self._on_folder_select,
            on_favorites=self._on_favorites_select,
            on_recent=self._on_recent_select,
            on_collection=self._on_collection_select,
            on_create_collection=self._on_create_collection,
            on_remove_folder=self._remove_folder,
            on_export_collection=self._on_export_collection
        )
        self.tree_view.grid(row=1, column=1, sticky="nsew")

        # Sample List (column 2)
        self.sample_list = SampleList(
            self,
            on_play_request=self._on_play_request,
            on_edit_request=self._on_edit_request,
            on_favorite_change=self._on_favorite_change,
            on_add_to_collection=self._on_add_to_collection,
            on_add_folder=self._add_folder,  # For empty state button
            on_seek_request=self._on_seek_request,  # Waveform click-to-seek
            config_manager=self.config_manager  # For sort persistence
        )
        self.sample_list.grid(row=1, column=2, sticky="nsew")

        # Footer Player (spans columns 1-2)
        self.player = FooterPlayer(
            self,
            on_volume_change=self._on_volume_change,
            on_progress=self._on_progress  # Waveform needle update
        )
        self.player.grid(row=2, column=1, columnspan=2, sticky="ew")

        # Set initial volume from config
        self.player.set_volume(self.config_manager.volume)

        # ==================== STARTUP OPTIMIZATION ====================
        # Secondary views are created lazily on first access
        # This significantly reduces startup time by deferring heavy imports
        self._network_view = None   # Lazy: ClientsView
        self._tasks_view = None     # Lazy: TasksView
        self._business_view = None  # Lazy: BusinessView

    # ==================== Lazy View Properties ====================

    @property
    def network_view(self):
        """Lazily create and return the network view."""
        if self._network_view is None:
            from ui.network_view import ClientsView
            self._network_view = ClientsView(self)
        return self._network_view

    @property
    def tasks_view(self):
        """Lazily create and return the tasks view."""
        if self._tasks_view is None:
            from ui.tasks_view import TasksView
            self._tasks_view = TasksView(self)
        return self._tasks_view

    @property
    def business_view(self):
        """Lazily create and return the business view."""
        if self._business_view is None:
            from ui.business_view import BusinessView
            self._business_view = BusinessView(self)
        return self._business_view

    def _build_topbar(self):
        """Build the top bar with search and actions."""
        self.topbar = ctk.CTkFrame(self, height=56, fg_color=COLORS['bg_dark'], corner_radius=0)
        self.topbar.grid(row=0, column=1, columnspan=2, sticky="ew")
        self.topbar.grid_propagate(False)
        topbar = self.topbar  # Local reference for convenience

        # Search bar (left side) - 8px grid
        search_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        search_frame.pack(side="left", fill="y", padx=SPACING['lg'])

        self.search_var = ctk.StringVar()
        self.search_var.trace('w', self._on_search_change)
        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Search samples...",
            width=280,  # Reduced to make room for toggle
            height=40,  # 8px grid: 40 = 5*8
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color=COLORS['bg_input'],
            border_width=1,
            border_color=COLORS['border'],
            corner_radius=8
        )
        search_entry.pack(side="left", pady=SPACING['sm'])

        # Search mode toggle (Folder / Library) - width=120 matches Card/List toggle in Clients view
        self.search_mode_var = ctk.StringVar(value="folder")
        self.search_mode_toggle = ctk.CTkSegmentedButton(
            search_frame,
            values=["Folder", "Library"],
            variable=self.search_mode_var,
            font=ctk.CTkFont(family="Inter", size=11),
            fg_color=COLORS['bg_hover'],
            selected_color=COLORS['accent'],
            selected_hover_color=COLORS['accent_hover'],
            unselected_color=COLORS['bg_hover'],
            unselected_hover_color=COLORS['bg_card'],
            width=160,
            height=32,
            corner_radius=4,
            dynamic_resizing=False,
            command=self._on_search_mode_change
        )
        self.search_mode_toggle.set("Folder")
        self.search_mode_toggle.pack(side="left", padx=(SPACING['sm'], 0), pady=SPACING['sm'])

        # Settings button (right side)
        settings_btn = ctk.CTkButton(
            topbar,
            text="\u2699",  # Gear icon
            font=ctk.CTkFont(size=18),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            height=40,
            width=40,
            corner_radius=4,
            text_color=COLORS['fg_secondary'],
            command=self._open_settings
        )
        settings_btn.pack(side="right", padx=(0, SPACING['lg']), pady=SPACING['sm'])

        # Tools button (Metadata Architect)
        tools_btn = ctk.CTkButton(
            topbar,
            text="\u26A1",  # Lightning bolt icon for tools
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            height=40,
            width=40,
            corner_radius=4,
            text_color=COLORS['accent_secondary'],
            command=self._open_metadata_architect
        )
        tools_btn.pack(side="right", pady=SPACING['sm'])

        # Add folder button (right side) - 8px grid
        add_btn = ctk.CTkButton(
            topbar,
            text="+ Add Folder",
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            height=40,  # 8px grid
            corner_radius=4,
            text_color="#ffffff",
            command=self._add_folder
        )
        add_btn.pack(side="right", padx=(0, SPACING['sm']), pady=SPACING['sm'])

    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        self.bind('<space>', self._on_space)
        self.bind('<Escape>', self._on_escape)
        self.bind('<Left>', self._on_left)
        self.bind('<Right>', self._on_right)

        # View switching shortcuts
        self.bind('<Control-Key-1>', self._on_ctrl_1)
        self.bind('<Control-Key-2>', self._on_ctrl_2)
        self.bind('<Control-Key-3>', self._on_ctrl_3)
        self.bind('<Control-Key-4>', self._on_ctrl_4)

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

    def _on_ctrl_1(self, event=None):
        """Switch to Browse view with Ctrl+1."""
        if not isinstance(self.focus_get(), ctk.CTkEntry):
            self._on_nav_change("browse")
            self.sidebar.set_active("browse")

    def _on_ctrl_2(self, event=None):
        """Switch to Studio Flow view with Ctrl+2."""
        if not isinstance(self.focus_get(), ctk.CTkEntry):
            self._on_nav_change("tasks")
            self.sidebar.set_active("tasks")

    def _on_ctrl_3(self, event=None):
        """Switch to Network view with Ctrl+3."""
        if not isinstance(self.focus_get(), ctk.CTkEntry):
            self._on_nav_change("network")
            self.sidebar.set_active("network")

    def _on_ctrl_4(self, event=None):
        """Switch to Business view with Ctrl+4."""
        if not isinstance(self.focus_get(), ctk.CTkEntry):
            self._on_nav_change("business")
            self.sidebar.set_active("business")

    def _add_folder(self):
        """Open folder browser and add selected folder."""
        folder = filedialog.askdirectory(title="Select Sample Folder")
        if folder:
            if self.config_manager.add_folder(folder):
                self.tree_view.update_roots(self.config_manager.root_folders)

    def _remove_folder(self, folder_path):
        """Remove a folder from the library."""
        if self.config_manager.remove_folder(folder_path):
            self.tree_view.update_roots(self.config_manager.root_folders)
            # Clear sample list if it was showing the removed folder
            if hasattr(self.sample_list, 'current_path') and self.sample_list.current_path:
                if self.sample_list.current_path.startswith(folder_path):
                    self.sample_list.clear_samples()

    def _on_folder_select(self, path):
        """Handle folder selection from tree view."""
        self.sample_list.load_folder(path)

    def _on_play_request(self, sample, playlist, index, toggle=False):
        """Handle play request from sample list."""
        if toggle:
            # Toggle play/pause for current track
            self.player.toggle_play_pause()
        else:
            # Load and play new track
            self.player.load_track(sample, playlist, index)
            self.player.play()

            # Update sample list to show which sample is playing (with sync indicator)
            if sample:
                self.sample_list.set_playing_sample(
                    sample['path'],
                    sync_active=self.player.is_sync_active()
                )

            # Track in recently played
            if sample:
                db = get_database()
                db.add_to_recent(sample['path'])

    def _on_volume_change(self, volume):
        """Handle volume change - persist to config."""
        self.config_manager.set_volume(volume)

    def _on_progress(self, progress: float):
        """Handle playback progress update - update waveform needle."""
        self.sample_list.update_progress(progress)

    def _on_seek_request(self, sample, percentage: float):
        """Handle seek request from waveform click."""
        self.player.seek(percentage)

    def _on_search_change(self, *args):
        """Handle search text change."""
        is_global = self.search_mode_toggle.get() == "Library"
        self.sample_list.filter_samples(self.search_var.get(), global_search=is_global)

    def _on_search_mode_change(self, value):
        """Handle search mode toggle change."""
        # Re-run search with new mode if there's a query
        if self.search_var.get().strip():
            is_global = value == "Library"
            self.sample_list.filter_samples(self.search_var.get(), global_search=is_global)

    def _on_nav_change(self, nav_id):
        """Handle navigation change between Browse, Network, Tasks, and Business views."""
        if nav_id == self.current_view:
            return

        if nav_id == "browse":
            # Show Browse view components
            self._show_browse_view()
        elif nav_id == "network":
            # Show Network view (contacts/collaborators)
            self._show_network_view()
        elif nav_id == "tasks":
            # Show Tasks view (Studio Flow)
            self._show_tasks_view()
        elif nav_id == "business":
            # Show Business view (Finance & invoices)
            self._show_business_view()

        self.current_view = nav_id

    def _show_browse_view(self):
        """Show the sample browser view."""
        # Hide other views (only if they exist - lazy initialization)
        if self._network_view is not None:
            self._network_view.grid_remove()
        if self._tasks_view is not None:
            self._tasks_view.grid_remove()
        if self._business_view is not None:
            self._business_view.grid_remove()

        # Show browse components
        self.topbar.grid(row=0, column=1, columnspan=2, sticky="ew")
        self.tree_view.grid(row=1, column=1, sticky="nsew")
        self.sample_list.grid(row=1, column=2, sticky="nsew")
        self.player.grid(row=2, column=1, columnspan=2, sticky="ew")

    def _show_network_view(self):
        """Show the network/contacts manager view."""
        # Hide other views
        self.topbar.grid_remove()
        self.tree_view.grid_remove()
        self.sample_list.grid_remove()
        self.player.grid_remove()
        if self._tasks_view is not None:
            self._tasks_view.grid_remove()
        if self._business_view is not None:
            self._business_view.grid_remove()

        # Show network view (spans columns 1-2, rows 0-2)
        # This triggers lazy creation via property if first access
        self.network_view.grid(row=0, column=1, columnspan=2, rowspan=3, sticky="nsew")

    def _show_tasks_view(self):
        """Show the tasks/Studio Flow view."""
        # Hide other views
        self.topbar.grid_remove()
        self.tree_view.grid_remove()
        self.sample_list.grid_remove()
        self.player.grid_remove()
        if self._network_view is not None:
            self._network_view.grid_remove()
        if self._business_view is not None:
            self._business_view.grid_remove()

        # Show tasks view (spans columns 1-2, rows 0-2)
        # This triggers lazy creation via property if first access
        self.tasks_view.grid(row=0, column=1, columnspan=2, rowspan=3, sticky="nsew")
        self.tasks_view.refresh()

    def _show_business_view(self):
        """Show the business/finance view."""
        # Hide other views
        self.topbar.grid_remove()
        self.tree_view.grid_remove()
        self.sample_list.grid_remove()
        self.player.grid_remove()
        if self._network_view is not None:
            self._network_view.grid_remove()
        if self._tasks_view is not None:
            self._tasks_view.grid_remove()

        # Show business view (spans columns 1-2, rows 0-2)
        # This triggers lazy creation via property if first access
        self.business_view.grid(row=0, column=1, columnspan=2, rowspan=3, sticky="nsew")
        self.business_view.refresh()

    def _on_favorites_select(self):
        """Handle favorites selection from tree view."""
        self.sample_list.load_favorites()

    def _on_collection_select(self, collection_id: int):
        """Handle collection selection from tree view."""
        self.sample_list.load_collection(collection_id)

    def _on_create_collection(self):
        """Handle create collection request."""
        from ui.dialogs import NewCollectionDialog

        def on_create(name):
            db = get_database()
            collection_id = db.create_collection(name)
            if collection_id:
                self.tree_view.refresh()

        NewCollectionDialog(self, on_create=on_create)

    def _on_favorite_change(self, sample, is_favorite):
        """Handle favorite status change."""
        # Refresh tree view to update favorites count
        self.tree_view.refresh()

    def _on_add_to_collection(self, sample):
        """Handle add to collection request."""
        from ui.dialogs import NewCollectionDialog, AddToCollectionDialog

        db = get_database()
        collections = db.get_collections()

        def on_select(collection_id):
            db.add_to_collection(collection_id, sample['path'])
            self.tree_view.refresh()

        def on_create_new():
            # Show create collection dialog, then add sample
            def on_create(name):
                collection_id = db.create_collection(name)
                if collection_id:
                    db.add_to_collection(collection_id, sample['path'])
                    self.tree_view.refresh()

            NewCollectionDialog(self, on_create=on_create)

        AddToCollectionDialog(
            self, collections, sample['path'],
            on_select=on_select,
            on_create_new=on_create_new
        )

    def _on_export_collection(self, collection_id: int, collection_name: str):
        """Handle export collection to ZIP request."""
        from core.exporter import get_exporter

        # Clean up collection name for filename
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in collection_name)
        default_filename = f"{safe_name}.zip"

        # Get user's Desktop or Documents as initial directory
        initial_dir = os.path.expanduser("~/Desktop")
        if not os.path.exists(initial_dir):
            initial_dir = os.path.expanduser("~/Documents")

        # Show Save As dialog
        output_path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Collection to ZIP",
            initialdir=initial_dir,
            initialfile=default_filename,
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )

        if not output_path:
            return  # User cancelled

        # Perform export
        exporter = get_exporter()
        success, message, count = exporter.export_to_zip(collection_id, output_path)

        # Show result
        if success:
            messagebox.showinfo(
                "Export Complete",
                f"{message}\n\nSaved to:\n{output_path}",
                parent=self
            )
        else:
            messagebox.showerror(
                "Export Failed",
                message,
                parent=self
            )

    def _on_edit_request(self, sample, row):
        """Handle metadata edit request from sample list."""
        from ui.dialogs import MetadataEditDialog
        from core.scanner import LibraryScanner

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

    def _open_settings(self):
        """Open the settings dialog."""
        from ui.dialogs import SettingsDialog
        SettingsDialog(self, self.config_manager)

    def _open_metadata_architect(self):
        """Open the Metadata Architect dialog."""
        from ui.dialogs import MetadataArchitectDialog

        def on_refresh():
            # Refresh sample list if a folder is loaded
            if hasattr(self.sample_list, 'current_path') and self.sample_list.current_path:
                self.sample_list.load_folder(self.sample_list.current_path)

        MetadataArchitectDialog(self, sample_list=self.sample_list, on_refresh=on_refresh)

    def _on_recent_select(self):
        """Handle recent samples selection from sidebar."""
        self.sample_list.load_recent()


if __name__ == "__main__":
    app = ProducerOSApp()
    app.mainloop()
