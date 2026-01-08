"""Clients View for Beatflow - CRM interface for managing clients."""

import customtkinter as ctk
from ui.theme import COLORS, SPACING
from ui.client_card import ClientCard, ClientListRow
from ui.client_dialogs import AddClientDialog, EditClientDialog
from core.client_manager import get_client_manager


class ClientsView(ctk.CTkFrame):
    """Main view for the Client Manager feature."""

    CARD_MIN_WIDTH = 280  # Minimum card width for responsive grid
    CARD_HEIGHT = 180     # Fixed card height

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_main'], corner_radius=0, **kwargs)

        self.client_manager = get_client_manager()
        self.clients = []
        self.card_widgets = []
        self.current_view = "card"  # "card" or "list"

        self._build_ui()

        # Bind resize for responsive grid
        self.bind("<Configure>", self._on_resize)

        # Initial load
        self.after(100, self.refresh)

    def _build_ui(self):
        """Build the clients view UI."""
        # Topbar - matches Browse view topbar exactly
        self.topbar = ctk.CTkFrame(self, fg_color=COLORS['bg_dark'], height=56, corner_radius=0)
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)

        # Search bar (left side) - same placement as Browse
        search_frame = ctk.CTkFrame(self.topbar, fg_color="transparent")
        search_frame.pack(side="left", fill="y", padx=SPACING['lg'])

        self.search_var = ctk.StringVar()
        self.search_var.trace('w', self._on_search_change)
        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Search clients...",
            width=280,
            height=40,
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color=COLORS['bg_input'],
            border_width=1,
            border_color=COLORS['border'],
            corner_radius=8
        )
        search_entry.pack(side="left", pady=SPACING['sm'])

        # View toggle (Card / List) - matches Folder/Library toggle size in Browse
        self.view_mode_var = ctk.StringVar(value="Card")
        self.view_toggle = ctk.CTkSegmentedButton(
            search_frame,
            values=["Card", "List"],
            variable=self.view_mode_var,
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
            command=self._on_view_toggle
        )
        self.view_toggle.set("Card")
        self.view_toggle.pack(side="left", padx=(SPACING['sm'], 0), pady=SPACING['sm'])

        # Client count label
        self.count_label = ctk.CTkLabel(
            self.topbar,
            text="",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg_dim']
        )
        self.count_label.pack(side="right", padx=(0, SPACING['md']))

        # Add Client button (right side) - same placement as "+ Add Folder"
        self.add_btn = ctk.CTkButton(
            self.topbar,
            text="+ Add Client",
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            height=40,
            corner_radius=4,
            text_color="#ffffff",
            command=self._on_add_client
        )
        self.add_btn.pack(side="right", padx=SPACING['lg'], pady=SPACING['sm'])

        # Content area - scrollable
        self.content_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS['bg_hover'],
            scrollbar_button_hover_color=COLORS['accent']
        )
        self.content_frame.pack(fill="both", expand=True, padx=SPACING['lg'], pady=SPACING['lg'])

        # Card view container (grid)
        self.card_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.card_container.pack(fill="both", expand=True)

        # List view container
        self.list_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")

        # List header
        self.list_header = ctk.CTkFrame(self.list_container, fg_color=COLORS['bg_dark'], height=36, corner_radius=4)
        self.list_header.pack(fill="x", pady=(0, SPACING['xs']))
        self.list_header.pack_propagate(False)

        # Header labels
        name_header = ctk.CTkLabel(
            self.list_header,
            text="Name",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color=COLORS['fg_secondary'],
            anchor="w",
            width=180
        )
        name_header.pack(side="left", padx=SPACING['md'], pady=SPACING['xs'])

        email_header = ctk.CTkLabel(
            self.list_header,
            text="Email",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color=COLORS['fg_secondary'],
            anchor="w",
            width=200
        )
        email_header.pack(side="left", padx=SPACING['sm'])

        phone_header = ctk.CTkLabel(
            self.list_header,
            text="Phone",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color=COLORS['fg_secondary'],
            anchor="w",
            width=120
        )
        phone_header.pack(side="left", padx=SPACING['sm'])

        socials_header = ctk.CTkLabel(
            self.list_header,
            text="Socials",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color=COLORS['fg_secondary'],
            anchor="e"
        )
        socials_header.pack(side="right", padx=SPACING['md'])

        # List rows container
        self.list_rows_container = ctk.CTkFrame(self.list_container, fg_color="transparent")
        self.list_rows_container.pack(fill="both", expand=True)

        # Empty state
        self.empty_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")

        empty_icon = ctk.CTkLabel(
            self.empty_frame,
            text="\U0001f464",
            font=ctk.CTkFont(size=48),
            text_color=COLORS['fg_dim']
        )
        empty_icon.pack(pady=(SPACING['xl'], SPACING['md']))

        empty_msg = ctk.CTkLabel(
            self.empty_frame,
            text="No Clients Yet",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=COLORS['fg']
        )
        empty_msg.pack()

        empty_submsg = ctk.CTkLabel(
            self.empty_frame,
            text="Add your first client to start tracking\nyour network and contacts.",
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=COLORS['fg_secondary'],
            justify="center"
        )
        empty_submsg.pack(pady=(SPACING['sm'], SPACING['lg']))

        empty_add_btn = ctk.CTkButton(
            self.empty_frame,
            text="+ Add Client",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            height=44,
            width=160,
            corner_radius=8,
            text_color="#ffffff",
            command=self._on_add_client
        )
        empty_add_btn.pack()

    def refresh(self):
        """Refresh the client list from database."""
        search_query = self.search_var.get().strip() if hasattr(self, 'search_var') else None
        self.clients = self.client_manager.get_clients(search=search_query if search_query else None)

        # Update count
        count = len(self.clients)
        self.count_label.configure(text=f"{count} client{'s' if count != 1 else ''}")

        # Show appropriate view
        if not self.clients:
            self._show_empty_state()
        elif self.current_view == "card":
            self._show_card_view()
        else:
            self._show_list_view()

    def _show_empty_state(self):
        """Show empty state."""
        self.card_container.pack_forget()
        self.list_container.pack_forget()
        self.empty_frame.pack(expand=True)

    def _show_card_view(self):
        """Display clients in card grid view."""
        self.empty_frame.pack_forget()
        self.list_container.pack_forget()
        self.card_container.pack(fill="both", expand=True)

        # Clear existing cards
        for widget in self.card_widgets:
            widget.destroy()
        self.card_widgets = []

        # Calculate columns based on container width
        container_width = self.content_frame.winfo_width()
        if container_width < 100:
            container_width = 800  # Default fallback

        num_columns = max(1, container_width // (self.CARD_MIN_WIDTH + SPACING['md']))

        # Configure grid columns
        for i in range(num_columns):
            self.card_container.grid_columnconfigure(i, weight=1, uniform="card")

        # Create cards
        for idx, client in enumerate(self.clients):
            row = idx // num_columns
            col = idx % num_columns

            card = ClientCard(
                self.card_container,
                client,
                on_edit=self._on_edit_client
            )
            card.grid(row=row, column=col, padx=SPACING['xs'], pady=SPACING['xs'], sticky="nsew")
            self.card_widgets.append(card)

        # Configure rows
        num_rows = (len(self.clients) + num_columns - 1) // num_columns
        for i in range(num_rows):
            self.card_container.grid_rowconfigure(i, weight=0)

    def _show_list_view(self):
        """Display clients in list view."""
        self.empty_frame.pack_forget()
        self.card_container.pack_forget()
        self.list_container.pack(fill="both", expand=True)

        # Clear existing rows
        for widget in self.card_widgets:
            widget.destroy()
        self.card_widgets = []

        # Create rows
        for client in self.clients:
            row = ClientListRow(
                self.list_rows_container,
                client,
                on_edit=self._on_edit_client
            )
            row.pack(fill="x", pady=2)
            self.card_widgets.append(row)

    def _on_view_toggle(self, value):
        """Handle view toggle change."""
        self.current_view = "card" if value == "Card" else "list"
        if self.clients:
            if self.current_view == "card":
                self._show_card_view()
            else:
                self._show_list_view()

    def _on_search_change(self, *args):
        """Handle search text change."""
        self.refresh()

    def _on_resize(self, event):
        """Handle window resize for responsive grid."""
        if self.current_view == "card" and self.clients:
            # Debounce resize events
            if hasattr(self, '_resize_after_id'):
                self.after_cancel(self._resize_after_id)
            self._resize_after_id = self.after(100, self._show_card_view)

    def _on_add_client(self):
        """Handle Add Client button click."""
        def on_save(data):
            self.client_manager.add_client(data)
            self.refresh()

        AddClientDialog(self.winfo_toplevel(), on_save=on_save)

    def _on_edit_client(self, client):
        """Handle edit client request."""
        def on_save(client_id, data):
            self.client_manager.update_client(client_id, data)
            self.refresh()

        def on_delete(client_id):
            self.client_manager.delete_client(client_id)
            self.refresh()

        EditClientDialog(
            self.winfo_toplevel(),
            client,
            on_save=on_save,
            on_delete=on_delete
        )
