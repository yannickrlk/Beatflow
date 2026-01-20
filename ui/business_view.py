"""Business View for ProducerOS - Main container for financial management."""

import customtkinter as ctk
from ui.theme import COLORS, SPACING


class BusinessView(ctk.CTkFrame):
    """Main view for the Business module with tabbed interface."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_main'], corner_radius=0, **kwargs)

        self.current_tab = "dashboard"

        self._build_ui()

        # Initial load
        self.after(100, self.refresh)

    def _build_ui(self):
        """Build the business view UI."""
        # Topbar
        self.topbar = ctk.CTkFrame(self, fg_color=COLORS['bg_dark'], height=56, corner_radius=0)
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)

        # Title
        title_frame = ctk.CTkFrame(self.topbar, fg_color="transparent")
        title_frame.pack(side="left", fill="y", padx=SPACING['lg'])

        title_label = ctk.CTkLabel(
            title_frame,
            text="$ Business",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=COLORS['fg']
        )
        title_label.pack(side="left", pady=SPACING['sm'])

        # Tab switcher (CTkSegmentedButton for consistency)
        self.tab_switcher = ctk.CTkSegmentedButton(
            self.topbar,
            values=["Dashboard", "Invoices", "Ledger", "Catalog"],
            command=self._on_segmented_tab_change,
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color=COLORS['bg_hover'],
            selected_color=COLORS['accent'],
            selected_hover_color=COLORS['accent_hover'],
            unselected_color=COLORS['bg_hover'],
            unselected_hover_color=COLORS['bg_card'],
            width=380,
            height=32,
            corner_radius=4,
            dynamic_resizing=False
        )
        self.tab_switcher.set("Dashboard")
        self.tab_switcher.pack(side="left", padx=SPACING['md'], pady=SPACING['sm'])

        # Content area
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=SPACING['lg'], pady=SPACING['lg'])

        # Create tab containers (lazy loaded)
        self.tab_containers = {}

        # Import and create views
        from ui.business_dashboard import BusinessDashboard
        from ui.invoices_view import InvoicesView
        from ui.ledger_view import LedgerView
        from ui.catalog_view import CatalogView

        self.tab_containers['dashboard'] = BusinessDashboard(self.content_frame)
        self.tab_containers['invoices'] = InvoicesView(self.content_frame)
        self.tab_containers['ledger'] = LedgerView(self.content_frame)
        self.tab_containers['catalog'] = CatalogView(self.content_frame)

        # Show default tab
        self.tab_containers['dashboard'].pack(fill="both", expand=True)

    def _on_segmented_tab_change(self, value):
        """Handle segmented button tab change."""
        # Map display names to tab IDs
        tab_map = {
            "Dashboard": "dashboard",
            "Invoices": "invoices",
            "Ledger": "ledger",
            "Catalog": "catalog"
        }
        tab_id = tab_map.get(value)
        if tab_id:
            self._on_tab_change(tab_id)

    def _on_tab_change(self, tab_id: str):
        """Handle tab change."""
        if tab_id == self.current_tab:
            return

        # Hide current tab
        if self.current_tab in self.tab_containers:
            self.tab_containers[self.current_tab].pack_forget()

        # Show new tab
        if tab_id in self.tab_containers:
            self.tab_containers[tab_id].pack(fill="both", expand=True)
            # Refresh the tab
            if hasattr(self.tab_containers[tab_id], 'refresh'):
                self.tab_containers[tab_id].refresh()

        self.current_tab = tab_id

    def refresh(self):
        """Refresh the current view."""
        if self.current_tab in self.tab_containers:
            tab = self.tab_containers[self.current_tab]
            if hasattr(tab, 'refresh'):
                tab.refresh()
