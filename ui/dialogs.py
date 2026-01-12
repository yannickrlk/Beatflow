"""Dialog components for ProducerOS."""

import os
import re
import threading
import webbrowser
import customtkinter as ctk
from typing import Dict, Callable, Optional, List
from ui.theme import COLORS, SPACING
from core.version import get_about_info, VERSION, APP_NAME

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

# Shortcuts
try:
    from core.shortcuts import GlobalShortcutListener, DEFAULT_SHORTCUTS
except ImportError:
    GlobalShortcutListener = None
    DEFAULT_SHORTCUTS = {}


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
    """Settings dialog for ProducerOS."""

    def __init__(self, parent, config_manager):
        super().__init__(parent)

        self.parent = parent
        self.config_manager = config_manager

        # Get shortcut listener from parent app if available
        self.shortcut_listener = getattr(parent, 'shortcut_listener', None)

        # Window setup
        self.title("Settings")
        self.geometry("450x520")
        self.resizable(False, False)
        self.configure(fg_color=COLORS['bg_dark'])

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 520) // 2
        self.geometry(f"+{x}+{y}")

        # Shortcut entry state
        self.shortcut_entries = {}
        self.active_shortcut_entry = None
        self.captured_modifiers = []
        self.captured_key = None

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

        # Settings container (scrollable)
        settings_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS['bg_card'],
            corner_radius=8,
            scrollbar_button_color=COLORS['bg_hover'],
            scrollbar_button_hover_color=COLORS['accent']
        )
        settings_frame.pack(fill="both", expand=True, padx=SPACING['lg'], pady=(0, SPACING['md']))

        # ===== Keyboard Shortcuts Section =====
        shortcuts_label = ctk.CTkLabel(
            settings_frame,
            text="Keyboard Shortcuts",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['fg']
        )
        shortcuts_label.pack(anchor="w", padx=SPACING['md'], pady=(SPACING['md'], SPACING['sm']))

        shortcuts_desc = ctk.CTkLabel(
            settings_frame,
            text="Global shortcuts work even when ProducerOS is in the background",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_dim']
        )
        shortcuts_desc.pack(anchor="w", padx=SPACING['md'], pady=(0, SPACING['sm']))

        # Shortcut entries
        shortcut_names = {
            'play_pause': 'Play / Pause',
            'next_track': 'Next Track',
            'prev_track': 'Previous Track'
        }

        # Get current shortcuts
        current_shortcuts = self.config_manager.config.get('shortcuts', DEFAULT_SHORTCUTS.copy())

        for action, label in shortcut_names.items():
            self._create_shortcut_row(settings_frame, action, label, current_shortcuts.get(action, {}))

        # Separator
        separator1 = ctk.CTkFrame(settings_frame, height=1, fg_color=COLORS['border'])
        separator1.pack(fill="x", padx=SPACING['md'], pady=SPACING['md'])

        # ===== OS Integration Section =====
        section_label = ctk.CTkLabel(
            settings_frame,
            text="OS Integration",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['fg']
        )
        section_label.pack(anchor="w", padx=SPACING['md'], pady=(0, SPACING['sm']))

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
            text="Add 'Add to ProducerOS' to folder right-click menu",
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
        separator2 = ctk.CTkFrame(settings_frame, height=1, fg_color=COLORS['border'])
        separator2.pack(fill="x", padx=SPACING['md'], pady=SPACING['md'])

        # ===== App Info Section =====
        about_info = get_about_info()

        info_label = ctk.CTkLabel(
            settings_frame,
            text="About",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['fg']
        )
        info_label.pack(anchor="w", padx=SPACING['md'], pady=(0, SPACING['sm']))

        version_label = ctk.CTkLabel(
            settings_frame,
            text=f"{about_info['name']} v{about_info['version']} - {about_info['description']}",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_secondary']
        )
        version_label.pack(anchor="w", padx=SPACING['md'])

        copyright_label = ctk.CTkLabel(
            settings_frame,
            text=about_info['copyright'],
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_dim']
        )
        copyright_label.pack(anchor="w", padx=SPACING['md'], pady=(2, 0))

        # Links frame
        links_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        links_frame.pack(anchor="w", padx=SPACING['md'], pady=(SPACING['sm'], SPACING['md']))

        website_btn = ctk.CTkButton(
            links_frame,
            text="Website",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            text_color=COLORS['accent'],
            height=24,
            width=70,
            corner_radius=4,
            command=lambda: webbrowser.open(about_info['website'])
        )
        website_btn.pack(side="left", padx=(0, SPACING['xs']))

        github_btn = ctk.CTkButton(
            links_frame,
            text="GitHub",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            text_color=COLORS['accent'],
            height=24,
            width=70,
            corner_radius=4,
            command=lambda: webbrowser.open(about_info['github'])
        )
        github_btn.pack(side="left", padx=(0, SPACING['xs']))

        support_btn = ctk.CTkButton(
            links_frame,
            text="Support",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            text_color=COLORS['accent'],
            height=24,
            width=70,
            corner_radius=4,
            command=lambda: webbrowser.open(f"mailto:{about_info['support_email']}")
        )
        support_btn.pack(side="left")

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

    def _create_shortcut_row(self, parent, action: str, label: str, shortcut: dict):
        """Create a row for a shortcut setting."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=SPACING['md'], pady=4)

        # Label
        lbl = ctk.CTkLabel(
            row,
            text=label,
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_secondary'],
            width=120,
            anchor="w"
        )
        lbl.pack(side="left")

        # Entry for shortcut
        entry = ctk.CTkEntry(
            row,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['bg_hover'],
            border_width=1,
            border_color=COLORS['border'],
            height=32,
            width=150
        )
        entry.pack(side="left", padx=(SPACING['sm'], 0))

        # Set current value
        if shortcut and GlobalShortcutListener:
            display = GlobalShortcutListener.format_shortcut(shortcut)
            entry.insert(0, display)

        # Store entry reference
        self.shortcut_entries[action] = entry

        # Bind focus and key events
        entry.bind("<FocusIn>", lambda e, a=action: self._on_shortcut_focus(a))
        entry.bind("<FocusOut>", lambda e, a=action: self._on_shortcut_blur(a))
        entry.bind("<KeyPress>", lambda e, a=action: self._on_shortcut_key(e, a))
        entry.bind("<KeyRelease>", self._on_shortcut_key_release)

        # Reset button
        reset_btn = ctk.CTkButton(
            row,
            text="Reset",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            text_color=COLORS['fg_dim'],
            width=50,
            height=28,
            corner_radius=4,
            command=lambda a=action: self._reset_shortcut(a)
        )
        reset_btn.pack(side="left", padx=(SPACING['sm'], 0))

    def _on_shortcut_focus(self, action: str):
        """Handle shortcut entry focus."""
        self.active_shortcut_entry = action
        self.captured_modifiers = []
        self.captured_key = None
        entry = self.shortcut_entries.get(action)
        if entry:
            entry.delete(0, 'end')
            entry.insert(0, "Press keys...")
            entry.configure(border_color=COLORS['accent'])

    def _on_shortcut_blur(self, action: str):
        """Handle shortcut entry blur."""
        entry = self.shortcut_entries.get(action)
        if entry:
            entry.configure(border_color=COLORS['border'])
            # If no valid shortcut was captured, restore previous
            current_text = entry.get()
            if current_text == "Press keys..." or not current_text:
                current_shortcuts = self.config_manager.config.get('shortcuts', DEFAULT_SHORTCUTS.copy())
                shortcut = current_shortcuts.get(action, {})
                if shortcut and GlobalShortcutListener:
                    entry.delete(0, 'end')
                    entry.insert(0, GlobalShortcutListener.format_shortcut(shortcut))
        self.active_shortcut_entry = None

    def _on_shortcut_key(self, event, action: str):
        """Handle key press in shortcut entry."""
        # Track modifiers
        if event.keysym in ('Control_L', 'Control_R'):
            if 'ctrl' not in self.captured_modifiers:
                self.captured_modifiers.append('ctrl')
            return "break"
        elif event.keysym in ('Alt_L', 'Alt_R'):
            if 'alt' not in self.captured_modifiers:
                self.captured_modifiers.append('alt')
            return "break"
        elif event.keysym in ('Shift_L', 'Shift_R'):
            if 'shift' not in self.captured_modifiers:
                self.captured_modifiers.append('shift')
            return "break"

        # Map keysym to key name
        key_map = {
            'space': 'space',
            'Left': 'left',
            'Right': 'right',
            'Up': 'up',
            'Down': 'down',
            'Return': 'enter',
            'Tab': 'tab',
        }

        # Get the key
        if event.keysym in key_map:
            self.captured_key = key_map[event.keysym]
        elif event.keysym.startswith('F') and event.keysym[1:].isdigit():
            self.captured_key = event.keysym.lower()
        elif len(event.keysym) == 1 and event.keysym.isalpha():
            self.captured_key = event.keysym.lower()
        else:
            return "break"

        # Build and save the shortcut
        if self.captured_key:
            new_shortcut = {
                'key': self.captured_key,
                'modifiers': self.captured_modifiers.copy()
            }

            # Update display
            entry = self.shortcut_entries.get(action)
            if entry and GlobalShortcutListener:
                entry.delete(0, 'end')
                entry.insert(0, GlobalShortcutListener.format_shortcut(new_shortcut))

            # Save to config
            self._save_shortcut(action, new_shortcut)

            # Move focus away
            self.focus_set()

        return "break"

    def _on_shortcut_key_release(self, event):
        """Handle key release - clear modifier tracking."""
        if event.keysym in ('Control_L', 'Control_R'):
            if 'ctrl' in self.captured_modifiers:
                self.captured_modifiers.remove('ctrl')
        elif event.keysym in ('Alt_L', 'Alt_R'):
            if 'alt' in self.captured_modifiers:
                self.captured_modifiers.remove('alt')
        elif event.keysym in ('Shift_L', 'Shift_R'):
            if 'shift' in self.captured_modifiers:
                self.captured_modifiers.remove('shift')

    def _save_shortcut(self, action: str, shortcut: dict):
        """Save a shortcut to config and reload listener."""
        # Get current shortcuts
        shortcuts = self.config_manager.config.get('shortcuts', DEFAULT_SHORTCUTS.copy())
        shortcuts[action] = shortcut
        self.config_manager.config['shortcuts'] = shortcuts
        self.config_manager.save()

        # Reload listener if available
        if self.shortcut_listener:
            self.shortcut_listener.reload_shortcuts()

    def _reset_shortcut(self, action: str):
        """Reset a shortcut to default."""
        if action in DEFAULT_SHORTCUTS:
            default = DEFAULT_SHORTCUTS[action]
            entry = self.shortcut_entries.get(action)
            if entry and GlobalShortcutListener:
                entry.delete(0, 'end')
                entry.insert(0, GlobalShortcutListener.format_shortcut(default))
            self._save_shortcut(action, default)

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


class MetadataArchitectDialog(ctk.CTkToplevel):
    """Metadata Architect - Rule-based tagging, renaming, and duplicate detection."""

    def __init__(self, parent, sample_list=None, on_refresh: Callable = None):
        super().__init__(parent)

        self.parent = parent
        self.sample_list = sample_list  # Reference to SampleList for getting samples
        self.on_refresh = on_refresh

        # Import metadata architect
        try:
            from core.metadata_architect import (
                get_rule_engine, get_regex_renamer, get_duplicate_finder,
                PRESET_RULES, RENAME_PATTERNS
            )
            from core.database import get_database
            self.rule_engine = get_rule_engine()
            self.regex_renamer = get_regex_renamer()
            self.duplicate_finder = get_duplicate_finder()
            self.db = get_database()
            self.preset_rules = PRESET_RULES
            self.rename_patterns = RENAME_PATTERNS
        except ImportError as e:
            print(f"Failed to import metadata_architect: {e}")
            self.destroy()
            return

        # Window setup
        self.title("Metadata Architect")
        self.geometry("800x650")
        self.minsize(700, 550)
        self.configure(fg_color=COLORS['bg_dark'])

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 800) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 650) // 2
        self.geometry(f"+{x}+{y}")

        # State
        self.current_tab = 'rules'
        self.rename_previews = []
        self.duplicate_groups = []

        self._build_ui()

    def _build_ui(self):
        """Build the main UI."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=50)
        header.pack(fill="x", padx=SPACING['lg'], pady=(SPACING['lg'], SPACING['md']))
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header,
            text="Metadata Architect",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS['fg']
        )
        title.pack(side="left")

        # Tab buttons
        tab_frame = ctk.CTkFrame(header, fg_color="transparent")
        tab_frame.pack(side="right")

        self.tab_buttons = {}
        tabs = [
            ('rules', 'Tagging Rules'),
            ('renamer', 'Regex Renamer'),
            ('duplicates', 'Duplicate Finder')
        ]

        for tab_id, tab_name in tabs:
            btn = ctk.CTkButton(
                tab_frame,
                text=tab_name,
                font=ctk.CTkFont(size=12),
                fg_color=COLORS['accent'] if tab_id == self.current_tab else COLORS['bg_hover'],
                hover_color=COLORS['accent_hover'] if tab_id == self.current_tab else COLORS['bg_card'],
                text_color='white' if tab_id == self.current_tab else COLORS['fg_secondary'],
                width=120,
                height=32,
                corner_radius=6,
                command=lambda t=tab_id: self._switch_tab(t)
            )
            btn.pack(side="left", padx=2)
            self.tab_buttons[tab_id] = btn

        # Content area
        self.content_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=8)
        self.content_frame.pack(fill="both", expand=True, padx=SPACING['lg'], pady=(0, SPACING['md']))

        # Build initial tab
        self._build_rules_tab()

        # Footer
        footer = ctk.CTkFrame(self, fg_color="transparent", height=50)
        footer.pack(fill="x", padx=SPACING['lg'], pady=(0, SPACING['lg']))

        close_btn = ctk.CTkButton(
            footer,
            text="Close",
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['bg_card'],
            text_color=COLORS['fg'],
            width=100,
            height=38,
            corner_radius=6,
            command=self.destroy
        )
        close_btn.pack(side="right")

        self.bind("<Escape>", lambda e: self.destroy())

    def _switch_tab(self, tab_id: str):
        """Switch to a different tab."""
        if tab_id == self.current_tab:
            return

        self.current_tab = tab_id

        # Update button styles
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.configure(
                    fg_color=COLORS['accent'],
                    hover_color=COLORS['accent_hover'],
                    text_color='white'
                )
            else:
                btn.configure(
                    fg_color=COLORS['bg_hover'],
                    hover_color=COLORS['bg_card'],
                    text_color=COLORS['fg_secondary']
                )

        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Build new tab content
        if tab_id == 'rules':
            self._build_rules_tab()
        elif tab_id == 'renamer':
            self._build_renamer_tab()
        elif tab_id == 'duplicates':
            self._build_duplicates_tab()

    # ==================== Tagging Rules Tab ====================

    def _build_rules_tab(self):
        """Build the tagging rules tab."""
        # Description
        desc = ctk.CTkLabel(
            self.content_frame,
            text="Define rules to automatically tag samples based on conditions.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_secondary']
        )
        desc.pack(anchor="w", padx=SPACING['md'], pady=(SPACING['md'], SPACING['sm']))

        # Rules list
        rules_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        rules_container.pack(fill="both", expand=True, padx=SPACING['md'], pady=(0, SPACING['sm']))

        # Scrollable rules list
        self.rules_list = ctk.CTkScrollableFrame(
            rules_container,
            fg_color=COLORS['bg_main'],
            corner_radius=6,
            scrollbar_button_color=COLORS['bg_hover'],
            scrollbar_button_hover_color=COLORS['accent']
        )
        self.rules_list.pack(fill="both", expand=True)

        self._refresh_rules_list()

        # Action buttons
        btn_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=SPACING['md'], pady=SPACING['md'])

        add_btn = ctk.CTkButton(
            btn_frame,
            text="+ Add Rule",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            text_color="white",
            width=100,
            height=34,
            corner_radius=6,
            command=self._show_add_rule_dialog
        )
        add_btn.pack(side="left")

        preset_btn = ctk.CTkButton(
            btn_frame,
            text="Add Presets",
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['bg_card'],
            text_color=COLORS['fg'],
            width=100,
            height=34,
            corner_radius=6,
            command=self._add_preset_rules
        )
        preset_btn.pack(side="left", padx=(SPACING['sm'], 0))

        apply_btn = ctk.CTkButton(
            btn_frame,
            text="Apply Rules to Library",
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['accent_secondary'],
            hover_color='#7C4DDB',
            text_color="white",
            width=150,
            height=34,
            corner_radius=6,
            command=self._apply_rules_to_library
        )
        apply_btn.pack(side="right")

    def _refresh_rules_list(self):
        """Refresh the rules list display."""
        # Clear existing
        for widget in self.rules_list.winfo_children():
            widget.destroy()

        rules = self.db.get_tagging_rules()

        if not rules:
            empty = ctk.CTkLabel(
                self.rules_list,
                text="No rules defined yet.\nClick 'Add Rule' or 'Add Presets' to get started.",
                font=ctk.CTkFont(size=12),
                text_color=COLORS['fg_dim'],
                justify="center"
            )
            empty.pack(pady=40)
            return

        for rule in rules:
            self._create_rule_row(rule)

    def _create_rule_row(self, rule: Dict):
        """Create a row for a rule."""
        row = ctk.CTkFrame(self.rules_list, fg_color=COLORS['bg_card'], corner_radius=4, height=50)
        row.pack(fill="x", padx=SPACING['sm'], pady=2)
        row.pack_propagate(False)

        # Enable toggle
        enabled_var = ctk.BooleanVar(value=rule.get('is_enabled', True))
        toggle = ctk.CTkSwitch(
            row,
            text="",
            variable=enabled_var,
            width=40,
            fg_color=COLORS['bg_hover'],
            progress_color=COLORS['accent'],
            button_color=COLORS['fg'],
            command=lambda: self._toggle_rule(rule['id'])
        )
        toggle.pack(side="left", padx=SPACING['sm'])

        # Rule info
        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=SPACING['sm'])

        name_label = ctk.CTkLabel(
            info_frame,
            text=rule.get('name', 'Unnamed Rule'),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS['fg'] if enabled_var.get() else COLORS['fg_dim']
        )
        name_label.pack(anchor="w")

        # Condition summary
        condition = f"If {rule.get('condition_field')} {rule.get('condition_operator')} '{rule.get('condition_value')}'"
        tags = ', '.join(rule.get('tags_to_add', []))
        details = f"{condition} → Add tags: {tags}"

        detail_label = ctk.CTkLabel(
            info_frame,
            text=details,
            font=ctk.CTkFont(size=10),
            text_color=COLORS['fg_dim']
        )
        detail_label.pack(anchor="w")

        # Delete button
        del_btn = ctk.CTkButton(
            row,
            text="X",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=COLORS['error'],
            text_color=COLORS['fg_dim'],
            width=30,
            height=30,
            corner_radius=4,
            command=lambda: self._delete_rule(rule['id'])
        )
        del_btn.pack(side="right", padx=SPACING['sm'])

    def _toggle_rule(self, rule_id: int):
        """Toggle a rule's enabled status."""
        self.db.toggle_tagging_rule(rule_id)
        self._refresh_rules_list()

    def _delete_rule(self, rule_id: int):
        """Delete a rule."""
        self.db.delete_tagging_rule(rule_id)
        self._refresh_rules_list()

    def _show_add_rule_dialog(self):
        """Show dialog to add a new rule."""
        AddRuleDialog(self, self.db, on_save=self._refresh_rules_list)

    def _add_preset_rules(self):
        """Add preset rules."""
        added = 0
        for preset in self.preset_rules:
            self.db.create_tagging_rule(
                name=preset['name'],
                condition_type='field',
                condition_field=preset['condition_field'],
                condition_operator=preset['condition_operator'],
                condition_value=preset['condition_value'],
                tags_to_add=preset['tags_to_add']
            )
            added += 1
        self._refresh_rules_list()

    def _apply_rules_to_library(self):
        """Apply all enabled rules to the entire library."""
        # Get all samples
        samples = self.db.get_samples_for_duplicate_check()

        if not samples:
            return

        # Run in background
        def apply_thread():
            rules = self.db.get_tagging_rules(enabled_only=True)
            total = len(samples)
            tagged = 0
            tags_added = 0

            for i, sample in enumerate(samples):
                full_sample = self.db.get_sample(sample['path'])
                if full_sample:
                    added = self.rule_engine.apply_rules_to_sample(full_sample, rules)
                    if added:
                        tagged += 1
                        tags_added += len(added)

            # Update UI
            self.after(0, lambda: self._show_apply_result(total, tagged, tags_added))

        threading.Thread(target=apply_thread, daemon=True).start()

    def _show_apply_result(self, total: int, tagged: int, tags_added: int):
        """Show result of applying rules."""
        msg = f"Processed {total} samples.\nTagged {tagged} samples with {tags_added} tags."
        ResultDialog(self, "Rules Applied", msg)
        if self.on_refresh:
            self.on_refresh()

    # ==================== Regex Renamer Tab ====================

    def _build_renamer_tab(self):
        """Build the regex renamer tab."""
        # Description
        desc = ctk.CTkLabel(
            self.content_frame,
            text="Batch rename files using regular expressions. Preview changes before applying.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_secondary']
        )
        desc.pack(anchor="w", padx=SPACING['md'], pady=(SPACING['md'], SPACING['sm']))

        # Pattern selection
        pattern_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        pattern_frame.pack(fill="x", padx=SPACING['md'], pady=SPACING['sm'])

        ctk.CTkLabel(
            pattern_frame,
            text="Preset Pattern:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_secondary']
        ).pack(side="left")

        pattern_names = [p['name'] for p in self.rename_patterns]
        self.pattern_var = ctk.StringVar(value=pattern_names[0] if pattern_names else '')
        pattern_menu = ctk.CTkOptionMenu(
            pattern_frame,
            values=pattern_names,
            variable=self.pattern_var,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['bg_hover'],
            button_color=COLORS['bg_hover'],
            button_hover_color=COLORS['accent'],
            dropdown_fg_color=COLORS['bg_card'],
            dropdown_hover_color=COLORS['bg_hover'],
            width=200,
            command=self._on_pattern_select
        )
        pattern_menu.pack(side="left", padx=SPACING['sm'])

        # Custom pattern input
        custom_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        custom_frame.pack(fill="x", padx=SPACING['md'], pady=SPACING['sm'])

        ctk.CTkLabel(
            custom_frame,
            text="Pattern:",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_secondary'],
            width=80
        ).pack(side="left")

        self.pattern_entry = ctk.CTkEntry(
            custom_frame,
            font=ctk.CTkFont(size=12, family="Consolas"),
            fg_color=COLORS['bg_hover'],
            border_width=0,
            height=32
        )
        self.pattern_entry.pack(side="left", fill="x", expand=True, padx=(0, SPACING['sm']))

        ctk.CTkLabel(
            custom_frame,
            text="Replace:",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_secondary'],
            width=70
        ).pack(side="left")

        self.replace_entry = ctk.CTkEntry(
            custom_frame,
            font=ctk.CTkFont(size=12, family="Consolas"),
            fg_color=COLORS['bg_hover'],
            border_width=0,
            height=32,
            width=150
        )
        self.replace_entry.pack(side="left")

        # Set initial pattern
        if self.rename_patterns:
            self._on_pattern_select(pattern_names[0])

        # Preview button
        preview_btn = ctk.CTkButton(
            self.content_frame,
            text="Preview Changes",
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['accent_secondary'],
            hover_color='#7C4DDB',
            text_color="white",
            width=130,
            height=32,
            corner_radius=6,
            command=self._preview_renames
        )
        preview_btn.pack(anchor="w", padx=SPACING['md'], pady=SPACING['sm'])

        # Preview list
        self.rename_list = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color=COLORS['bg_main'],
            corner_radius=6,
            scrollbar_button_color=COLORS['bg_hover'],
            scrollbar_button_hover_color=COLORS['accent']
        )
        self.rename_list.pack(fill="both", expand=True, padx=SPACING['md'], pady=(0, SPACING['sm']))

        # Apply button
        btn_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=SPACING['md'], pady=SPACING['md'])

        self.apply_rename_btn = ctk.CTkButton(
            btn_frame,
            text="Apply Renames",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            text_color="white",
            width=120,
            height=34,
            corner_radius=6,
            state="disabled",
            command=self._apply_renames
        )
        self.apply_rename_btn.pack(side="right")

        self.rename_count_label = ctk.CTkLabel(
            btn_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_secondary']
        )
        self.rename_count_label.pack(side="left")

    def _on_pattern_select(self, pattern_name: str):
        """Handle preset pattern selection."""
        for p in self.rename_patterns:
            if p['name'] == pattern_name:
                self.pattern_entry.delete(0, 'end')
                self.pattern_entry.insert(0, p['pattern'])
                self.replace_entry.delete(0, 'end')
                self.replace_entry.insert(0, p['replacement'])
                break

    def _preview_renames(self):
        """Preview rename changes."""
        pattern = self.pattern_entry.get()
        replacement = self.replace_entry.get()

        if not pattern:
            return

        # Get current samples
        samples = self._get_current_samples()
        if not samples:
            return

        paths = [s.get('path') for s in samples if s.get('path')]
        self.rename_previews = self.regex_renamer.preview_batch_rename(paths, pattern, replacement, re.IGNORECASE)

        # Update preview list
        for widget in self.rename_list.winfo_children():
            widget.destroy()

        if not self.rename_previews:
            empty = ctk.CTkLabel(
                self.rename_list,
                text="No files would be renamed with this pattern.",
                font=ctk.CTkFont(size=12),
                text_color=COLORS['fg_dim']
            )
            empty.pack(pady=40)
            self.apply_rename_btn.configure(state="disabled")
            self.rename_count_label.configure(text="")
            return

        for path, old_name, new_name in self.rename_previews:
            row = ctk.CTkFrame(self.rename_list, fg_color=COLORS['bg_card'], corner_radius=4)
            row.pack(fill="x", padx=SPACING['sm'], pady=2)

            ctk.CTkLabel(
                row,
                text=old_name,
                font=ctk.CTkFont(size=11),
                text_color=COLORS['fg_dim']
            ).pack(anchor="w", padx=SPACING['sm'], pady=(4, 0))

            ctk.CTkLabel(
                row,
                text=f"→ {new_name}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=COLORS['success']
            ).pack(anchor="w", padx=SPACING['sm'], pady=(0, 4))

        self.apply_rename_btn.configure(state="normal")
        self.rename_count_label.configure(text=f"{len(self.rename_previews)} files will be renamed")

    def _apply_renames(self):
        """Apply the previewed renames."""
        if not self.rename_previews:
            return

        renames = [(path, new_name) for path, old_name, new_name in self.rename_previews]
        result = self.regex_renamer.batch_rename(renames)

        msg = f"Renamed {result['success']} of {result['total']} files."
        if result['failed'] > 0:
            msg += f"\n{result['failed']} failed."

        ResultDialog(self, "Rename Complete", msg)

        self.rename_previews = []
        self.apply_rename_btn.configure(state="disabled")
        self._preview_renames()  # Refresh

        if self.on_refresh:
            self.on_refresh()

    # ==================== Duplicate Finder Tab ====================

    def _build_duplicates_tab(self):
        """Build the duplicate finder tab."""
        # Description
        desc = ctk.CTkLabel(
            self.content_frame,
            text="Find exact and near-exact duplicate files in your library.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_secondary']
        )
        desc.pack(anchor="w", padx=SPACING['md'], pady=(SPACING['md'], SPACING['sm']))

        # Options
        opt_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        opt_frame.pack(fill="x", padx=SPACING['md'], pady=SPACING['sm'])

        self.exact_var = ctk.BooleanVar(value=True)
        exact_check = ctk.CTkCheckBox(
            opt_frame,
            text="Exact duplicates (checksum)",
            variable=self.exact_var,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            text_color=COLORS['fg']
        )
        exact_check.pack(side="left")

        self.near_var = ctk.BooleanVar(value=False)
        near_check = ctk.CTkCheckBox(
            opt_frame,
            text="Near duplicates (duration + size)",
            variable=self.near_var,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            text_color=COLORS['fg']
        )
        near_check.pack(side="left", padx=(SPACING['lg'], 0))

        # Scan button
        scan_btn = ctk.CTkButton(
            self.content_frame,
            text="Scan for Duplicates",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            text_color="white",
            width=150,
            height=34,
            corner_radius=6,
            command=self._scan_duplicates
        )
        scan_btn.pack(anchor="w", padx=SPACING['md'], pady=SPACING['sm'])

        # Progress label
        self.dup_progress = ctk.CTkLabel(
            self.content_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_dim']
        )
        self.dup_progress.pack(anchor="w", padx=SPACING['md'])

        # Results list
        self.dup_list = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color=COLORS['bg_main'],
            corner_radius=6,
            scrollbar_button_color=COLORS['bg_hover'],
            scrollbar_button_hover_color=COLORS['accent']
        )
        self.dup_list.pack(fill="both", expand=True, padx=SPACING['md'], pady=(SPACING['sm'], SPACING['md']))

    def _scan_duplicates(self):
        """Scan for duplicates."""
        self.dup_progress.configure(text="Scanning...")

        for widget in self.dup_list.winfo_children():
            widget.destroy()

        def scan_thread():
            groups = []

            if self.exact_var.get():
                def progress(current, total):
                    self.after(0, lambda: self.dup_progress.configure(
                        text=f"Checking checksums... {current}/{total}"
                    ))
                exact_groups = self.duplicate_finder.find_exact_duplicates(progress_callback=progress)
                for g in exact_groups:
                    for s in g:
                        s['dup_type'] = 'exact'
                groups.extend(exact_groups)

            if self.near_var.get():
                self.after(0, lambda: self.dup_progress.configure(text="Checking near-duplicates..."))
                near_groups = self.duplicate_finder.find_near_duplicates()
                for g in near_groups:
                    for s in g:
                        s['dup_type'] = 'near'
                groups.extend(near_groups)

            self.duplicate_groups = groups
            self.after(0, self._show_duplicate_results)

        threading.Thread(target=scan_thread, daemon=True).start()

    def _show_duplicate_results(self):
        """Show duplicate scan results."""
        for widget in self.dup_list.winfo_children():
            widget.destroy()

        if not self.duplicate_groups:
            self.dup_progress.configure(text="No duplicates found!")
            empty = ctk.CTkLabel(
                self.dup_list,
                text="No duplicate files found in your library.",
                font=ctk.CTkFont(size=12),
                text_color=COLORS['fg_dim']
            )
            empty.pack(pady=40)
            return

        total_dupes = sum(len(g) - 1 for g in self.duplicate_groups)
        self.dup_progress.configure(
            text=f"Found {len(self.duplicate_groups)} duplicate groups ({total_dupes} extra files)"
        )

        for i, group in enumerate(self.duplicate_groups):
            self._create_duplicate_group(i, group)

    def _create_duplicate_group(self, index: int, group: List[Dict]):
        """Create a UI group for duplicates."""
        group_frame = ctk.CTkFrame(self.dup_list, fg_color=COLORS['bg_card'], corner_radius=6)
        group_frame.pack(fill="x", padx=SPACING['sm'], pady=SPACING['sm'])

        # Group header
        dup_type = group[0].get('dup_type', 'exact')
        header = ctk.CTkLabel(
            group_frame,
            text=f"Group {index + 1} - {len(group)} files ({dup_type})",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS['accent_secondary']
        )
        header.pack(anchor="w", padx=SPACING['sm'], pady=(SPACING['sm'], 4))

        # Files in group
        for j, sample in enumerate(group):
            file_frame = ctk.CTkFrame(group_frame, fg_color=COLORS['bg_hover'], corner_radius=4)
            file_frame.pack(fill="x", padx=SPACING['sm'], pady=2)

            # Keep first file indicator
            if j == 0:
                keep_label = ctk.CTkLabel(
                    file_frame,
                    text="KEEP",
                    font=ctk.CTkFont(size=9, weight="bold"),
                    text_color=COLORS['success'],
                    width=40
                )
                keep_label.pack(side="left", padx=(SPACING['sm'], 0))

            # File info
            info = ctk.CTkLabel(
                file_frame,
                text=sample.get('filename', ''),
                font=ctk.CTkFont(size=11),
                text_color=COLORS['fg']
            )
            info.pack(side="left", padx=SPACING['sm'], fill="x", expand=True)

            # Path (truncated)
            path = sample.get('path', '')
            short_path = '...' + path[-40:] if len(path) > 40 else path
            path_label = ctk.CTkLabel(
                file_frame,
                text=short_path,
                font=ctk.CTkFont(size=9),
                text_color=COLORS['fg_dim']
            )
            path_label.pack(side="left", padx=SPACING['sm'])

            # Delete button (not for first file)
            if j > 0:
                del_btn = ctk.CTkButton(
                    file_frame,
                    text="Remove",
                    font=ctk.CTkFont(size=10),
                    fg_color=COLORS['error'],
                    hover_color='#DC2626',
                    text_color="white",
                    width=60,
                    height=24,
                    corner_radius=4,
                    command=lambda p=sample['path']: self._remove_duplicate(p)
                )
                del_btn.pack(side="right", padx=SPACING['sm'], pady=4)

    def _remove_duplicate(self, path: str):
        """Remove a duplicate file."""
        success, msg = self.duplicate_finder.safe_delete(path)
        if success:
            self._scan_duplicates()  # Refresh
            if self.on_refresh:
                self.on_refresh()

    def _get_current_samples(self) -> List[Dict]:
        """Get samples from the current view."""
        if self.sample_list and hasattr(self.sample_list, 'filtered_samples'):
            return self.sample_list.filtered_samples
        # Fallback: get all samples from DB
        return self.db.get_samples_for_duplicate_check()


class AddRuleDialog(ctk.CTkToplevel):
    """Dialog for adding a new tagging rule."""

    def __init__(self, parent, db, on_save: Callable = None):
        super().__init__(parent)

        self.db = db
        self.on_save = on_save

        self.title("Add Tagging Rule")
        self.geometry("450x400")
        self.resizable(False, False)
        self.configure(fg_color=COLORS['bg_dark'])

        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 400) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        """Build the dialog UI."""
        # Title
        ctk.CTkLabel(
            self,
            text="Create Tagging Rule",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['fg']
        ).pack(padx=SPACING['lg'], pady=(SPACING['lg'], SPACING['md']))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=SPACING['lg'])

        # Rule name
        ctk.CTkLabel(
            form, text="Rule Name",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_secondary']
        ).pack(anchor="w")

        self.name_entry = ctk.CTkEntry(
            form,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['bg_hover'],
            border_width=0,
            height=36,
            placeholder_text="My Rule"
        )
        self.name_entry.pack(fill="x", pady=(4, SPACING['sm']))

        # Condition field
        ctk.CTkLabel(
            form, text="If this field...",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_secondary']
        ).pack(anchor="w")

        self.field_var = ctk.StringVar(value='filename')
        field_menu = ctk.CTkOptionMenu(
            form,
            values=['filename', 'folder', 'bpm', 'key', 'artist', 'genre'],
            variable=self.field_var,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['bg_hover'],
            button_color=COLORS['bg_hover'],
            button_hover_color=COLORS['accent'],
            dropdown_fg_color=COLORS['bg_card'],
            width=200
        )
        field_menu.pack(anchor="w", pady=(4, SPACING['sm']))

        # Operator
        ctk.CTkLabel(
            form, text="...matches this condition...",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_secondary']
        ).pack(anchor="w")

        self.op_var = ctk.StringVar(value='contains')
        op_menu = ctk.CTkOptionMenu(
            form,
            values=['contains', 'equals', 'starts_with', 'ends_with', 'greater_than', 'less_than'],
            variable=self.op_var,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['bg_hover'],
            button_color=COLORS['bg_hover'],
            button_hover_color=COLORS['accent'],
            dropdown_fg_color=COLORS['bg_card'],
            width=200
        )
        op_menu.pack(anchor="w", pady=(4, SPACING['sm']))

        # Value
        ctk.CTkLabel(
            form, text="Value to match",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_secondary']
        ).pack(anchor="w")

        self.value_entry = ctk.CTkEntry(
            form,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['bg_hover'],
            border_width=0,
            height=36,
            placeholder_text="e.g., kick, 808, minor"
        )
        self.value_entry.pack(fill="x", pady=(4, SPACING['sm']))

        # Tags to add
        ctk.CTkLabel(
            form, text="Tags to add (comma-separated)",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_secondary']
        ).pack(anchor="w")

        self.tags_entry = ctk.CTkEntry(
            form,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['bg_hover'],
            border_width=0,
            height=36,
            placeholder_text="e.g., drums, percussion"
        )
        self.tags_entry.pack(fill="x", pady=(4, SPACING['md']))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=SPACING['lg'], pady=SPACING['lg'])

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
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=(SPACING['sm'], 0))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save Rule",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            text_color="white",
            width=100,
            height=36,
            corner_radius=6,
            command=self._save_rule
        )
        save_btn.pack(side="right")

        self.bind("<Escape>", lambda e: self.destroy())

    def _save_rule(self):
        """Save the rule."""
        name = self.name_entry.get().strip()
        value = self.value_entry.get().strip()
        tags_str = self.tags_entry.get().strip()

        if not name or not value or not tags_str:
            return

        tags = [t.strip() for t in tags_str.split(',') if t.strip()]

        self.db.create_tagging_rule(
            name=name,
            condition_type='field',
            condition_field=self.field_var.get(),
            condition_operator=self.op_var.get(),
            condition_value=value,
            tags_to_add=tags
        )

        if self.on_save:
            self.on_save()

        self.destroy()


class ResultDialog(ctk.CTkToplevel):
    """Simple dialog for showing results."""

    def __init__(self, parent, title: str, message: str):
        super().__init__(parent)

        self.title(title)
        self.geometry("350x180")
        self.resizable(False, False)
        self.configure(fg_color=COLORS['bg_dark'])

        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 350) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 180) // 2
        self.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['fg']
        ).pack(pady=(SPACING['lg'], SPACING['sm']))

        ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_secondary'],
            justify="center"
        ).pack(pady=SPACING['md'])

        ctk.CTkButton(
            self,
            text="OK",
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            text_color="white",
            width=80,
            height=34,
            corner_radius=6,
            command=self.destroy
        ).pack(pady=SPACING['md'])

        self.bind("<Return>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self.destroy())
