"""Dialog components for Beatflow."""

import os
import customtkinter as ctk
from typing import Dict, Callable, Optional, List
from ui.theme import COLORS, SPACING

# Shell integration (Windows only)
try:
    from core.shell_integration import (
        is_shell_integration_enabled,
        enable_shell_integration,
        disable_shell_integration,
        WINREG_AVAILABLE
    )
except ImportError:
    WINREG_AVAILABLE = False
    is_shell_integration_enabled = lambda: False
    enable_shell_integration = lambda: (False, "Not available")
    disable_shell_integration = lambda: (False, "Not available")


class MetadataEditDialog(ctk.CTkToplevel):
    """Dialog for editing sample metadata."""

    def __init__(self, parent, sample: Dict, on_save: Callable[[Dict], None] = None):
        super().__init__(parent)

        self.sample = sample.copy()  # Work with a copy
        self.on_save = on_save
        self.result = None

        # Window setup
        self.title("Edit Metadata")
        self.geometry("450x580")
        self.resizable(False, False)
        self.configure(fg_color=COLORS['bg_dark'])

        # Store original filename for comparison
        self.original_filename = sample.get('filename', '')

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 580) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

        # Focus filename field
        self.filename_entry.focus()

    def _build_ui(self):
        """Build the dialog UI."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 16))

        title_label = ctk.CTkLabel(
            header,
            text="Edit Metadata",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['fg']
        )
        title_label.pack(side="left")

        # Form container
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        # Filename (editable, without extension)
        filename_frame = ctk.CTkFrame(form, fg_color="transparent")
        filename_frame.pack(fill="x", pady=(0, 12))

        filename_label = ctk.CTkLabel(
            filename_frame,
            text="Filename",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_secondary']
        )
        filename_label.pack(anchor="w")

        # Split filename and extension
        name_without_ext, self.file_ext = os.path.splitext(self.original_filename)

        filename_row = ctk.CTkFrame(filename_frame, fg_color="transparent")
        filename_row.pack(fill="x", pady=(4, 0))

        self.filename_entry = ctk.CTkEntry(
            filename_row,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['bg_hover'],
            border_width=0,
            height=36
        )
        self.filename_entry.pack(side="left", fill="x", expand=True)
        self.filename_entry.insert(0, name_without_ext)

        # Extension label (not editable)
        ext_label = ctk.CTkLabel(
            filename_row,
            text=self.file_ext,
            font=ctk.CTkFont(size=13),
            text_color=COLORS['fg_dim']
        )
        ext_label.pack(side="left", padx=(8, 0))

        # Title
        self.title_entry = self._create_field(form, "Title", self.sample.get('title', ''))

        # Artist
        self.artist_entry = self._create_field(form, "Artist", self.sample.get('artist', ''))

        # Album
        self.album_entry = self._create_field(form, "Album", self.sample.get('album', ''))

        # Two columns for BPM and Key
        row_frame = ctk.CTkFrame(form, fg_color="transparent")
        row_frame.pack(fill="x", pady=(0, 12))

        # BPM - use detected value if no embedded value
        bpm_value = self.sample.get('bpm', '') or self.sample.get('detected_bpm', '')
        bpm_is_detected = not self.sample.get('bpm') and self.sample.get('detected_bpm')

        bpm_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        bpm_frame.pack(side="left", fill="x", expand=True, padx=(0, 8))

        bpm_label_text = "BPM (detected)" if bpm_is_detected else "BPM"
        bpm_label = ctk.CTkLabel(
            bpm_frame,
            text=bpm_label_text,
            font=ctk.CTkFont(size=12),
            text_color=COLORS['accent_secondary'] if bpm_is_detected else COLORS['fg_secondary']
        )
        bpm_label.pack(anchor="w")

        self.bpm_entry = ctk.CTkEntry(
            bpm_frame,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['bg_hover'],
            border_width=0,
            height=36
        )
        self.bpm_entry.pack(fill="x", pady=(4, 0))
        self.bpm_entry.insert(0, bpm_value)

        # Key - use detected value if no embedded value
        key_value = self.sample.get('key', '') or self.sample.get('detected_key', '')
        key_is_detected = not self.sample.get('key') and self.sample.get('detected_key')

        key_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        key_frame.pack(side="left", fill="x", expand=True, padx=(8, 0))

        key_label_text = "Key (detected)" if key_is_detected else "Key"
        key_label = ctk.CTkLabel(
            key_frame,
            text=key_label_text,
            font=ctk.CTkFont(size=12),
            text_color=COLORS['accent_secondary'] if key_is_detected else COLORS['fg_secondary']
        )
        key_label.pack(anchor="w")

        self.key_entry = ctk.CTkEntry(
            key_frame,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['bg_hover'],
            border_width=0,
            height=36
        )
        self.key_entry.pack(fill="x", pady=(4, 0))
        self.key_entry.insert(0, key_value)

        # Genre
        self.genre_entry = self._create_field(form, "Genre", self.sample.get('genre', ''))

        # Year
        self.year_entry = self._create_field(form, "Year", self.sample.get('year', ''))

        # Format warning (for formats with limited tag support)
        ext = self.sample.get('filename', '').split('.')[-1].lower()
        if ext == 'wav':
            warning = ctk.CTkLabel(
                form,
                text="Note: WAV files have limited metadata support.",
                font=ctk.CTkFont(size=11),
                text_color=COLORS['fg_dim']
            )
            warning.pack(anchor="w", pady=(8, 0))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 20))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['bg_card'],
            text_color=COLORS['fg'],
            width=100,
            height=38,
            corner_radius=6,
            command=self._on_cancel
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'] if 'accent_hover' in COLORS else COLORS['accent'],
            text_color="white",
            width=100,
            height=38,
            corner_radius=6,
            command=self._on_save
        )
        save_btn.pack(side="right")

        # Bind Enter key to save
        self.bind("<Return>", lambda e: self._on_save())
        self.bind("<Escape>", lambda e: self._on_cancel())

    def _create_field(self, parent, label: str, value: str) -> ctk.CTkEntry:
        """Create a labeled input field."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 12))

        lbl = ctk.CTkLabel(
            frame,
            text=label,
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_secondary']
        )
        lbl.pack(anchor="w")

        entry = ctk.CTkEntry(
            frame,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['bg_hover'],
            border_width=0,
            height=36
        )
        entry.pack(fill="x", pady=(4, 0))
        entry.insert(0, value or '')

        return entry

    def _on_save(self):
        """Handle save button click."""
        # Build new filename
        new_name = self.filename_entry.get().strip()
        new_filename = new_name + self.file_ext if new_name else self.original_filename

        # Collect values
        self.result = {
            'title': self.title_entry.get().strip(),
            'artist': self.artist_entry.get().strip(),
            'album': self.album_entry.get().strip(),
            'bpm': self.bpm_entry.get().strip(),
            'key': self.key_entry.get().strip(),
            'genre': self.genre_entry.get().strip(),
            'year': self.year_entry.get().strip(),
            'new_filename': new_filename if new_filename != self.original_filename else None,
        }

        if self.on_save:
            self.on_save(self.result)

        self.destroy()

    def _on_cancel(self):
        """Handle cancel button click."""
        self.result = None
        self.destroy()


class NewCollectionDialog(ctk.CTkToplevel):
    """Dialog for creating a new collection."""

    def __init__(self, parent, on_create: Callable[[str], None] = None):
        super().__init__(parent)

        self.on_create = on_create
        self.result = None

        # Window setup
        self.title("New Collection")
        self.geometry("350x180")
        self.resizable(False, False)
        self.configure(fg_color=COLORS['bg_dark'])

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 350) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 180) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()
        self.name_entry.focus()

    def _build_ui(self):
        """Build the dialog UI."""
        # Header
        title_label = ctk.CTkLabel(
            self,
            text="Create New Collection",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['fg']
        )
        title_label.pack(padx=24, pady=(20, 16))

        # Name input
        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.pack(fill="x", padx=24)

        name_label = ctk.CTkLabel(
            name_frame,
            text="Collection Name",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_secondary']
        )
        name_label.pack(anchor="w")

        self.name_entry = ctk.CTkEntry(
            name_frame,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['bg_hover'],
            border_width=0,
            height=36,
            placeholder_text="My Collection"
        )
        self.name_entry.pack(fill="x", pady=(4, 0))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(20, 20))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['bg_card'],
            text_color=COLORS['fg'],
            width=90,
            height=36,
            corner_radius=6,
            command=self._on_cancel
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        create_btn = ctk.CTkButton(
            btn_frame,
            text="Create",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'] if 'accent_hover' in COLORS else COLORS['accent'],
            text_color="white",
            width=90,
            height=36,
            corner_radius=6,
            command=self._on_create
        )
        create_btn.pack(side="right")

        # Bind keys
        self.bind("<Return>", lambda e: self._on_create())
        self.bind("<Escape>", lambda e: self._on_cancel())

    def _on_create(self):
        """Handle create button click."""
        name = self.name_entry.get().strip()
        if name:
            self.result = name
            if self.on_create:
                self.on_create(name)
            self.destroy()

    def _on_cancel(self):
        """Handle cancel button click."""
        self.result = None
        self.destroy()


class AddToCollectionDialog(ctk.CTkToplevel):
    """Dialog for adding a sample to a collection."""

    def __init__(self, parent, collections: List[Dict], sample_path: str,
                 on_select: Callable[[int], None] = None,
                 on_create_new: Callable[[], None] = None):
        super().__init__(parent)

        self.collections = collections
        self.sample_path = sample_path
        self.on_select = on_select
        self.on_create_new = on_create_new
        self.result = None

        # Window setup
        self.title("Add to Collection")
        self.geometry("320x350")
        self.resizable(False, False)
        self.configure(fg_color=COLORS['bg_dark'])

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 320) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 350) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        """Build the dialog UI."""
        # Header
        title_label = ctk.CTkLabel(
            self,
            text="Add to Collection",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['fg']
        )
        title_label.pack(padx=20, pady=(16, 12))

        # Collections list
        list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS['bg_main'],
            corner_radius=8,
            height=200
        )
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        if not self.collections:
            hint = ctk.CTkLabel(
                list_frame,
                text="No collections yet.\nCreate one below.",
                font=ctk.CTkFont(size=12),
                text_color=COLORS['fg_dim'],
                justify="center"
            )
            hint.pack(pady=40)
        else:
            for collection in self.collections:
                self._create_collection_row(list_frame, collection)

        # Create new collection button
        new_btn = ctk.CTkButton(
            self,
            text="+ Create New Collection",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            text_color=COLORS['accent'],
            height=32,
            corner_radius=6,
            command=self._on_create_new
        )
        new_btn.pack(fill="x", padx=20, pady=(0, 12))

        # Cancel button
        cancel_btn = ctk.CTkButton(
            self,
            text="Cancel",
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['bg_card'],
            text_color=COLORS['fg'],
            height=36,
            corner_radius=6,
            command=self._on_cancel
        )
        cancel_btn.pack(fill="x", padx=20, pady=(0, 16))

        # Bind escape
        self.bind("<Escape>", lambda e: self._on_cancel())

    def _create_collection_row(self, parent, collection: Dict):
        """Create a row for a collection."""
        row = ctk.CTkButton(
            parent,
            text=f"\u25A1 {collection['name']}",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            text_color=COLORS['fg'],
            anchor="w",
            height=36,
            corner_radius=4,
            command=lambda cid=collection['id']: self._on_collection_select(cid)
        )
        row.pack(fill="x", pady=2)

    def _on_collection_select(self, collection_id: int):
        """Handle collection selection."""
        self.result = collection_id
        if self.on_select:
            self.on_select(collection_id)
        self.destroy()

    def _on_create_new(self):
        """Handle create new collection."""
        self.destroy()
        if self.on_create_new:
            self.on_create_new()

    def _on_cancel(self):
        """Handle cancel."""
        self.result = None
        self.destroy()


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog for Beatflow."""

    def __init__(self, parent, config_manager):
        super().__init__(parent)

        self.config_manager = config_manager

        # Window setup
        self.title("Settings")
        self.geometry("450x350")
        self.resizable(False, False)
        self.configure(fg_color=COLORS['bg_dark'])

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 350) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        """Build the settings UI."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING['lg'], pady=(SPACING['lg'], SPACING['md']))

        title_label = ctk.CTkLabel(
            header,
            text="Settings",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS['fg']
        )
        title_label.pack(side="left")

        # Settings container
        settings_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=8)
        settings_frame.pack(fill="both", expand=True, padx=SPACING['lg'], pady=(0, SPACING['lg']))

        # OS Integration Section
        section_label = ctk.CTkLabel(
            settings_frame,
            text="OS Integration",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['fg']
        )
        section_label.pack(anchor="w", padx=SPACING['md'], pady=(SPACING['md'], SPACING['sm']))

        # Shell integration toggle
        shell_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        shell_frame.pack(fill="x", padx=SPACING['md'], pady=SPACING['sm'])

        shell_label = ctk.CTkLabel(
            shell_frame,
            text="Windows Explorer Integration",
            font=ctk.CTkFont(size=13),
            text_color=COLORS['fg']
        )
        shell_label.pack(side="left")

        self.shell_switch_var = ctk.BooleanVar(value=is_shell_integration_enabled())
        self.shell_switch = ctk.CTkSwitch(
            shell_frame,
            text="",
            variable=self.shell_switch_var,
            onvalue=True,
            offvalue=False,
            fg_color=COLORS['bg_hover'],
            progress_color=COLORS['accent'],
            button_color=COLORS['fg'],
            button_hover_color=COLORS['fg_secondary'],
            command=self._on_shell_toggle
        )
        self.shell_switch.pack(side="right")

        # Disable if not on Windows
        if not WINREG_AVAILABLE:
            self.shell_switch.configure(state="disabled")

        shell_desc = ctk.CTkLabel(
            settings_frame,
            text="Add 'Add to Beatflow' to folder right-click menu",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_dim']
        )
        shell_desc.pack(anchor="w", padx=SPACING['md'])

        # Status label
        self.status_label = ctk.CTkLabel(
            settings_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['accent']
        )
        self.status_label.pack(anchor="w", padx=SPACING['md'], pady=(SPACING['xs'], 0))

        # Separator
        separator = ctk.CTkFrame(settings_frame, height=1, fg_color=COLORS['border'])
        separator.pack(fill="x", padx=SPACING['md'], pady=SPACING['md'])

        # App Info Section
        info_label = ctk.CTkLabel(
            settings_frame,
            text="About",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['fg']
        )
        info_label.pack(anchor="w", padx=SPACING['md'], pady=(0, SPACING['sm']))

        version_label = ctk.CTkLabel(
            settings_frame,
            text="Beatflow v1.0 - Sample Browser for Producers",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_secondary']
        )
        version_label.pack(anchor="w", padx=SPACING['md'])

        tech_label = ctk.CTkLabel(
            settings_frame,
            text="Python + CustomTkinter + Pygame",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_dim']
        )
        tech_label.pack(anchor="w", padx=SPACING['md'], pady=(2, SPACING['md']))

        # Close button
        close_btn = ctk.CTkButton(
            self,
            text="Close",
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['bg_card'],
            text_color=COLORS['fg'],
            height=38,
            width=100,
            corner_radius=6,
            command=self.destroy
        )
        close_btn.pack(pady=(0, SPACING['lg']))

        # Bind escape
        self.bind("<Escape>", lambda e: self.destroy())

    def _on_shell_toggle(self):
        """Handle shell integration toggle."""
        if self.shell_switch_var.get():
            success, message = enable_shell_integration()
        else:
            success, message = disable_shell_integration()

        if success:
            self.status_label.configure(text=message, text_color=COLORS['success'])
        else:
            self.status_label.configure(text=message, text_color=COLORS['error'])
            # Revert switch on failure
            self.shell_switch_var.set(not self.shell_switch_var.get())
