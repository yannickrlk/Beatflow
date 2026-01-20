"""Network dialogs for ProducerOS - Add/Edit contact dialogs."""

import customtkinter as ctk
from ui.theme import COLORS, SPACING

# Available role options for contacts
ROLE_OPTIONS = ['Producer', 'Artist']


def show_success_toast(parent, message: str, duration: int = 2000):
    """Show a temporary success toast notification."""
    # Create toast window
    toast = ctk.CTkToplevel(parent)
    toast.withdraw()  # Hide initially
    toast.overrideredirect(True)  # Remove window decorations
    toast.attributes('-topmost', True)  # Keep on top

    # Toast content
    frame = ctk.CTkFrame(
        toast,
        fg_color=COLORS['success'],
        corner_radius=8,
        border_width=0
    )
    frame.pack(padx=2, pady=2)

    label = ctk.CTkLabel(
        frame,
        text=f"✓ {message}",
        font=ctk.CTkFont(size=13),
        text_color=COLORS['bg_darkest'],
        padx=16,
        pady=10
    )
    label.pack()

    # Position toast at bottom center of parent window
    toast.update_idletasks()
    parent_x = parent.winfo_x()
    parent_y = parent.winfo_y()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()

    toast_width = toast.winfo_reqwidth()
    toast_height = toast.winfo_reqheight()

    x = parent_x + (parent_width - toast_width) // 2
    y = parent_y + parent_height - toast_height - 60  # 60px from bottom

    toast.geometry(f"+{x}+{y}")
    toast.deiconify()  # Show toast

    # Auto-hide after duration
    def hide_toast():
        toast.destroy()

    toast.after(duration, hide_toast)


class AddClientDialog(ctk.CTkToplevel):
    """Dialog for adding a new contact."""

    def __init__(self, parent, on_save=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.on_save = on_save

        self.title("Add Contact")
        self.geometry("450x580")  # Taller to accommodate role field
        self.minsize(400, 450)
        self.resizable(True, True)
        self.configure(fg_color=COLORS['bg_main'])

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 540) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

        # Focus on name field
        self.name_entry.focus()

    def _build_ui(self):
        """Build the dialog UI."""
        # Use grid layout for proper expansion
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            self,
            text="Add New Contact",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=COLORS['fg']
        )
        header.grid(row=0, column=0, pady=(SPACING['md'], SPACING['sm']))

        # Scrollable form container
        form = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS['bg_hover'],
            scrollbar_button_hover_color=COLORS['accent']
        )
        form.grid(row=1, column=0, sticky="nsew", padx=SPACING['lg'], pady=SPACING['xs'])

        # Name field (required)
        self._create_field(form, "Name *", "name")

        # Role dropdown
        role_label = ctk.CTkLabel(
            form,
            text="Role",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg_secondary'],
            anchor="w"
        )
        role_label.pack(fill="x", pady=(SPACING['sm'], SPACING['xs']))

        self.role_var = ctk.StringVar(value="Producer")
        self.role_dropdown = ctk.CTkOptionMenu(
            form,
            variable=self.role_var,
            values=ROLE_OPTIONS,
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color=COLORS['bg_input'],
            button_color=COLORS['bg_hover'],
            button_hover_color=COLORS['accent'],
            dropdown_fg_color=COLORS['bg_card'],
            dropdown_hover_color=COLORS['bg_hover'],
            height=40,
            corner_radius=8
        )
        self.role_dropdown.pack(fill="x")

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
        btn_frame.grid(row=2, column=0, sticky="ew", padx=SPACING['lg'], pady=SPACING['md'])

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
            text="Add Contact",
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
        """Create a labeled input field with validation feedback for required fields."""
        is_required = label.endswith("*")

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

        # Add validation feedback for required fields
        if is_required:
            def on_focus_out(event):
                value = entry.get().strip()
                if not value:
                    entry.configure(border_color=COLORS['error'])
                else:
                    entry.configure(border_color=COLORS['success'])

            def on_focus_in(event):
                # Reset to neutral border when editing
                entry.configure(border_color=COLORS['border'])

            entry.bind("<FocusOut>", on_focus_out)
            entry.bind("<FocusIn>", on_focus_in)

        # Store reference
        setattr(self, f"{field_name}_entry", entry)

    def _on_save(self):
        """Handle save button click."""
        # Validate required fields
        name = self.name_entry.get().strip()
        if not name:
            self.name_entry.configure(border_color=COLORS['error'])
            return

        # Collect all data including role
        data = {
            'name': name,
            'role': self.role_var.get(),
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

        # Show success toast before destroying dialog
        show_success_toast(self.master, "Contact added successfully!")
        self.destroy()


class EditClientDialog(ctk.CTkToplevel):
    """Dialog for editing an existing contact."""

    def __init__(self, parent, client: dict, on_save=None, on_delete=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.client = client
        self.on_save = on_save
        self.on_delete = on_delete

        self.title("Edit Contact")
        self.geometry("450x600")  # Taller to accommodate role field
        self.minsize(400, 480)
        self.resizable(True, True)
        self.configure(fg_color=COLORS['bg_main'])

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 560) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        """Build the dialog UI."""
        # Use grid layout for proper expansion
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            self,
            text="Edit Contact",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=COLORS['fg']
        )
        header.grid(row=0, column=0, pady=(SPACING['md'], SPACING['sm']))

        # Scrollable form container
        form = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS['bg_hover'],
            scrollbar_button_hover_color=COLORS['accent']
        )
        form.grid(row=1, column=0, sticky="nsew", padx=SPACING['lg'], pady=SPACING['xs'])

        # Name field (required)
        self._create_field(form, "Name *", "name", self.client.get('name', ''))

        # Role dropdown
        role_label = ctk.CTkLabel(
            form,
            text="Role",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg_secondary'],
            anchor="w"
        )
        role_label.pack(fill="x", pady=(SPACING['sm'], SPACING['xs']))

        current_role = self.client.get('role', 'Producer')
        self.role_var = ctk.StringVar(value=current_role)
        self.role_dropdown = ctk.CTkOptionMenu(
            form,
            variable=self.role_var,
            values=ROLE_OPTIONS,
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color=COLORS['bg_input'],
            button_color=COLORS['bg_hover'],
            button_hover_color=COLORS['accent'],
            dropdown_fg_color=COLORS['bg_card'],
            dropdown_hover_color=COLORS['bg_hover'],
            height=40,
            corner_radius=8
        )
        self.role_dropdown.pack(fill="x")

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
            text="Delete Contact",
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
        btn_frame.grid(row=2, column=0, sticky="ew", padx=SPACING['lg'], pady=SPACING['md'])

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
        """Create a labeled input field with initial value and validation feedback for required fields."""
        is_required = label.endswith("*")

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

        # Add validation feedback for required fields
        if is_required:
            def on_focus_out(event):
                field_value = entry.get().strip()
                if not field_value:
                    entry.configure(border_color=COLORS['error'])
                else:
                    entry.configure(border_color=COLORS['success'])

            def on_focus_in(event):
                # Reset to neutral border when editing
                entry.configure(border_color=COLORS['border'])

            entry.bind("<FocusOut>", on_focus_out)
            entry.bind("<FocusIn>", on_focus_in)

        # Store reference
        setattr(self, f"{field_name}_entry", entry)

    def _on_save(self):
        """Handle save button click."""
        # Validate required fields
        name = self.name_entry.get().strip()
        if not name:
            self.name_entry.configure(border_color=COLORS['error'])
            return

        # Collect all data including role
        data = {
            'name': name,
            'role': self.role_var.get(),
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

        # Show success toast before destroying dialog
        show_success_toast(self.master, "Contact updated successfully!")
        self.destroy()

    def _on_delete(self):
        """Handle delete contact button click with confirmation."""
        from tkinter import messagebox

        # Show confirmation dialog using standard messagebox
        result = messagebox.askyesno(
            "Confirm Delete Contact",
            f"Are you sure you want to delete:\n{self.client['name']}?\n\nThis action cannot be undone.",
            icon='warning'
        )

        if result:
            if self.on_delete:
                self.on_delete(self.client['id'])
            self.destroy()
