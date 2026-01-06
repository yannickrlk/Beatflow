"""Library Index / Tree View component for Beatflow."""

import os
import customtkinter as ctk
from ui.theme import COLORS
from core.scanner import LibraryScanner


class FolderNode(ctk.CTkFrame):
    """A single folder node in the tree view."""

    def __init__(self, parent, folder_path, level, on_select, on_toggle, is_root=False, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.folder_path = folder_path
        self.level = level
        self.on_select = on_select
        self.on_toggle = on_toggle
        self.is_root = is_root
        self.is_expanded = False
        self.children_frame = None
        self.child_nodes = []

        self._build_ui()

    def _build_ui(self):
        """Build the folder node UI."""
        folder_name = os.path.basename(self.folder_path)
        indent = 12 * self.level

        # Check if has subfolders
        has_subfolders = len(LibraryScanner.get_subfolders(self.folder_path)) > 0

        # Row container
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
                text="\u25b6",  # Right arrow
                width=20,
                height=20,
                font=ctk.CTkFont(size=8),
                fg_color="transparent",
                hover_color=COLORS['bg_hover'],
                text_color=COLORS['fg_dim'],
                corner_radius=4,
                command=self._toggle_expand
            )
            self.expand_btn.pack(side="left", padx=(4, 0))
        else:
            # Empty spacer for alignment
            spacer = ctk.CTkFrame(row, fg_color="transparent", width=24)
            spacer.pack(side="left", padx=(4, 0))

        # Folder button
        self.folder_btn = ctk.CTkButton(
            row,
            text=f" {folder_name}",
            font=ctk.CTkFont(size=12),
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
                font=ctk.CTkFont(size=10),
                fg_color=COLORS['bg_hover'],
                corner_radius=3,
                text_color=COLORS['fg_dim'],
                width=35,
                height=18
            )
            count_label.pack(side="right", padx=(0, 8))

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
                self.expand_btn.configure(text="\u25bc")  # Down arrow
                self._create_children()
            else:
                self.expand_btn.configure(text="\u25b6")  # Right arrow
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


class LibraryTreeView(ctk.CTkFrame):
    """Library index showing folders with expandable tree structure."""

    def __init__(self, master, root_folders=None, command=None, **kwargs):
        super().__init__(master, width=220, corner_radius=0, fg_color=COLORS['bg_dark'], **kwargs)
        self.grid_propagate(False)

        self.command = command
        self.root_folders = root_folders or []
        self.root_nodes = []
        self.selected_node = None

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

        for folder in self.root_folders:
            if os.path.exists(folder):
                try:
                    node = FolderNode(
                        self.scroll_frame,
                        folder,
                        level=0,
                        on_select=self._on_folder_select,
                        on_toggle=self._on_folder_toggle,
                        is_root=True
                    )
                    node.pack(fill="x", pady=1)
                    self.root_nodes.append(node)
                except Exception:
                    pass  # Skip if widget creation fails

    def _on_folder_select(self, path, node):
        """Handle folder selection."""
        # Deselect previous (check if still exists)
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
