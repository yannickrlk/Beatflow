"""Library Index / Tree View component for Beatflow."""

import os
import tkinter as tk
import customtkinter as ctk
from ui.theme import COLORS, SPACING
from core.scanner import LibraryScanner
from core.database import get_database


class FolderNode(ctk.CTkFrame):
    """A single folder node in the tree view."""

    def __init__(self, parent, folder_path, level, on_select, on_toggle, is_root=False,
                 on_remove=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.folder_path = folder_path
        self.level = level
        self.on_select = on_select
        self.on_toggle = on_toggle
        self.on_remove = on_remove  # Callback for removing root folders
        self.is_root = is_root
        self.is_expanded = False
        self.children_frame = None
        self.child_nodes = []

        self._build_ui()
        if self.is_root:
            self._bind_context_menu()

    def _build_ui(self):
        """Build the folder node UI."""
        folder_name = os.path.basename(self.folder_path)
        indent = SPACING['md'] * self.level  # 16px per level

        # Check if has subfolders
        has_subfolders = len(LibraryScanner.get_subfolders(self.folder_path)) > 0

        # Row container - 8px grid
        row = ctk.CTkFrame(self, fg_color="transparent", height=32)
        row.pack(fill="x")
        row.pack_propagate(False)

        # Indent spacer
        if indent > 0:
            spacer = ctk.CTkFrame(row, fg_color="transparent", width=indent)
            spacer.pack(side="left")

        # Expand/collapse button (if has subfolders)
        if has_subfolders:
            self.expand_btn = ctk.CTkButton(
                row,
                text="\u25b8",  # Thin right arrow ▸
                width=SPACING['lg'],  # 24px
                height=SPACING['lg'],
                font=ctk.CTkFont(size=10),
                fg_color="transparent",
                hover_color=COLORS['bg_hover'],
                text_color=COLORS['fg_dim'],
                corner_radius=4,
                command=self._toggle_expand
            )
            self.expand_btn.pack(side="left", padx=(SPACING['xs'], 0))
        else:
            # Empty spacer for alignment
            spacer = ctk.CTkFrame(row, fg_color="transparent", width=SPACING['lg'])
            spacer.pack(side="left", padx=(SPACING['xs'], 0))

        # Folder button
        self.folder_btn = ctk.CTkButton(
            row,
            text=f" {folder_name}",
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            anchor="w",
            height=28,
            corner_radius=4,
            text_color=COLORS['fg_secondary'],
            command=self._on_click
        )
        self.folder_btn.pack(side="left", fill="x", expand=True)

        # Sample count (only for this folder, not recursive)
        count = LibraryScanner.count_samples_shallow(self.folder_path)
        if count > 0:
            count_label = ctk.CTkLabel(
                row,
                text=str(count),
                font=ctk.CTkFont(family="Consolas", size=10),
                fg_color=COLORS['bg_hover'],
                corner_radius=3,
                text_color=COLORS['fg_dim'],
                width=32,
                height=18
            )
            count_label.pack(side="right", padx=(0, SPACING['sm']))

    def _on_click(self):
        """Handle folder click."""
        try:
            if not self.winfo_exists():
                return
            self.on_select(self.folder_path, self)
        except Exception:
            pass  # Widget was destroyed

    def _toggle_expand(self):
        """Toggle expand/collapse state."""
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        self.is_expanded = not self.is_expanded

        try:
            if self.is_expanded:
                self.expand_btn.configure(text="\u25be")  # Thin down arrow ▾
                self._create_children()
            else:
                self.expand_btn.configure(text="\u25b8")  # Thin right arrow ▸
                self._destroy_children()

            self.on_toggle(self.folder_path, self.is_expanded)
        except Exception:
            pass  # Widget was destroyed during operation

    def _create_children(self):
        """Create child folder nodes."""
        if self.children_frame is not None:
            return

        self.children_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.children_frame.pack(fill="x")

        subfolders = LibraryScanner.get_subfolders(self.folder_path)
        for subfolder in subfolders:
            child = FolderNode(
                self.children_frame,
                subfolder,
                self.level + 1,
                self.on_select,
                self.on_toggle
            )
            child.pack(fill="x")
            self.child_nodes.append(child)

    def _destroy_children(self):
        """Destroy child folder nodes."""
        if self.children_frame:
            try:
                if self.children_frame.winfo_exists():
                    self.children_frame.destroy()
            except Exception:
                pass
            self.children_frame = None
            self.child_nodes = []

    def set_selected(self, is_selected):
        """Update visual state for selection."""
        try:
            if not self.winfo_exists():
                return
            if is_selected:
                self.folder_btn.configure(fg_color=COLORS['bg_hover'], text_color=COLORS['fg'])
            else:
                self.folder_btn.configure(fg_color="transparent", text_color=COLORS['fg_secondary'])
        except Exception:
            pass  # Widget was destroyed

    def _bind_context_menu(self):
        """Bind right-click context menu for root folders."""
        self.folder_btn.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        """Show context menu for removing folder from library."""
        import tkinter as tk

        menu = tk.Menu(self, tearoff=0, bg=COLORS['bg_dark'], fg=COLORS['fg'],
                       activebackground=COLORS['accent'], activeforeground='#ffffff',
                       relief='flat', borderwidth=1)
        menu.add_command(label="Remove from Library", command=self._on_remove_click)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _on_remove_click(self):
        """Handle remove from library click."""
        if self.on_remove:
            self.on_remove(self.folder_path)


class LibraryTreeView(ctk.CTkFrame):
    """Library index showing folders with expandable tree structure."""

    def __init__(self, master, root_folders=None, command=None, on_favorites=None,
                 on_recent=None, on_collection=None, on_create_collection=None,
                 on_remove_folder=None, **kwargs):
        super().__init__(master, width=220, corner_radius=0, fg_color=COLORS['bg_dark'], **kwargs)
        self.grid_propagate(False)

        self.command = command
        self.on_favorites = on_favorites  # Callback for favorites selection
        self.on_recent = on_recent  # Callback for recent selection
        self.on_collection = on_collection  # Callback for collection selection
        self.on_create_collection = on_create_collection  # Callback for new collection
        self.on_remove_folder = on_remove_folder  # Callback for removing root folders
        self.root_folders = root_folders or []
        self.root_nodes = []
        self.selected_node = None
        self.favorites_btn = None
        self.favorites_selected = False
        self.collection_btns = {}  # Track collection buttons by ID
        self.selected_collection_id = None

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        """Build the tree view UI."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(16, 8))

        title = ctk.CTkLabel(
            header,
            text="LIBRARY INDEX",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS['fg_dim']
        )
        title.pack(side="left")

        # Scrollable folder list
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS['bg_hover'],
            scrollbar_button_hover_color=COLORS['accent']
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=4, pady=(0, 12))

    def refresh(self):
        """Re-render the folder tree."""
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        # Clear existing
        try:
            for widget in self.scroll_frame.winfo_children():
                try:
                    widget.destroy()
                except Exception:
                    pass
        except Exception:
            pass

        self.root_nodes = []
        self.selected_node = None
        self.favorites_btn = None
        self.favorites_selected = False
        self.recent_btn = None
        self.recent_selected = False
        self.collection_btns = {}
        self.selected_collection_id = None

        # Add Favorites item at the top
        self._create_favorites_item()

        # Add Recent item
        self._create_recent_item()

        # Add Collections section
        self._create_collections_section()

        # Separator before folders
        separator = ctk.CTkFrame(self.scroll_frame, fg_color=COLORS['bg_hover'], height=1)
        separator.pack(fill="x", padx=8, pady=8)

        for folder in self.root_folders:
            if os.path.exists(folder):
                try:
                    node = FolderNode(
                        self.scroll_frame,
                        folder,
                        level=0,
                        on_select=self._on_folder_select,
                        on_toggle=self._on_folder_toggle,
                        is_root=True,
                        on_remove=self.on_remove_folder
                    )
                    node.pack(fill="x", pady=1)
                    self.root_nodes.append(node)
                except Exception:
                    pass  # Skip if widget creation fails

    def _create_favorites_item(self):
        """Create the Favorites item at the top of the tree."""
        # Row container
        row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent", height=32)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        # Star icon spacer (to align with folder expand buttons)
        spacer = ctk.CTkFrame(row, fg_color="transparent", width=24)
        spacer.pack(side="left", padx=(4, 0))

        # Favorites button
        self.favorites_btn = ctk.CTkButton(
            row,
            text="\u2605 Favorites",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            anchor="w",
            height=28,
            corner_radius=4,
            text_color=COLORS['accent'],
            command=self._on_favorites_click
        )
        self.favorites_btn.pack(side="left", fill="x", expand=True)

        # Favorites count
        db = get_database()
        count = db.get_favorites_count()
        if count > 0:
            count_label = ctk.CTkLabel(
                row,
                text=str(count),
                font=ctk.CTkFont(size=10),
                fg_color=COLORS['accent'],
                corner_radius=3,
                text_color="#ffffff",
                width=35,
                height=18
            )
            count_label.pack(side="right", padx=(0, 8))

    def _on_favorites_click(self):
        """Handle favorites click."""
        # Deselect any selected folder
        if self.selected_node:
            try:
                if self.selected_node.winfo_exists():
                    self.selected_node.set_selected(False)
            except Exception:
                pass
            self.selected_node = None

        # Deselect any selected collection
        self._deselect_collection()

        # Deselect recent
        self._deselect_recent()

        # Select favorites
        self.favorites_selected = True
        self.favorites_btn.configure(fg_color=COLORS['bg_hover'])

        if self.on_favorites:
            self.on_favorites()

    def _create_recent_item(self):
        """Create the Recent item below Favorites."""
        # Row container
        row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent", height=32)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        # Clock icon spacer (to align with folder expand buttons)
        spacer = ctk.CTkFrame(row, fg_color="transparent", width=24)
        spacer.pack(side="left", padx=(4, 0))

        # Recent button
        self.recent_btn = ctk.CTkButton(
            row,
            text="\U0001f552 Recent",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            anchor="w",
            height=28,
            corner_radius=4,
            text_color=COLORS['fg_secondary'],
            command=self._on_recent_click
        )
        self.recent_btn.pack(side="left", fill="x", expand=True)

        # Recent count
        db = get_database()
        count = db.get_recent_count()
        if count > 0:
            self.recent_count_label = ctk.CTkLabel(
                row,
                text=str(count),
                font=ctk.CTkFont(size=10),
                fg_color=COLORS['bg_hover'],
                corner_radius=3,
                text_color=COLORS['fg_dim'],
                width=35,
                height=18
            )
            self.recent_count_label.pack(side="right", padx=(0, 8))

    def _on_recent_click(self):
        """Handle recent click."""
        # Deselect any selected folder
        if self.selected_node:
            try:
                if self.selected_node.winfo_exists():
                    self.selected_node.set_selected(False)
            except Exception:
                pass
            self.selected_node = None

        # Deselect any selected collection
        self._deselect_collection()

        # Deselect favorites
        self._deselect_favorites()

        # Select recent
        self.recent_selected = True
        self.recent_btn.configure(fg_color=COLORS['bg_hover'])

        if self.on_recent:
            self.on_recent()

    def _deselect_recent(self):
        """Deselect recent item."""
        if self.recent_selected and self.recent_btn:
            try:
                if self.recent_btn.winfo_exists():
                    self.recent_btn.configure(fg_color="transparent")
            except Exception:
                pass
            self.recent_selected = False

    def _deselect_favorites(self):
        """Deselect favorites item."""
        if self.favorites_selected and self.favorites_btn:
            try:
                if self.favorites_btn.winfo_exists():
                    self.favorites_btn.configure(fg_color="transparent")
            except Exception:
                pass
            self.favorites_selected = False

    def _create_collections_section(self):
        """Create the Collections section."""
        # Separator before collections
        separator = ctk.CTkFrame(self.scroll_frame, fg_color=COLORS['bg_hover'], height=1)
        separator.pack(fill="x", padx=8, pady=8)

        # Collections header with + button
        header_row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent", height=24)
        header_row.pack(fill="x", padx=8, pady=(0, 4))
        header_row.pack_propagate(False)

        collections_label = ctk.CTkLabel(
            header_row,
            text="COLLECTIONS",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS['fg_dim']
        )
        collections_label.pack(side="left")

        # Add collection button
        add_btn = ctk.CTkButton(
            header_row,
            text="+",
            width=20,
            height=20,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            text_color=COLORS['fg_dim'],
            corner_radius=4,
            command=self._on_create_collection_click
        )
        add_btn.pack(side="right")

        # Get collections from database
        db = get_database()
        collections = db.get_collections()

        if not collections:
            # Show hint when no collections
            hint = ctk.CTkLabel(
                self.scroll_frame,
                text="No collections yet",
                font=ctk.CTkFont(size=11),
                text_color=COLORS['fg_muted']
            )
            hint.pack(anchor="w", padx=32, pady=4)
        else:
            # Create collection items
            for collection in collections:
                self._create_collection_item(collection)

    def _create_collection_item(self, collection: dict):
        """Create a single collection item."""
        collection_id = collection['id']

        # Row container
        row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent", height=28)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        # Indent spacer
        spacer = ctk.CTkFrame(row, fg_color="transparent", width=24)
        spacer.pack(side="left", padx=(4, 0))

        # Collection button
        btn = ctk.CTkButton(
            row,
            text=f"\u25A1 {collection['name']}",  # Box symbol
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            anchor="w",
            height=24,
            corner_radius=4,
            text_color=COLORS['fg_secondary'],
            command=lambda cid=collection_id: self._on_collection_click(cid)
        )
        btn.pack(side="left", fill="x", expand=True)

        # Sample count
        count = collection.get('sample_count', 0)
        if count > 0:
            count_label = ctk.CTkLabel(
                row,
                text=str(count),
                font=ctk.CTkFont(size=10),
                fg_color=COLORS['bg_hover'],
                corner_radius=3,
                text_color=COLORS['fg_dim'],
                width=30,
                height=16
            )
            count_label.pack(side="right", padx=(0, 8))

        self.collection_btns[collection_id] = btn

    def _on_collection_click(self, collection_id: int):
        """Handle collection click."""
        # Deselect folder
        if self.selected_node:
            try:
                if self.selected_node.winfo_exists():
                    self.selected_node.set_selected(False)
            except Exception:
                pass
            self.selected_node = None

        # Deselect favorites
        if self.favorites_selected and self.favorites_btn:
            try:
                self.favorites_btn.configure(fg_color="transparent")
            except Exception:
                pass
            self.favorites_selected = False

        # Deselect previous collection
        self._deselect_collection()

        # Select this collection
        self.selected_collection_id = collection_id
        if collection_id in self.collection_btns:
            self.collection_btns[collection_id].configure(
                fg_color=COLORS['bg_hover'],
                text_color=COLORS['fg']
            )

        if self.on_collection:
            self.on_collection(collection_id)

    def _deselect_collection(self):
        """Deselect the currently selected collection."""
        if self.selected_collection_id and self.selected_collection_id in self.collection_btns:
            try:
                self.collection_btns[self.selected_collection_id].configure(
                    fg_color="transparent",
                    text_color=COLORS['fg_secondary']
                )
            except Exception:
                pass
        self.selected_collection_id = None

    def _on_create_collection_click(self):
        """Handle create collection button click."""
        if self.on_create_collection:
            self.on_create_collection()

    def _on_folder_select(self, path, node):
        """Handle folder selection."""
        # Deselect favorites if selected
        if self.favorites_selected and self.favorites_btn:
            try:
                self.favorites_btn.configure(fg_color="transparent")
            except Exception:
                pass
            self.favorites_selected = False

        # Deselect any selected collection
        self._deselect_collection()

        # Deselect previous folder (check if still exists)
        if self.selected_node:
            try:
                if self.selected_node.winfo_exists():
                    self.selected_node.set_selected(False)
            except Exception:
                pass  # Widget was destroyed
            self.selected_node = None

        # Select new
        self.selected_node = node
        node.set_selected(True)

        if self.command:
            self.command(path)

    def _on_folder_toggle(self, path, is_expanded):
        """Handle folder expand/collapse."""
        pass  # Could track expanded state here

    def update_roots(self, new_roots):
        """Update the root folders and refresh."""
        self.root_folders = new_roots
        self.refresh()

    def add_folder(self, folder_path):
        """Add a single folder to the list."""
        if folder_path not in self.root_folders:
            self.root_folders.append(folder_path)
            self.refresh()

    def select_folder(self, folder_path):
        """Select a folder by path in the tree view."""
        # Deselect current selection
        if self.selected_node:
            try:
                if self.selected_node.winfo_exists():
                    self.selected_node.set_selected(False)
            except Exception:
                pass
            self.selected_node = None

        # Deselect favorites and collections
        self._deselect_favorites()
        self._deselect_collection()
        self._deselect_recent()

        # Find and select the matching root node
        for node in self.root_nodes:
            if node.folder_path == folder_path:
                self.selected_node = node
                node.set_selected(True)
                return True

        return False
