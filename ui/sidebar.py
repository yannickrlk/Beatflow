"""Sidebar navigation component for ProducerOS."""

import customtkinter as ctk
from ui.theme import COLORS, SPACING, SIZING, FONTS


class Sidebar(ctk.CTkFrame):
    """Main navigation sidebar with logo and navigation buttons."""

    def __init__(self, parent, on_nav_change=None, **kwargs):
        # Add right border for pro look - WIDER sidebar
        super().__init__(
            parent,
            width=220,  # Wider for bigger buttons
            corner_radius=0,
            fg_color=COLORS['bg_darkest'],
            border_width=1,
            border_color=COLORS['border'],
            **kwargs
        )
        self.grid_propagate(False)
        self.on_nav_change = on_nav_change
        self.nav_buttons = {}
        self.nav_indicators = {}  # Vertical accent bars
        self.active_nav = "browse"
        self._build_ui()

    def _build_ui(self):
        """Build the sidebar UI."""
        # Logo area - bigger and more prominent
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(24, 0))

        logo_text = ctk.CTkLabel(
            logo_frame,
            text="ProducerOS",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=COLORS['fg']
        )
        logo_text.pack(side="left")

        # Navigation items - more space from logo
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", pady=(32, 0), padx=8)

        nav_items = [
            ("browse", "Browse", True),  # Active by default
            ("network", "Network", False),
            ("tasks", "Studio Flow", False),  # Task management
            ("business", "Business", False),  # Finance & invoices
        ]

        for nav_id, label, is_active in nav_items:
            btn, indicator = self._create_nav_button(nav_frame, nav_id, label, is_active)
            self.nav_buttons[nav_id] = btn
            self.nav_indicators[nav_id] = indicator

    def _create_nav_button(self, parent, nav_id, label, is_active=False):
        """Create a navigation button with vertical accent indicator."""
        # Icon mapping
        icons = {
            "browse": "\U0001f4c1",  # Folder icon
            "network": "\U0001f310",  # Globe icon for Network
            "tasks": "\u2713",  # Checkmark icon for Studio Flow
            "business": "$",  # Dollar sign for Business
        }

        icon = icons.get(nav_id, "")
        text = f"  {icon}  {label}" if icon else f"  {label}"

        # Container for indicator + button - BIGGER for easier clicking
        row_height = 48  # Much bigger buttons
        row = ctk.CTkFrame(parent, fg_color="transparent", height=row_height)
        row.pack(fill="x", pady=4)  # More spacing between buttons
        row.pack_propagate(False)

        # Vertical accent indicator (4px wide bar on left)
        indicator = ctk.CTkFrame(
            row,
            width=4,
            fg_color=COLORS['accent'] if is_active else "transparent",
            corner_radius=2
        )
        indicator.pack(side="left", fill="y")

        # Navigation button with active background - BIGGER font
        btn = ctk.CTkButton(
            row,
            text=text,
            font=ctk.CTkFont(family=FONTS['primary'], size=14, weight="bold"),
            fg_color=COLORS['bg_hover'] if is_active else "transparent",
            hover_color=COLORS['bg_hover'],
            anchor="w",
            height=row_height,
            corner_radius=6,
            text_color=COLORS['fg'] if is_active else COLORS['fg_secondary'],
            command=lambda nid=nav_id: self._on_nav_click(nid)
        )
        btn.pack(side="left", fill="x", expand=True, padx=(8, 12))

        return btn, indicator

    def _on_nav_click(self, nav_id):
        """Handle navigation click."""
        if nav_id == self.active_nav:
            return

        # Reset old active button
        if self.active_nav in self.nav_buttons:
            self.nav_buttons[self.active_nav].configure(
                text_color=COLORS['fg_secondary'],
                fg_color="transparent"
            )
            self.nav_indicators[self.active_nav].configure(
                fg_color="transparent"
            )

        # Set new active button
        self.active_nav = nav_id
        if nav_id in self.nav_buttons:
            self.nav_buttons[nav_id].configure(
                text_color=COLORS['fg'],
                fg_color=COLORS['bg_hover']
            )
            self.nav_indicators[nav_id].configure(
                fg_color=COLORS['accent']
            )

        if self.on_nav_change:
            self.on_nav_change(nav_id)
