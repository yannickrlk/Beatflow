"""Client dialogs for Beatflow - Add/Edit client dialogs."""

import customtkinter as ctk
from ui.theme import COLORS, SPACING


class AddClientDialog(ctk.CTkToplevel):
    """Dialog for adding a new client."""

    def __init__(self, parent, on_save=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.on_save = on_save

        self.title("Add Client")
        self.geometry("450x500")
        self.resizable(False, False)
        self.configure(fg_color=COLORS['bg_main'])

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 500) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

        # Focus on name field
        self.name_entry.focus()

    def _build_ui(self):
        """Build the dialog UI."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="Add New Client",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=COLORS['fg']
        )
        header.pack(pady=(SPACING['md'], SPACING['sm']))

        # Scrollable form container
        form = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS['bg_hover'],
            scrollbar_button_hover_color=COLORS['accent']
        )
        form.pack(fill="both", expand=True, padx=SPACING['lg'], pady=SPACING['xs'])

        # Name field (required)
        self._create_field(form, "Name *", "name")

        # Email field
        self._create_field(form, "Email", "email")

        # Phone field
        self._create_field(form, "Phone", "phone")

        # Instagram field
        self._create_field(form, "Instagram", "instagram", placeholder="@handle or URL")

        # Twitter field
        self._create_field(form, "Twitter / X", "twitter", placeholder="@handle or URL")

        # Website field
        self._create_field(form, "Website", "website", placeholder="https://...")

        # Notes field (multiline)
        notes_label = ctk.CTkLabel(
            form,
            text="Notes",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg_secondary'],
            anchor="w"
        )
        notes_label.pack(fill="x", pady=(SPACING['sm'], SPACING['xs']))

        self.notes_entry = ctk.CTkTextbox(
            form,
            height=60,
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color=COLORS['bg_input'],
            border_width=1,
            border_color=COLORS['border'],
            corner_radius=8,
            text_color=COLORS['fg']
        )
        self.notes_entry.pack(fill="x", pady=(0, SPACING['sm']))

        # Buttons at bottom (outside scrollable area)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=SPACING['lg'], pady=SPACING['md'])

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['bg_card'],
            height=40,
            corner_radius=8,
            text_color=COLORS['fg'],
            command=self.destroy
        )
        cancel_btn.pack(side="left", expand=True, fill="x", padx=(0, SPACING['sm']))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Add Client",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            height=40,
            corner_radius=8,
            text_color="#ffffff",
            command=self._on_save
        )
        save_btn.pack(side="right", expand=True, fill="x", padx=(SPACING['sm'], 0))

    def _create_field(self, parent, label: str, field_name: str, placeholder: str = ""):
        """Create a labeled input field."""
        label_widget = ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg_secondary'],
            anchor="w"
        )
        label_widget.pack(fill="x", pady=(SPACING['sm'], SPACING['xs']))

        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            height=40,
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color=COLORS['bg_input'],
            border_width=1,
            border_color=COLORS['border'],
            corner_radius=8,
            text_color=COLORS['fg']
        )
        entry.pack(fill="x")

        # Store reference
        setattr(self, f"{field_name}_entry", entry)

    def _on_save(self):
        """Handle save button click."""
        # Validate required fields
        name = self.name_entry.get().strip()
        if not name:
            self.name_entry.configure(border_color=COLORS['error'])
            return

        # Collect all data
        data = {
            'name': name,
            'email': self.email_entry.get().strip(),
            'phone': self.phone_entry.get().strip(),
            'instagram': self.instagram_entry.get().strip(),
            'twitter': self.twitter_entry.get().strip(),
            'website': self.website_entry.get().strip(),
            'notes': self.notes_entry.get("1.0", "end-1c").strip()
        }

        # Call save callback
        if self.on_save:
            self.on_save(data)

        self.destroy()


class EditClientDialog(ctk.CTkToplevel):
    """Dialog for editing an existing client."""

    def __init__(self, parent, client: dict, on_save=None, on_delete=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.client = client
        self.on_save = on_save
        self.on_delete = on_delete

        self.title("Edit Client")
        self.geometry("450x520")
        self.resizable(False, False)
        self.configure(fg_color=COLORS['bg_main'])

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 520) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        """Build the dialog UI."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="Edit Client",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=COLORS['fg']
        )
        header.pack(pady=(SPACING['md'], SPACING['sm']))

        # Scrollable form container
        form = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS['bg_hover'],
            scrollbar_button_hover_color=COLORS['accent']
        )
        form.pack(fill="both", expand=True, padx=SPACING['lg'], pady=SPACING['xs'])

        # Name field (required)
        self._create_field(form, "Name *", "name", self.client.get('name', ''))

        # Email field
        self._create_field(form, "Email", "email", self.client.get('email', ''))

        # Phone field
        self._create_field(form, "Phone", "phone", self.client.get('phone', ''))

        # Instagram field
        self._create_field(form, "Instagram", "instagram", self.client.get('instagram', ''), "@handle or URL")

        # Twitter field
        self._create_field(form, "Twitter / X", "twitter", self.client.get('twitter', ''), "@handle or URL")

        # Website field
        self._create_field(form, "Website", "website", self.client.get('website', ''), "https://...")

        # Notes field (multiline)
        notes_label = ctk.CTkLabel(
            form,
            text="Notes",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg_secondary'],
            anchor="w"
        )
        notes_label.pack(fill="x", pady=(SPACING['sm'], SPACING['xs']))

        self.notes_entry = ctk.CTkTextbox(
            form,
            height=60,
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color=COLORS['bg_input'],
            border_width=1,
            border_color=COLORS['border'],
            corner_radius=8,
            text_color=COLORS['fg']
        )
        self.notes_entry.pack(fill="x")
        if self.client.get('notes'):
            self.notes_entry.insert("1.0", self.client['notes'])

        # Delete button inside form
        delete_btn = ctk.CTkButton(
            form,
            text="Delete Client",
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color="transparent",
            hover_color=COLORS['error'],
            height=32,
            corner_radius=6,
            text_color=COLORS['error'],
            command=self._on_delete
        )
        delete_btn.pack(pady=(SPACING['md'], SPACING['sm']))

        # Buttons at bottom (outside scrollable area)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=SPACING['lg'], pady=SPACING['md'])

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['bg_card'],
            height=40,
            corner_radius=8,
            text_color=COLORS['fg'],
            command=self.destroy
        )
        cancel_btn.pack(side="left", expand=True, fill="x", padx=(0, SPACING['sm']))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save Changes",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            height=40,
            corner_radius=8,
            text_color="#ffffff",
            command=self._on_save
        )
        save_btn.pack(side="right", expand=True, fill="x", padx=(SPACING['sm'], 0))

    def _create_field(self, parent, label: str, field_name: str, value: str = "", placeholder: str = ""):
        """Create a labeled input field with initial value."""
        label_widget = ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg_secondary'],
            anchor="w"
        )
        label_widget.pack(fill="x", pady=(SPACING['sm'], SPACING['xs']))

        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            height=40,
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color=COLORS['bg_input'],
            border_width=1,
            border_color=COLORS['border'],
            corner_radius=8,
            text_color=COLORS['fg']
        )
        entry.pack(fill="x")

        # Set initial value
        if value:
            entry.insert(0, value)

        # Store reference
        setattr(self, f"{field_name}_entry", entry)

    def _on_save(self):
        """Handle save button click."""
        # Validate required fields
        name = self.name_entry.get().strip()
        if not name:
            self.name_entry.configure(border_color=COLORS['error'])
            return

        # Collect all data
        data = {
            'name': name,
            'email': self.email_entry.get().strip(),
            'phone': self.phone_entry.get().strip(),
            'instagram': self.instagram_entry.get().strip(),
            'twitter': self.twitter_entry.get().strip(),
            'website': self.website_entry.get().strip(),
            'notes': self.notes_entry.get("1.0", "end-1c").strip()
        }

        # Call save callback
        if self.on_save:
            self.on_save(self.client['id'], data)

        self.destroy()

    def _on_delete(self):
        """Handle delete button click."""
        if self.on_delete:
            self.on_delete(self.client['id'])
        self.destroy()
