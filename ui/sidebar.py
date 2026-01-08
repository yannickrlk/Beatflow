"""Sidebar navigation component for Beatflow."""

import customtkinter as ctk
from ui.theme import COLORS, SPACING


class Sidebar(ctk.CTkFrame):
    """Main navigation sidebar with logo and navigation buttons."""

    def __init__(self, parent, on_nav_change=None, **kwargs):
        super().__init__(parent, width=180, corner_radius=0, fg_color=COLORS['bg_darkest'], **kwargs)
        self.grid_propagate(False)
        self.on_nav_change = on_nav_change
        self.nav_buttons = {}
        self.nav_indicators = {}  # Vertical accent bars
        self.active_nav = "browse"
        self._build_ui()

    def _build_ui(self):
        """Build the sidebar UI."""
        # Logo area - 8px grid
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", padx=SPACING['md'], pady=(SPACING['lg'], 0))

        logo_text = ctk.CTkLabel(
            logo_frame,
            text="Beatflow",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=COLORS['fg']
        )
        logo_text.pack(side="left")

        # Navigation items - 8px grid
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", pady=(SPACING['xl'], 0))

        nav_items = [
            ("browse", "Browse", True),  # Active by default
            ("clients", "Clients", False),
        ]

        for nav_id, label, is_active in nav_items:
            btn, indicator = self._create_nav_button(nav_frame, nav_id, label, is_active)
            self.nav_buttons[nav_id] = btn
            self.nav_indicators[nav_id] = indicator

        # Settings at bottom - 8px grid
        settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        settings_frame.pack(side="bottom", fill="x", pady=SPACING['md'])

        settings_btn = ctk.CTkButton(
            settings_frame,
            text="  Settings",
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            anchor="w",
            height=40,
            text_color=COLORS['fg_dim'],
            corner_radius=4
        )
        settings_btn.pack(fill="x", padx=SPACING['sm'])

    def _create_nav_button(self, parent, nav_id, label, is_active=False):
        """Create a navigation button with vertical accent indicator."""
        # Icon mapping
        icons = {
            "browse": "\U0001f4c1",  # Folder icon
            "clients": "\U0001f464",  # Person icon
        }

        icon = icons.get(nav_id, "")
        text = f"  {icon}  {label}" if icon else f"  {label}"

        # Container for indicator + button
        row = ctk.CTkFrame(parent, fg_color="transparent", height=40)
        row.pack(fill="x", pady=SPACING['xs'])
        row.pack_propagate(False)

        # Vertical accent indicator (2px wide bar on left)
        indicator = ctk.CTkFrame(
            row,
            width=2,
            fg_color=COLORS['accent'] if is_active else "transparent",
            corner_radius=1
        )
        indicator.pack(side="left", fill="y")

        # Navigation button
        btn = ctk.CTkButton(
            row,
            text=text,
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            anchor="w",
            height=40,
            corner_radius=4,
            text_color=COLORS['fg'] if is_active else COLORS['fg_secondary'],
            command=lambda nid=nav_id: self._on_nav_click(nid)
        )
        btn.pack(side="left", fill="x", expand=True, padx=(SPACING['sm'], SPACING['sm']))

        return btn, indicator

    def _on_nav_click(self, nav_id):
        """Handle navigation click."""
        if nav_id == self.active_nav:
            return

        # Reset old active button
        if self.active_nav in self.nav_buttons:
            self.nav_buttons[self.active_nav].configure(
                text_color=COLORS['fg_secondary']
            )
            self.nav_indicators[self.active_nav].configure(
                fg_color="transparent"
            )

        # Set new active button
        self.active_nav = nav_id
        if nav_id in self.nav_buttons:
            self.nav_buttons[nav_id].configure(
                text_color=COLORS['fg']
            )
            self.nav_indicators[nav_id].configure(
                fg_color=COLORS['accent']
            )

        if self.on_nav_change:
            self.on_nav_change(nav_id)
