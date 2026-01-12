"""Tasks View - Main container for Studio Flow with multi-tab layout."""

import customtkinter as ctk
from ui.theme import COLORS, SPACING
from ui.today_view import TodayView
from ui.projects_view import ProjectsView
from ui.productivity_dashboard import ProductivityDashboard
from ui.calendar_view import CalendarView


class TasksView(ctk.CTkFrame):
    """Main view for Studio Flow task management."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_main'], corner_radius=0, **kwargs)

        self.current_tab = "today"
        self._build_ui()

    def _build_ui(self):
        """Build the two-tab layout."""
        # Header with tab switcher
        header = ctk.CTkFrame(self, fg_color=COLORS['bg_dark'], height=56, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        # Title
        title_label = ctk.CTkLabel(
            header,
            text="Studio Flow",
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            text_color=COLORS['fg']
        )
        title_label.pack(side="left", padx=SPACING['lg'], pady=SPACING['sm'])

        # Tab switcher (CTkSegmentedButton)
        self.tab_switcher = ctk.CTkSegmentedButton(
            header,
            values=["Today", "Projects", "Dashboard", "Calendar"],
            command=self._on_tab_change,
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
        self.tab_switcher.set("Today")
        self.tab_switcher.pack(side="left", padx=SPACING['md'], pady=SPACING['sm'])

        # Content area
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True)

        # Create all views
        self.today_view = TodayView(self.content_frame)
        self.projects_view = ProjectsView(self.content_frame)
        self.dashboard_view = ProductivityDashboard(self.content_frame)
        self.calendar_view = CalendarView(self.content_frame)

        # Show Today view by default
        self.today_view.pack(fill="both", expand=True)

    def _on_tab_change(self, value):
        """Handle tab switch."""
        # Hide current view
        views = {
            "today": self.today_view,
            "projects": self.projects_view,
            "dashboard": self.dashboard_view,
            "calendar": self.calendar_view
        }
        views[self.current_tab].pack_forget()

        # Show new view
        tab_map = {
            "Today": "today",
            "Projects": "projects",
            "Dashboard": "dashboard",
            "Calendar": "calendar"
        }
        self.current_tab = tab_map[value]
        views[self.current_tab].pack(fill="both", expand=True)
        views[self.current_tab].refresh()

    def refresh(self):
        """Refresh current view."""
        views = {
            "today": self.today_view,
            "projects": self.projects_view,
            "dashboard": self.dashboard_view,
            "calendar": self.calendar_view
        }
        views[self.current_tab].refresh()
