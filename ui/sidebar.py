"""Sidebar navigation component for Beatflow."""

import customtkinter as ctk
from ui.theme import COLORS


class Sidebar(ctk.CTkFrame):
    """Main navigation sidebar with logo and navigation buttons."""

    def __init__(self, parent, on_nav_change=None, **kwargs):
        super().__init__(parent, width=180, corner_radius=0, fg_color=COLORS['bg_darkest'], **kwargs)
        self.grid_propagate(False)
        self.on_nav_change = on_nav_change
        self.nav_buttons = {}
        self.active_nav = "samples"
        self._build_ui()

    def _build_ui(self):
        """Build the sidebar UI."""
        # Logo area
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(20, 0))

        # FLP badge
        flp_badge = ctk.CTkLabel(
            logo_frame,
            text=" FLP ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=COLORS['accent'],
            corner_radius=4,
            text_color="#ffffff"
        )
        flp_badge.pack(side="left")

        logo_text = ctk.CTkLabel(
            logo_frame,
            text="BeatmakerOS",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['fg']
        )
        logo_text.pack(side="left", padx=(8, 0))

        # Navigation items
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", pady=(30, 0))

        nav_items = [
            ("dashboard", "Dashboard", False),
            ("clients", "Clients", False),
            ("samples", "Samples", True),  # Active by default
            ("projects", "Projects", False),
            ("roadmap", "Dev RoadMap", False),
        ]

        for nav_id, label, is_active in nav_items:
            btn = self._create_nav_button(nav_frame, nav_id, label, is_active)
            self.nav_buttons[nav_id] = btn

        # Settings at bottom
        settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        settings_frame.pack(side="bottom", fill="x", pady=16)

        settings_btn = ctk.CTkButton(
            settings_frame,
            text="  Settings",
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            anchor="w",
            height=40,
            text_color=COLORS['fg_dim'],
            corner_radius=8
        )
        settings_btn.pack(fill="x", padx=8)

    def _create_nav_button(self, parent, nav_id, label, is_active=False):
        """Create a navigation button."""
        # Icon mapping
        icons = {
            "dashboard": "",
            "clients": "",
            "samples": "",
            "projects": "",
            "roadmap": "",
        }

        icon = icons.get(nav_id, "")
        text = f"  {icon}  {label}" if icon else f"  {label}"

        btn = ctk.CTkButton(
            parent,
            text=text,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['accent'] if is_active else "transparent",
            hover_color=COLORS['accent_hover'] if is_active else COLORS['bg_hover'],
            anchor="w",
            height=40,
            corner_radius=8,
            text_color=COLORS['fg'] if is_active else COLORS['fg_secondary'],
            command=lambda nid=nav_id: self._on_nav_click(nid)
        )
        btn.pack(fill="x", padx=8, pady=2)
        return btn

    def _on_nav_click(self, nav_id):
        """Handle navigation click."""
        if nav_id == self.active_nav:
            return

        # Reset old active button
        if self.active_nav in self.nav_buttons:
            self.nav_buttons[self.active_nav].configure(
                fg_color="transparent",
                hover_color=COLORS['bg_hover'],
                text_color=COLORS['fg_secondary']
            )

        # Set new active button
        self.active_nav = nav_id
        if nav_id in self.nav_buttons:
            self.nav_buttons[nav_id].configure(
                fg_color=COLORS['accent'],
                hover_color=COLORS['accent_hover'],
                text_color=COLORS['fg']
            )

        if self.on_nav_change:
            self.on_nav_change(nav_id)
