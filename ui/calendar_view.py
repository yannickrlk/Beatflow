"""Calendar View - Multi-view calendar for task planning (Month, Week, Day)."""

import customtkinter as ctk
from ui.theme import COLORS, SPACING
from core.task_manager import get_task_manager
from datetime import datetime, timedelta
import calendar
import tkinter as tk
from typing import Optional, Tuple


class CalendarView(ctk.CTkFrame):
    """Multi-view calendar with Month, Week, and Day views."""

    # Time configuration
    START_HOUR = 6   # 6 AM
    END_HOUR = 23    # 11 PM
    HOUR_HEIGHT = 60  # Pixels per hour

    def __init__(self, parent, on_date_select=None, **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_main'], **kwargs)
        self.task_manager = get_task_manager()
        self.on_date_select = on_date_select

        # Current displayed date/period
        self.current_date = datetime.now()
        self.selected_date = datetime.now().strftime('%Y-%m-%d')
        self.current_view = "Month"  # "Month", "Week", "Day"

        # Focused cell for keyboard navigation (row, col)
        self.focused_cell: Optional[Tuple[int, int]] = None

        # Cache for cell buttons (reuse instead of recreate)
        self.day_buttons = {}
        self.tasks_cache = {}

        # Tooltip management
        self._tooltip_window: Optional[tk.Toplevel] = None
        self._tooltip_after_id: Optional[str] = None

        # Inline edit state
        self._inline_edit_entry: Optional[ctk.CTkEntry] = None
        self._inline_edit_task_id: Optional[int] = None
        self._inline_edit_row = None
        self._inline_edit_title_label = None

        self._build_ui()
        self._build_month_view_structure()
        self._create_month_grid_cells()
        self._bind_keyboard_shortcuts()
        self.refresh()

    def _build_ui(self):
        """Build the calendar UI structure."""
        # Header with navigation and view toggle
        header = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], height=50, corner_radius=8)
        header.pack(fill="x", padx=8, pady=(8, 4))
        header.pack_propagate(False)

        # Navigation buttons and label
        self.prev_btn = ctk.CTkButton(
            header, text="<", font=ctk.CTkFont(size=14, weight="bold"),
            width=32, height=32, fg_color=COLORS['bg_hover'],
            hover_color=COLORS['accent'], corner_radius=4,
            command=self._prev_period
        )
        self.prev_btn.pack(side="left", padx=8, pady=9)

        self.period_label = ctk.CTkLabel(
            header, text="", font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            text_color=COLORS['fg']
        )
        self.period_label.pack(side="left", padx=8)

        self.next_btn = ctk.CTkButton(
            header, text=">", font=ctk.CTkFont(size=14, weight="bold"),
            width=32, height=32, fg_color=COLORS['bg_hover'],
            hover_color=COLORS['accent'], corner_radius=4,
            command=self._next_period
        )
        self.next_btn.pack(side="left")

        # View toggle (Month / Week / Day)
        self.view_toggle = ctk.CTkSegmentedButton(
            header, values=["Month", "Week", "Day"],
            command=self._on_view_change,
            selected_color=COLORS['accent'],
            selected_hover_color=COLORS['accent_hover'],
            unselected_color=COLORS['bg_hover'],
            unselected_hover_color=COLORS['bg_dark'],
            font=ctk.CTkFont(family="Inter", size=11),
            corner_radius=4, height=28
        )
        self.view_toggle.set("Month")
        self.view_toggle.pack(side="left", padx=16)

        # Right side buttons
        ctk.CTkButton(
            header, text="Export", font=ctk.CTkFont(family="Inter", size=11),
            width=60, height=28, fg_color=COLORS['bg_hover'],
            hover_color=COLORS['accent'], corner_radius=4,
            command=self._export_calendar
        ).pack(side="right", padx=4, pady=11)

        ctk.CTkButton(
            header, text="+ Add", font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            width=55, height=28, fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'], corner_radius=4,
            command=self._add_task_to_selected
        ).pack(side="right", padx=4, pady=11)

        ctk.CTkButton(
            header, text="Today", font=ctk.CTkFont(family="Inter", size=11),
            width=50, height=28, fg_color=COLORS['bg_hover'],
            hover_color=COLORS['accent'], corner_radius=4,
            command=self._go_to_today
        ).pack(side="right", pady=11)

        # Main container - holds the view area and info panel
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=8, pady=4)
        self.main_container.grid_columnconfigure(0, weight=3)
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # View section (will contain month/week/day views)
        self.view_section = ctk.CTkFrame(self.main_container, fg_color=COLORS['bg_card'], corner_radius=8)
        self.view_section.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        # Info panel (right side)
        self.info_frame = ctk.CTkFrame(self.main_container, fg_color=COLORS['bg_card'], corner_radius=8)
        self.info_frame.grid(row=0, column=1, sticky="nsew")

    def _build_month_view_structure(self):
        """Build the month view UI structure."""
        # Clear existing content
        for widget in self.view_section.winfo_children():
            widget.destroy()

        # Day headers
        days_header = ctk.CTkFrame(self.view_section, fg_color=COLORS['bg_dark'], height=32)
        days_header.pack(fill="x", padx=2, pady=(2, 0))
        days_header.pack_propagate(False)

        for i, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            color = COLORS['fg_dim'] if i >= 5 else COLORS['fg_secondary']
            ctk.CTkLabel(
                days_header, text=day, font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                text_color=color
            ).pack(side="left", expand=True, pady=6)

        # Calendar grid frame
        self.calendar_frame = ctk.CTkFrame(self.view_section, fg_color="transparent")
        self.calendar_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Configure grid
        for col in range(7):
            self.calendar_frame.grid_columnconfigure(col, weight=1, uniform="day")
        for row in range(6):
            self.calendar_frame.grid_rowconfigure(row, weight=1, uniform="week")

    def _build_week_view_structure(self):
        """Build the week view UI structure."""
        # Clear existing content
        for widget in self.view_section.winfo_children():
            widget.destroy()
        self.day_buttons.clear()

        # Main week container
        week_container = ctk.CTkFrame(self.view_section, fg_color="transparent")
        week_container.pack(fill="both", expand=True, padx=2, pady=2)

        # Day headers row
        header_frame = ctk.CTkFrame(week_container, fg_color=COLORS['bg_dark'], height=50)
        header_frame.pack(fill="x", padx=0, pady=(0, 1))
        header_frame.pack_propagate(False)

        # Time column header (empty space)
        time_header = ctk.CTkFrame(header_frame, fg_color=COLORS['bg_dark'], width=60)
        time_header.pack(side="left", fill="y")
        time_header.pack_propagate(False)

        # Store day column headers for updates
        self.week_day_headers = []

        # Get the week dates
        week_start = self._get_week_start(self.current_date)
        today = datetime.now().strftime('%Y-%m-%d')

        for i in range(7):
            day_date = week_start + timedelta(days=i)
            day_str = day_date.strftime('%Y-%m-%d')
            is_weekend = i >= 5
            is_today = day_str == today

            # Day column header
            col_header = ctk.CTkFrame(
                header_frame,
                fg_color=COLORS['accent'] if is_today else COLORS['bg_dark'],
                corner_radius=0
            )
            col_header.pack(side="left", fill="both", expand=True, padx=(0, 1))

            # Day name
            day_name = day_date.strftime("%a")
            name_color = "#ffffff" if is_today else (COLORS['fg_dim'] if is_weekend else COLORS['fg_secondary'])
            ctk.CTkLabel(
                col_header, text=day_name,
                font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                text_color=name_color
            ).pack(pady=(4, 0))

            # Day number
            day_num = day_date.strftime("%d")
            num_color = "#ffffff" if is_today else COLORS['fg']
            ctk.CTkLabel(
                col_header, text=day_num,
                font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
                text_color=num_color
            ).pack(pady=(0, 4))

            self.week_day_headers.append({
                'frame': col_header, 'date': day_str,
                'is_today': is_today, 'is_weekend': is_weekend
            })

        # All-day events row
        self.all_day_frame = ctk.CTkFrame(week_container, fg_color=COLORS['bg_hover'], height=30)
        self.all_day_frame.pack(fill="x", padx=0, pady=(0, 1))
        self.all_day_frame.pack_propagate(False)

        # Time column for all-day
        all_day_label = ctk.CTkFrame(self.all_day_frame, fg_color=COLORS['bg_hover'], width=60)
        all_day_label.pack(side="left", fill="y")
        all_day_label.pack_propagate(False)
        ctk.CTkLabel(
            all_day_label, text="All Day",
            font=ctk.CTkFont(family="Inter", size=9),
            text_color=COLORS['fg_dim']
        ).pack(expand=True)

        # All-day event columns (will be populated in refresh)
        self.all_day_columns = []
        for i in range(7):
            col = ctk.CTkFrame(self.all_day_frame, fg_color="transparent")
            col.pack(side="left", fill="both", expand=True, padx=(0, 1))
            self.all_day_columns.append(col)

        # Scrollable time grid
        self.week_scroll = ctk.CTkScrollableFrame(
            week_container, fg_color="transparent",
            scrollbar_button_color=COLORS['bg_hover']
        )
        self.week_scroll.pack(fill="both", expand=True)

        # Build time slots
        self.week_time_slots = {}  # (hour, day_index) -> frame

        for hour in range(self.START_HOUR, self.END_HOUR + 1):
            hour_row = ctk.CTkFrame(self.week_scroll, fg_color="transparent", height=self.HOUR_HEIGHT)
            hour_row.pack(fill="x")
            hour_row.pack_propagate(False)

            # Time label column
            time_label_frame = ctk.CTkFrame(hour_row, fg_color=COLORS['bg_dark'], width=60)
            time_label_frame.pack(side="left", fill="y")
            time_label_frame.pack_propagate(False)

            # Format hour (12-hour format)
            hour_12 = hour % 12 or 12
            am_pm = "AM" if hour < 12 else "PM"
            ctk.CTkLabel(
                time_label_frame, text=f"{hour_12}{am_pm}",
                font=ctk.CTkFont(family="Inter", size=10),
                text_color=COLORS['fg_dim']
            ).pack(anchor="ne", padx=4, pady=2)

            # Day columns for this hour
            for day_idx in range(7):
                is_weekend = day_idx >= 5
                slot_frame = ctk.CTkFrame(
                    hour_row,
                    fg_color=COLORS['bg_dark'] if is_weekend else COLORS['bg_card'],
                    corner_radius=0
                )
                slot_frame.pack(side="left", fill="both", expand=True, padx=(0, 1))

                # Add bottom border line
                border = ctk.CTkFrame(slot_frame, fg_color=COLORS['border'], height=1)
                border.pack(side="bottom", fill="x")

                # Bind click to create event
                date_str = (week_start + timedelta(days=day_idx)).strftime('%Y-%m-%d')
                slot_frame.bind("<Button-1>", lambda e, d=date_str, h=hour: self._on_time_slot_click(d, h))

                self.week_time_slots[(hour, day_idx)] = slot_frame

        # Scroll to current time on load
        self.after(100, self._scroll_to_current_time)

    def _build_day_view_structure(self):
        """Build the day view UI structure."""
        # Clear existing content
        for widget in self.view_section.winfo_children():
            widget.destroy()
        self.day_buttons.clear()

        # Main day container
        day_container = ctk.CTkFrame(self.view_section, fg_color="transparent")
        day_container.pack(fill="both", expand=True, padx=2, pady=2)

        # Day header
        header_frame = ctk.CTkFrame(day_container, fg_color=COLORS['bg_dark'], height=50)
        header_frame.pack(fill="x", padx=0, pady=(0, 1))
        header_frame.pack_propagate(False)

        # Time column header (empty space)
        time_header = ctk.CTkFrame(header_frame, fg_color=COLORS['bg_dark'], width=60)
        time_header.pack(side="left", fill="y")
        time_header.pack_propagate(False)

        # Day info header
        today = datetime.now().strftime('%Y-%m-%d')
        is_today = self.selected_date == today

        day_header = ctk.CTkFrame(
            header_frame,
            fg_color=COLORS['accent'] if is_today else COLORS['bg_dark'],
            corner_radius=0
        )
        day_header.pack(side="left", fill="both", expand=True)

        date_obj = datetime.strptime(self.selected_date, '%Y-%m-%d')
        day_name = date_obj.strftime("%A")
        day_num = date_obj.strftime("%B %d, %Y")

        name_color = "#ffffff" if is_today else COLORS['fg_secondary']
        ctk.CTkLabel(
            day_header, text=day_name,
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=name_color
        ).pack(pady=(8, 0))

        num_color = "#ffffff" if is_today else COLORS['fg']
        ctk.CTkLabel(
            day_header, text=day_num,
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=num_color
        ).pack(pady=(0, 8))

        self.day_header_frame = day_header

        # All-day events row
        self.day_all_day_frame = ctk.CTkFrame(day_container, fg_color=COLORS['bg_hover'], height=30)
        self.day_all_day_frame.pack(fill="x", padx=0, pady=(0, 1))
        self.day_all_day_frame.pack_propagate(False)

        # Time column for all-day
        all_day_label = ctk.CTkFrame(self.day_all_day_frame, fg_color=COLORS['bg_hover'], width=60)
        all_day_label.pack(side="left", fill="y")
        all_day_label.pack_propagate(False)
        ctk.CTkLabel(
            all_day_label, text="All Day",
            font=ctk.CTkFont(family="Inter", size=9),
            text_color=COLORS['fg_dim']
        ).pack(expand=True)

        # All-day event area
        self.day_all_day_events = ctk.CTkFrame(self.day_all_day_frame, fg_color="transparent")
        self.day_all_day_events.pack(side="left", fill="both", expand=True, padx=4)

        # Scrollable time grid
        self.day_scroll = ctk.CTkScrollableFrame(
            day_container, fg_color="transparent",
            scrollbar_button_color=COLORS['bg_hover']
        )
        self.day_scroll.pack(fill="both", expand=True)

        # Build time slots
        self.day_time_slots = {}  # hour -> frame

        for hour in range(self.START_HOUR, self.END_HOUR + 1):
            hour_row = ctk.CTkFrame(self.day_scroll, fg_color="transparent", height=self.HOUR_HEIGHT)
            hour_row.pack(fill="x")
            hour_row.pack_propagate(False)

            # Time label column
            time_label_frame = ctk.CTkFrame(hour_row, fg_color=COLORS['bg_dark'], width=60)
            time_label_frame.pack(side="left", fill="y")
            time_label_frame.pack_propagate(False)

            # Format hour (12-hour format)
            hour_12 = hour % 12 or 12
            am_pm = "AM" if hour < 12 else "PM"
            ctk.CTkLabel(
                time_label_frame, text=f"{hour_12}{am_pm}",
                font=ctk.CTkFont(family="Inter", size=10),
                text_color=COLORS['fg_dim']
            ).pack(anchor="ne", padx=4, pady=2)

            # Main slot area
            slot_frame = ctk.CTkFrame(
                hour_row,
                fg_color=COLORS['bg_card'],
                corner_radius=0
            )
            slot_frame.pack(side="left", fill="both", expand=True)

            # Add bottom border line
            border = ctk.CTkFrame(slot_frame, fg_color=COLORS['border'], height=1)
            border.pack(side="bottom", fill="x")

            # Bind click to create event
            slot_frame.bind("<Button-1>", lambda e, h=hour: self._on_time_slot_click(self.selected_date, h))

            self.day_time_slots[hour] = slot_frame

        # Scroll to current time on load
        self.after(100, self._scroll_to_current_time)

        # Add current time indicator
        self._update_current_time_indicator()

    def _create_month_grid_cells(self):
        """Create all 42 day cells once (6 rows x 7 cols)."""
        for row in range(6):
            for col in range(7):
                cell_key = (row, col)
                btn = ctk.CTkButton(
                    self.calendar_frame,
                    text="",
                    font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
                    fg_color=COLORS['bg_card'],
                    hover_color=COLORS['bg_hover'],
                    corner_radius=4,
                    anchor="n",
                    compound="top",
                    command=lambda r=row, c=col: self._on_cell_click(r, c)
                )
                btn.grid(row=row, column=col, sticky="nsew", padx=1, pady=1, ipady=4)
                # Right-click binding for context menu
                btn.bind("<Button-3>", lambda e, r=row, c=col: self._on_cell_right_click(e, r, c))
                # Tooltip bindings
                btn.bind("<Enter>", lambda e, r=row, c=col: self._on_cell_enter(e, r, c))
                btn.bind("<Leave>", lambda e: self._on_cell_leave(e))
                self.day_buttons[cell_key] = btn

    def _bind_keyboard_shortcuts(self):
        """Bind keyboard shortcuts for navigation."""
        # Enable focus on the underlying tkinter frame (CTkFrame doesn't support takefocus)
        self._canvas.configure(takefocus=True)
        self.bind("<Up>", self._on_key_up)
        self.bind("<Down>", self._on_key_down)
        self.bind("<Left>", self._on_key_left)
        self.bind("<Right>", self._on_key_right)
        self.bind("<Return>", self._on_key_enter)
        self.bind("<Delete>", self._on_key_delete)
        self.bind("<Escape>", self._on_key_escape)
        self.bind("<t>", self._on_key_today)
        self.bind("<T>", self._on_key_today)
        self.bind("<FocusIn>", self._on_focus_in)

    def _on_view_change(self, value: str):
        """Handle view toggle change."""
        self.current_view = value
        self.focused_cell = None

        if value == "Month":
            self._build_month_view_structure()
            self._create_month_grid_cells()
        elif value == "Week":
            self._build_week_view_structure()
        elif value == "Day":
            self._build_day_view_structure()

        self.refresh()

    def refresh(self):
        """Refresh the calendar display based on current view."""
        self._update_period_label()

        if self.current_view == "Month":
            self._load_tasks_for_month()
            self._update_calendar_cells()
        elif self.current_view == "Week":
            self._load_tasks_for_week()
            self._update_week_view()
        elif self.current_view == "Day":
            self._load_tasks_for_day()
            self._update_day_view()

        self._update_date_info()

    def _update_period_label(self):
        """Update the period label based on current view."""
        if self.current_view == "Month":
            self.period_label.configure(text=self.current_date.strftime("%B %Y"))
        elif self.current_view == "Week":
            week_start = self._get_week_start(self.current_date)
            week_end = week_start + timedelta(days=6)
            if week_start.month == week_end.month:
                self.period_label.configure(
                    text=f"{week_start.strftime('%b %d')} - {week_end.strftime('%d, %Y')}"
                )
            else:
                self.period_label.configure(
                    text=f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}"
                )
        elif self.current_view == "Day":
            date_obj = datetime.strptime(self.selected_date, '%Y-%m-%d')
            self.period_label.configure(text=date_obj.strftime("%B %d, %Y"))

    def _get_week_start(self, date: datetime) -> datetime:
        """Get the Monday of the week containing the given date."""
        return date - timedelta(days=date.weekday())

    def _load_tasks_for_month(self):
        """Load all tasks for the month in a single query."""
        year = self.current_date.year
        month = self.current_date.month
        self.tasks_cache = self.task_manager.get_tasks_for_month(year, month)

    def _load_tasks_for_week(self):
        """Load all tasks for the current week."""
        week_start = self._get_week_start(self.current_date)

        # Load tasks for the week (may span months)
        self.tasks_cache = {}
        for i in range(7):
            day_date = week_start + timedelta(days=i)
            day_str = day_date.strftime('%Y-%m-%d')
            tasks = self.task_manager.get_daily_tasks(date=day_str)
            if tasks:
                self.tasks_cache[day_str] = tasks

    def _load_tasks_for_day(self):
        """Load all tasks for the selected day."""
        tasks = self.task_manager.get_daily_tasks(date=self.selected_date)
        self.tasks_cache = {self.selected_date: tasks} if tasks else {}

    def _update_calendar_cells(self):
        """Update all calendar cells with current month data."""
        year = self.current_date.year
        month = self.current_date.month
        cal = calendar.Calendar(firstweekday=0)
        today = datetime.now().strftime('%Y-%m-%d')

        weeks = list(cal.monthdayscalendar(year, month))

        for row in range(6):
            for col in range(7):
                btn = self.day_buttons[(row, col)]
                is_weekend = col >= 5
                is_focused = self.focused_cell == (row, col)

                if row < len(weeks) and weeks[row][col] != 0:
                    day = weeks[row][col]
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    tasks = self.tasks_cache.get(date_str, [])
                    has_tasks = len(tasks) > 0
                    is_today = date_str == today
                    is_selected = date_str == self.selected_date

                    # Build display text
                    text = str(day)
                    if has_tasks:
                        if len(tasks) <= 3:
                            dots_line = ""
                            for t in tasks:
                                dots_line += "@ " if t.get('completed') else "o "
                            text = f"{day}\n{dots_line.strip()}"
                        else:
                            completed = sum(1 for t in tasks if t.get('completed'))
                            text = f"{day}\n{completed}/{len(tasks)}"

                    # Set colors based on state priority
                    if is_focused and not is_selected:
                        fg_color = COLORS['bg_hover']
                        text_color = COLORS['accent']
                        hover = COLORS['accent_hover']
                        border_width = 2
                        border_color = COLORS['accent']
                    elif is_selected:
                        fg_color = COLORS['accent']
                        text_color = "#ffffff"
                        hover = COLORS['accent_hover']
                        border_width = 2 if is_focused else 0
                        border_color = "#ffffff" if is_focused else COLORS['accent']
                    elif is_today:
                        fg_color = COLORS['bg_hover']
                        text_color = COLORS['accent']
                        hover = COLORS['bg_hover']
                        border_width = 2
                        border_color = COLORS['accent']
                    elif is_weekend:
                        fg_color = COLORS['bg_dark']
                        text_color = COLORS['fg_dim']
                        hover = COLORS['bg_hover']
                        border_width = 0
                        border_color = COLORS['border']
                    else:
                        fg_color = COLORS['bg_card']
                        text_color = COLORS['fg'] if has_tasks else COLORS['fg_secondary']
                        hover = COLORS['bg_hover']
                        border_width = 0
                        border_color = COLORS['border']

                    btn.configure(
                        text=text,
                        fg_color=fg_color,
                        text_color=text_color,
                        hover_color=hover,
                        border_width=border_width,
                        border_color=border_color,
                        state="normal"
                    )
                    btn._date_str = date_str
                    btn._tasks = tasks
                else:
                    btn.configure(
                        text="",
                        fg_color=COLORS['bg_dark'] if is_weekend else COLORS['bg_card'],
                        hover_color=COLORS['bg_dark'],
                        border_width=0,
                        state="disabled"
                    )
                    btn._date_str = None
                    btn._tasks = []

    def _update_week_view(self):
        """Update the week view with current data."""
        if not hasattr(self, 'week_time_slots'):
            return

        week_start = self._get_week_start(self.current_date)
        today = datetime.now().strftime('%Y-%m-%d')

        # Update day headers
        for i, header_info in enumerate(self.week_day_headers):
            day_date = week_start + timedelta(days=i)
            day_str = day_date.strftime('%Y-%m-%d')
            is_today = day_str == today

            header_info['date'] = day_str
            header_info['is_today'] = is_today
            header_info['frame'].configure(
                fg_color=COLORS['accent'] if is_today else COLORS['bg_dark']
            )

        # Clear all-day columns
        for col in self.all_day_columns:
            for widget in col.winfo_children():
                widget.destroy()

        # Clear time slots (except border frames)
        for slot in self.week_time_slots.values():
            for widget in slot.winfo_children():
                if not isinstance(widget, ctk.CTkFrame) or widget.cget("height") != 1:
                    widget.destroy()

        # Add events
        for day_idx in range(7):
            day_date = week_start + timedelta(days=day_idx)
            day_str = day_date.strftime('%Y-%m-%d')
            tasks = self.tasks_cache.get(day_str, [])

            all_day_tasks = []
            timed_tasks = []

            for task in tasks:
                if task.get('all_day', True) or not task.get('start_time'):
                    all_day_tasks.append(task)
                else:
                    timed_tasks.append(task)

            # Add all-day events
            for task in all_day_tasks[:2]:  # Show max 2
                self._create_all_day_event(self.all_day_columns[day_idx], task)

            if len(all_day_tasks) > 2:
                ctk.CTkLabel(
                    self.all_day_columns[day_idx],
                    text=f"+{len(all_day_tasks) - 2} more",
                    font=ctk.CTkFont(family="Inter", size=9),
                    text_color=COLORS['fg_dim']
                ).pack(anchor="w")

            # Add timed events
            for task in timed_tasks:
                self._create_timed_event_week(task, day_idx)

        # Update time indicator
        self._update_current_time_indicator()

    def _update_day_view(self):
        """Update the day view with current data."""
        if not hasattr(self, 'day_time_slots'):
            return

        today = datetime.now().strftime('%Y-%m-%d')
        is_today = self.selected_date == today

        # Update header
        if hasattr(self, 'day_header_frame'):
            self.day_header_frame.configure(
                fg_color=COLORS['accent'] if is_today else COLORS['bg_dark']
            )

        # Clear all-day events area
        for widget in self.day_all_day_events.winfo_children():
            widget.destroy()

        # Clear time slots (except border frames)
        for slot in self.day_time_slots.values():
            for widget in slot.winfo_children():
                if not isinstance(widget, ctk.CTkFrame) or widget.cget("height") != 1:
                    widget.destroy()

        # Get tasks
        tasks = self.tasks_cache.get(self.selected_date, [])
        all_day_tasks = []
        timed_tasks = []

        for task in tasks:
            if task.get('all_day', True) or not task.get('start_time'):
                all_day_tasks.append(task)
            else:
                timed_tasks.append(task)

        # Add all-day events
        for task in all_day_tasks:
            self._create_all_day_event_day(task)

        # Add timed events
        for task in timed_tasks:
            self._create_timed_event_day(task)

        # Update time indicator
        self._update_current_time_indicator()

    def _create_all_day_event(self, parent, task: dict):
        """Create an all-day event badge for week view."""
        done = task.get('completed', False)
        bg_color = COLORS['bg_dark'] if done else COLORS['accent']

        event_frame = ctk.CTkFrame(parent, fg_color=bg_color, height=18, corner_radius=2)
        event_frame.pack(fill="x", pady=1)
        event_frame.pack_propagate(False)

        title = task['title'][:10] + ('...' if len(task['title']) > 10 else '')
        ctk.CTkLabel(
            event_frame, text=title,
            font=ctk.CTkFont(family="Inter", size=9),
            text_color="#ffffff" if not done else COLORS['fg_dim']
        ).pack(side="left", padx=2)

    def _create_all_day_event_day(self, task: dict):
        """Create an all-day event for day view."""
        done = task.get('completed', False)
        bg_color = COLORS['bg_dark'] if done else COLORS['accent']

        event_frame = ctk.CTkFrame(self.day_all_day_events, fg_color=bg_color, height=22, corner_radius=4)
        event_frame.pack(fill="x", pady=2)
        event_frame.pack_propagate(False)

        check = "* " if done else ""
        ctk.CTkLabel(
            event_frame, text=f"{check}{task['title']}",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color="#ffffff" if not done else COLORS['fg_dim']
        ).pack(side="left", padx=6)

        if task.get('context'):
            ctk.CTkLabel(
                event_frame, text=task['context'].replace('@', ''),
                font=ctk.CTkFont(family="Inter", size=9),
                text_color="#ffffff80"
            ).pack(side="right", padx=6)

    def _create_timed_event_week(self, task: dict, day_idx: int):
        """Create a timed event block for week view."""
        start_time = task.get('start_time', '')
        end_time = task.get('end_time', '')

        try:
            start_hour, start_min = map(int, start_time.split(':'))
        except (ValueError, AttributeError):
            start_hour, start_min = 9, 0

        try:
            end_hour, end_min = map(int, end_time.split(':'))
        except (ValueError, AttributeError):
            end_hour, end_min = start_hour + 1, 0

        # Calculate position and height
        if start_hour < self.START_HOUR:
            start_hour = self.START_HOUR
            start_min = 0
        if end_hour > self.END_HOUR:
            end_hour = self.END_HOUR
            end_min = 0

        start_offset = start_min * (self.HOUR_HEIGHT / 60)
        duration_mins = (end_hour - start_hour) * 60 + (end_min - start_min)
        height = max(20, duration_mins * (self.HOUR_HEIGHT / 60))

        # Get the slot for the start hour
        slot_key = (start_hour, day_idx)
        if slot_key not in self.week_time_slots:
            return

        slot = self.week_time_slots[slot_key]

        done = task.get('completed', False)
        bg_color = COLORS['bg_dark'] if done else COLORS['accent_secondary']

        event_frame = ctk.CTkFrame(
            slot, fg_color=bg_color,
            corner_radius=4
        )
        event_frame.place(x=2, y=start_offset, relwidth=0.95, height=height - 2)

        title = task['title'][:12] + ('...' if len(task['title']) > 12 else '')
        ctk.CTkLabel(
            event_frame, text=title,
            font=ctk.CTkFont(family="Inter", size=9),
            text_color="#ffffff",
            anchor="nw"
        ).pack(anchor="nw", padx=4, pady=2)

        if height > 30:
            ctk.CTkLabel(
                event_frame, text=f"{start_time}",
                font=ctk.CTkFont(family="JetBrains Mono", size=8),
                text_color="#ffffff80"
            ).pack(anchor="nw", padx=4)

    def _create_timed_event_day(self, task: dict):
        """Create a timed event block for day view."""
        start_time = task.get('start_time', '')
        end_time = task.get('end_time', '')

        try:
            start_hour, start_min = map(int, start_time.split(':'))
        except (ValueError, AttributeError):
            start_hour, start_min = 9, 0

        try:
            end_hour, end_min = map(int, end_time.split(':'))
        except (ValueError, AttributeError):
            end_hour, end_min = start_hour + 1, 0

        # Calculate position and height
        if start_hour < self.START_HOUR:
            start_hour = self.START_HOUR
            start_min = 0
        if end_hour > self.END_HOUR:
            end_hour = self.END_HOUR
            end_min = 0

        start_offset = start_min * (self.HOUR_HEIGHT / 60)
        duration_mins = (end_hour - start_hour) * 60 + (end_min - start_min)
        height = max(30, duration_mins * (self.HOUR_HEIGHT / 60))

        # Get the slot for the start hour
        if start_hour not in self.day_time_slots:
            return

        slot = self.day_time_slots[start_hour]

        done = task.get('completed', False)
        bg_color = COLORS['bg_dark'] if done else COLORS['accent_secondary']

        event_frame = ctk.CTkFrame(
            slot, fg_color=bg_color,
            corner_radius=4
        )
        event_frame.place(x=4, y=start_offset, relwidth=0.98, height=height - 4)

        # Event content
        content = ctk.CTkFrame(event_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=8, pady=4)

        check = "* " if done else ""
        ctk.CTkLabel(
            content, text=f"{check}{task['title']}",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color="#ffffff" if not done else COLORS['fg_dim'],
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            content, text=f"{start_time} - {end_time}",
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            text_color="#ffffff80",
            anchor="w"
        ).pack(anchor="w", pady=(2, 0))

        if height > 60 and task.get('context'):
            ctk.CTkLabel(
                content, text=task['context'],
                font=ctk.CTkFont(family="Inter", size=10),
                text_color="#ffffff60"
            ).pack(anchor="w", pady=(4, 0))

    def _update_current_time_indicator(self):
        """Add/update current time indicator (red line)."""
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')

        if self.current_view == "Week":
            week_start = self._get_week_start(self.current_date)
            for day_idx in range(7):
                day_str = (week_start + timedelta(days=day_idx)).strftime('%Y-%m-%d')
                if day_str == today:
                    current_hour = now.hour
                    if self.START_HOUR <= current_hour <= self.END_HOUR:
                        slot_key = (current_hour, day_idx)
                        if slot_key in self.week_time_slots:
                            slot = self.week_time_slots[slot_key]
                            minute_offset = now.minute * (self.HOUR_HEIGHT / 60)
                            # Remove old indicator if exists
                            for widget in slot.winfo_children():
                                if hasattr(widget, '_is_time_indicator'):
                                    widget.destroy()
                            # Add new indicator
                            indicator = ctk.CTkFrame(
                                slot, fg_color="#EF4444", height=2
                            )
                            indicator._is_time_indicator = True
                            indicator.place(x=0, y=minute_offset, relwidth=1)

        elif self.current_view == "Day" and self.selected_date == today:
            current_hour = now.hour
            if self.START_HOUR <= current_hour <= self.END_HOUR:
                if current_hour in self.day_time_slots:
                    slot = self.day_time_slots[current_hour]
                    minute_offset = now.minute * (self.HOUR_HEIGHT / 60)
                    # Remove old indicator if exists
                    for widget in slot.winfo_children():
                        if hasattr(widget, '_is_time_indicator'):
                            widget.destroy()
                    # Add new indicator
                    indicator = ctk.CTkFrame(
                        slot, fg_color="#EF4444", height=2
                    )
                    indicator._is_time_indicator = True
                    indicator.place(x=0, y=minute_offset, relwidth=1)

    def _scroll_to_current_time(self):
        """Scroll to show current time in week/day view."""
        now = datetime.now()
        current_hour = now.hour

        if current_hour < self.START_HOUR:
            target_hour = self.START_HOUR
        elif current_hour > self.END_HOUR:
            target_hour = self.END_HOUR - 4
        else:
            target_hour = max(self.START_HOUR, current_hour - 2)

        total_hours = self.END_HOUR - self.START_HOUR + 1
        scroll_pos = (target_hour - self.START_HOUR) / total_hours

        if self.current_view == "Week" and hasattr(self, 'week_scroll'):
            try:
                self.week_scroll._parent_canvas.yview_moveto(scroll_pos)
            except Exception:
                pass
        elif self.current_view == "Day" and hasattr(self, 'day_scroll'):
            try:
                self.day_scroll._parent_canvas.yview_moveto(scroll_pos)
            except Exception:
                pass

    def _on_time_slot_click(self, date_str: str, hour: int):
        """Handle click on a time slot to create event."""
        self.selected_date = date_str
        self._update_date_info()

        time_str = f"{hour:02d}:00"

        dialog = AddTaskDialog(
            self, self.task_manager, date_str,
            on_save=self.refresh, allow_date_edit=False,
            default_time=time_str
        )
        dialog.focus()

    # ===== KEYBOARD NAVIGATION =====

    def _on_focus_in(self, event):
        """Handle focus in - initialize focused cell if needed."""
        if self.current_view == "Month" and self.focused_cell is None:
            self._focus_selected_date()

    def _focus_selected_date(self):
        """Set focus to the cell containing the selected date."""
        if self.current_view != "Month":
            return

        year = self.current_date.year
        month = self.current_date.month
        cal = calendar.Calendar(firstweekday=0)
        weeks = list(cal.monthdayscalendar(year, month))

        try:
            selected_day = int(self.selected_date.split('-')[2])
            selected_month = int(self.selected_date.split('-')[1])
            selected_year = int(self.selected_date.split('-')[0])

            if selected_year == year and selected_month == month:
                for row_idx, week in enumerate(weeks):
                    for col_idx, day in enumerate(week):
                        if day == selected_day:
                            self.focused_cell = (row_idx, col_idx)
                            self._update_calendar_cells()
                            return
        except (ValueError, IndexError):
            pass

        for row_idx, week in enumerate(weeks):
            for col_idx, day in enumerate(week):
                if day != 0:
                    self.focused_cell = (row_idx, col_idx)
                    self._update_calendar_cells()
                    return

    def _get_cell_date(self, row: int, col: int) -> Optional[str]:
        """Get the date string for a cell position."""
        btn = self.day_buttons.get((row, col))
        if btn:
            return getattr(btn, '_date_str', None)
        return None

    def _on_key_up(self, event):
        """Move focus up one week."""
        if self.current_view != "Month":
            return "break"
        if self.focused_cell is None:
            self._focus_selected_date()
            return "break"

        row, col = self.focused_cell
        new_row = row - 1

        if new_row < 0:
            self._prev_period()
            year = self.current_date.year
            month = self.current_date.month
            cal = calendar.Calendar(firstweekday=0)
            weeks = list(cal.monthdayscalendar(year, month))

            for r in range(len(weeks) - 1, -1, -1):
                if weeks[r][col] != 0:
                    self.focused_cell = (r, col)
                    break
        else:
            if self._get_cell_date(new_row, col):
                self.focused_cell = (new_row, col)

        self._update_calendar_cells()
        return "break"

    def _on_key_down(self, event):
        """Move focus down one week."""
        if self.current_view != "Month":
            return "break"
        if self.focused_cell is None:
            self._focus_selected_date()
            return "break"

        row, col = self.focused_cell
        new_row = row + 1

        year = self.current_date.year
        month = self.current_date.month
        cal = calendar.Calendar(firstweekday=0)
        weeks = list(cal.monthdayscalendar(year, month))

        if new_row >= len(weeks) or weeks[new_row][col] == 0:
            self._next_period()
            year = self.current_date.year
            month = self.current_date.month
            weeks = list(cal.monthdayscalendar(year, month))

            for r in range(len(weeks)):
                if weeks[r][col] != 0:
                    self.focused_cell = (r, col)
                    break
        else:
            self.focused_cell = (new_row, col)

        self._update_calendar_cells()
        return "break"

    def _on_key_left(self, event):
        """Move focus left one day."""
        if self.current_view != "Month":
            return "break"
        if self.focused_cell is None:
            self._focus_selected_date()
            return "break"

        row, col = self.focused_cell
        new_col = col - 1
        new_row = row

        if new_col < 0:
            new_col = 6
            new_row = row - 1

        if new_row < 0:
            self._prev_period()
            year = self.current_date.year
            month = self.current_date.month
            cal = calendar.Calendar(firstweekday=0)
            weeks = list(cal.monthdayscalendar(year, month))

            for r in range(len(weeks) - 1, -1, -1):
                for c in range(6, -1, -1):
                    if weeks[r][c] != 0:
                        self.focused_cell = (r, c)
                        self._update_calendar_cells()
                        return "break"
        else:
            if self._get_cell_date(new_row, new_col):
                self.focused_cell = (new_row, new_col)

        self._update_calendar_cells()
        return "break"

    def _on_key_right(self, event):
        """Move focus right one day."""
        if self.current_view != "Month":
            return "break"
        if self.focused_cell is None:
            self._focus_selected_date()
            return "break"

        row, col = self.focused_cell
        new_col = col + 1
        new_row = row

        if new_col > 6:
            new_col = 0
            new_row = row + 1

        year = self.current_date.year
        month = self.current_date.month
        cal = calendar.Calendar(firstweekday=0)
        weeks = list(cal.monthdayscalendar(year, month))

        if new_row >= len(weeks) or not self._get_cell_date(new_row, new_col):
            self._next_period()
            year = self.current_date.year
            month = self.current_date.month
            weeks = list(cal.monthdayscalendar(year, month))

            for r in range(len(weeks)):
                for c in range(7):
                    if weeks[r][c] != 0:
                        self.focused_cell = (r, c)
                        self._update_calendar_cells()
                        return "break"
        else:
            self.focused_cell = (new_row, new_col)

        self._update_calendar_cells()
        return "break"

    def _on_key_enter(self, event):
        """Open add task dialog for focused/selected day."""
        if self.focused_cell:
            date_str = self._get_cell_date(*self.focused_cell)
            if date_str:
                self.selected_date = date_str
                self._update_calendar_cells()
                self._update_date_info()
                self._open_add_task_dialog(date_str)
        else:
            self._open_add_task_dialog(self.selected_date)
        return "break"

    def _on_key_delete(self, event):
        """Delete the first incomplete task on focused day (if any)."""
        date_str = self.selected_date
        if self.focused_cell:
            cell_date = self._get_cell_date(*self.focused_cell)
            if cell_date:
                date_str = cell_date

        tasks = self.tasks_cache.get(date_str, [])
        for task in tasks:
            if not task.get('completed'):
                self._confirm_delete_task(task)
                return "break"

        if tasks:
            self._confirm_delete_task(tasks[0])
        return "break"

    def _confirm_delete_task(self, task: dict):
        """Show confirmation and delete a task."""
        from tkinter import messagebox
        result = messagebox.askyesno(
            "Delete Task",
            f"Delete task '{task['title']}'?",
            parent=self
        )
        if result:
            self.task_manager.delete_daily_task(task['id'])
            self.refresh()

    def _on_key_escape(self, event):
        """Deselect focused cell / cancel inline edit."""
        if self._inline_edit_entry:
            self._cancel_inline_edit()
            return "break"

        self.focused_cell = None
        self._update_calendar_cells()
        return "break"

    def _on_key_today(self, event):
        """Jump to today."""
        self._go_to_today()
        if self.current_view == "Month":
            self._focus_selected_date()
        return "break"

    # ===== TOOLTIP FUNCTIONALITY =====

    def _on_cell_enter(self, event, row: int, col: int):
        """Handle mouse entering a day cell - schedule tooltip."""
        date_str = self._get_cell_date(row, col)
        if not date_str:
            return

        if self._tooltip_after_id:
            self.after_cancel(self._tooltip_after_id)

        self._tooltip_after_id = self.after(500, lambda: self._show_tooltip(event, date_str))

    def _on_cell_leave(self, event):
        """Handle mouse leaving a day cell - hide tooltip."""
        if self._tooltip_after_id:
            self.after_cancel(self._tooltip_after_id)
            self._tooltip_after_id = None

        self._hide_tooltip()

    def _show_tooltip(self, event, date_str: str):
        """Show tooltip with task preview for a date."""
        tasks = self.tasks_cache.get(date_str, [])
        if not tasks:
            return

        self._hide_tooltip()

        self._tooltip_window = tk.Toplevel(self)
        self._tooltip_window.wm_overrideredirect(True)
        self._tooltip_window.configure(bg=COLORS['bg_card'])

        frame = tk.Frame(
            self._tooltip_window,
            bg=COLORS['bg_card'],
            highlightbackground=COLORS['border'],
            highlightthickness=1
        )
        frame.pack(fill="both", expand=True)

        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        header = tk.Label(
            frame,
            text=date_obj.strftime("%b %d"),
            font=("Inter", 10, "bold"),
            bg=COLORS['bg_dark'],
            fg=COLORS['fg'],
            pady=4,
            padx=8
        )
        header.pack(fill="x")

        max_display = 5
        for i, task in enumerate(tasks[:max_display]):
            done = task.get('completed', False)
            check = "[x]" if done else "[ ]"
            title = task['title'][:30] + ('...' if len(task['title']) > 30 else '')

            task_label = tk.Label(
                frame,
                text=f"{check} {title}",
                font=("Inter", 9),
                bg=COLORS['bg_card'],
                fg=COLORS['fg_dim'] if done else COLORS['fg'],
                anchor="w",
                padx=8,
                pady=2
            )
            task_label.pack(fill="x")

        if len(tasks) > max_display:
            overflow = tk.Label(
                frame,
                text=f"+{len(tasks) - max_display} more",
                font=("Inter", 9, "italic"),
                bg=COLORS['bg_card'],
                fg=COLORS['fg_secondary'],
                padx=8,
                pady=2
            )
            overflow.pack(fill="x")

        x = event.x_root
        y = event.y_root + 20

        self._tooltip_window.update_idletasks()
        width = self._tooltip_window.winfo_reqwidth()
        height = self._tooltip_window.winfo_reqheight()
        screen_width = self._tooltip_window.winfo_screenwidth()
        screen_height = self._tooltip_window.winfo_screenheight()

        if x + width > screen_width:
            x = screen_width - width - 10
        if y + height > screen_height:
            y = event.y_root - height - 10

        self._tooltip_window.wm_geometry(f"+{x}+{y}")

    def _hide_tooltip(self):
        """Hide the tooltip window."""
        if self._tooltip_window:
            self._tooltip_window.destroy()
            self._tooltip_window = None

    # ===== CELL CLICK HANDLERS =====

    def _on_cell_click(self, row: int, col: int):
        """Handle cell click."""
        btn = self.day_buttons[(row, col)]
        date_str = getattr(btn, '_date_str', None)
        if date_str:
            self.selected_date = date_str
            self.focused_cell = (row, col)
            self._update_calendar_cells()
            self._update_date_info()
            if self.on_date_select:
                self.on_date_select(date_str)
            self.focus_set()

    def _on_cell_right_click(self, event, row: int, col: int):
        """Handle right-click on a cell - show context menu."""
        btn = self.day_buttons[(row, col)]
        date_str = getattr(btn, '_date_str', None)
        if not date_str:
            return

        menu = tk.Menu(self, tearoff=0, bg=COLORS['bg_card'], fg=COLORS['fg'],
                      activebackground=COLORS['accent'], activeforeground="#ffffff",
                      font=("Inter", 10))
        menu.add_command(label="+ Add Task/Event", command=lambda: self._open_add_task_dialog(date_str))
        menu.add_separator()
        menu.add_command(label="View Day", command=lambda: self._switch_to_day_view(date_str))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _switch_to_day_view(self, date_str: str):
        """Switch to day view for a specific date."""
        self.selected_date = date_str
        self.current_date = datetime.strptime(date_str, '%Y-%m-%d')
        self.view_toggle.set("Day")
        self._on_view_change("Day")

    def _open_add_task_dialog(self, date_str: str):
        """Open dialog to add a new task/event."""
        dialog = AddTaskDialog(self, self.task_manager, date_str, on_save=self.refresh)
        dialog.focus()

    def _add_task_to_selected(self):
        """Add a task to the currently selected date (with date picker)."""
        dialog = AddTaskDialog(self, self.task_manager, self.selected_date,
                              on_save=self.refresh, allow_date_edit=True)
        dialog.focus()

    # ===== INFO PANEL =====

    def _update_date_info(self):
        """Update the selected date info panel."""
        for widget in self.info_frame.winfo_children():
            widget.destroy()

        date_obj = datetime.strptime(self.selected_date, '%Y-%m-%d')
        is_today = date_obj.date() == datetime.now().date()

        header = ctk.CTkFrame(self.info_frame, fg_color=COLORS['bg_darkest'], height=68)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text=date_obj.strftime("%A").upper(),
            font=ctk.CTkFont(family="Inter", size=10, weight="bold"),
            text_color=COLORS['fg_secondary']
        ).pack(anchor="w", padx=16, pady=(10, 0))

        date_row = ctk.CTkFrame(header, fg_color="transparent")
        date_row.pack(fill="x", padx=16, pady=(2, 0))

        ctk.CTkLabel(
            date_row, text=date_obj.strftime("%b %d, %Y"),
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            text_color=COLORS['fg']
        ).pack(side="left")

        if is_today:
            ctk.CTkLabel(
                date_row, text="TODAY",
                font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                text_color="#ffffff",
                fg_color=COLORS['accent'],
                corner_radius=4,
                padx=6,
                pady=3
            ).pack(side="left", padx=8)

        tasks = self.tasks_cache.get(self.selected_date, [])

        count_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent", height=36)
        count_frame.pack(fill="x", padx=16, pady=8)
        count_frame.pack_propagate(False)

        if tasks:
            completed = sum(1 for t in tasks if t.get('completed'))
            task_word = "task" if len(tasks) == 1 else "tasks"
            ctk.CTkLabel(
                count_frame, text=f"{len(tasks)} {task_word}",
                font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
                text_color=COLORS['fg']
            ).pack(side="left")

            all_done = completed == len(tasks)
            badge_color = COLORS['success'] if all_done else COLORS['accent']
            badge_text = "Complete" if all_done else f"{completed}/{len(tasks)}"

            ctk.CTkLabel(
                count_frame, text=badge_text,
                font=ctk.CTkFont(family="JetBrains Mono", size=11, weight="bold"),
                text_color="#ffffff",
                fg_color=badge_color,
                corner_radius=4,
                padx=8,
                pady=4
            ).pack(side="right")
        else:
            ctk.CTkLabel(
                count_frame, text="No tasks scheduled",
                font=ctk.CTkFont(family="Inter", size=13),
                text_color=COLORS['fg_dim']
            ).pack(side="left")

        ctk.CTkFrame(self.info_frame, fg_color=COLORS['border'], height=1).pack(fill="x", padx=16, pady=(0, 8))

        task_list = ctk.CTkScrollableFrame(
            self.info_frame, fg_color="transparent",
            scrollbar_button_color=COLORS['bg_hover']
        )
        task_list.pack(fill="both", expand=True, padx=4, pady=4)

        if tasks:
            for task in tasks:
                self._create_task_row(task_list, task)
        else:
            empty = ctk.CTkFrame(task_list, fg_color="transparent")
            empty.pack(expand=True, pady=40)

            ctk.CTkLabel(
                empty, text="No tasks scheduled",
                font=ctk.CTkFont(family="Inter", size=13),
                text_color=COLORS['fg_secondary']
            ).pack()

            ctk.CTkLabel(
                empty, text="Press Enter or right-click to add",
                font=ctk.CTkFont(family="Inter", size=11),
                text_color=COLORS['fg_dim']
            ).pack(pady=(4, 0))

    def _create_task_row(self, parent, task: dict):
        """Create a compact task row with enhanced interactions."""
        done = task.get('completed', False)
        task_id = task.get('id')

        row = ctk.CTkFrame(parent, fg_color=COLORS['bg_dark'] if done else COLORS['bg_hover'],
                          corner_radius=4, height=40)
        row.pack(fill="x", pady=2, padx=4)
        row.pack_propagate(False)

        row._task = task
        row._task_id = task_id

        check = "@" if done else "o"
        color = COLORS['success'] if done else COLORS['fg_dim']
        check_label = ctk.CTkLabel(row, text=check, font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=color, width=24, cursor="hand2")
        check_label.pack(side="left", padx=(8, 4))
        check_label.bind("<Button-1>", lambda e, tid=task_id: self._toggle_task(tid))

        if not task.get('all_day', True) and task.get('start_time'):
            time_str = task['start_time']
            ctk.CTkLabel(
                row, text=time_str,
                font=ctk.CTkFont(family="JetBrains Mono", size=10),
                text_color=COLORS['fg_secondary'],
                width=50
            ).pack(side="left", padx=(0, 4))

        title = task['title'][:22] + ('...' if len(task['title']) > 22 else '')
        title_label = ctk.CTkLabel(
            row, text=title,
            font=ctk.CTkFont(family="Inter", size=12, overstrike=done),
            text_color=COLORS['fg_dim'] if done else COLORS['fg'],
            anchor="w", cursor="hand2"
        )
        title_label.pack(side="left", fill="x", expand=True, padx=(0, 4))
        title_label.bind("<Double-Button-1>", lambda e, t=task, r=row, lbl=title_label: self._start_inline_edit(t, r, lbl))

        row._title_label = title_label

        if task.get('context'):
            ctx_colors = {
                "@Studio": "#9B59B6",
                "@Mixing": "#3498DB",
                "@Marketing": "#E74C3C",
                "@Admin": "#95A5A6",
                "@Other": "#7F8C8D"
            }
            ctx = task['context']
            ctx_color = ctx_colors.get(ctx, "#7F8C8D")

            ctk.CTkLabel(
                row, text=ctx.replace('@', ''),
                font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                text_color=ctx_color,
                fg_color=COLORS['bg_card'],
                corner_radius=3,
                padx=6,
                pady=2
            ).pack(side="right", padx=(4, 4))

        delete_btn = ctk.CTkButton(
            row, text="x", font=ctk.CTkFont(size=10),
            width=20, height=20, corner_radius=2,
            fg_color="transparent", hover_color=COLORS['error'],
            text_color=COLORS['fg_dim'],
            command=lambda t=task: self._confirm_delete_task(t)
        )
        delete_btn.pack(side="right", padx=(0, 4))
        delete_btn.pack_forget()

        row._delete_btn = delete_btn

        row.bind("<Enter>", lambda e, r=row: self._on_task_row_enter(r))
        row.bind("<Leave>", lambda e, r=row: self._on_task_row_leave(r))
        for child in row.winfo_children():
            child.bind("<Enter>", lambda e, r=row: self._on_task_row_enter(r))
            child.bind("<Leave>", lambda e, r=row: self._on_task_row_leave(r))

    def _on_task_row_enter(self, row):
        """Show delete button on task row hover."""
        if hasattr(row, '_delete_btn'):
            row._delete_btn.pack(side="right", padx=(0, 4))
        if hasattr(row, '_task'):
            done = row._task.get('completed', False)
            row.configure(fg_color=COLORS['bg_card'] if not done else COLORS['bg_hover'])

    def _on_task_row_leave(self, row):
        """Hide delete button when leaving task row."""
        if hasattr(row, '_delete_btn'):
            try:
                x, y = row.winfo_pointerxy()
                widget_under = row.winfo_containing(x, y)
                if widget_under:
                    parent = widget_under
                    while parent:
                        if parent == row:
                            return
                        parent = parent.master
            except tk.TclError:
                pass
            row._delete_btn.pack_forget()
        if hasattr(row, '_task'):
            done = row._task.get('completed', False)
            row.configure(fg_color=COLORS['bg_dark'] if done else COLORS['bg_hover'])

    def _toggle_task(self, task_id: int):
        """Toggle task completion status."""
        self.task_manager.toggle_daily_task(task_id)
        self.refresh()

    # ===== INLINE EDITING =====

    def _start_inline_edit(self, task: dict, row, title_label):
        """Start inline editing of a task title."""
        if self._inline_edit_entry:
            self._cancel_inline_edit()

        self._inline_edit_task_id = task['id']

        title_label.pack_forget()

        self._inline_edit_entry = ctk.CTkEntry(
            row,
            font=ctk.CTkFont(family="Inter", size=11),
            fg_color=COLORS['bg_input'],
            border_color=COLORS['accent'],
            height=24,
            width=150
        )
        self._inline_edit_entry.insert(0, task['title'])
        self._inline_edit_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._inline_edit_entry.focus_set()
        self._inline_edit_entry.select_range(0, 'end')

        self._inline_edit_entry.bind("<Return>", lambda e: self._save_inline_edit())
        self._inline_edit_entry.bind("<Escape>", lambda e: self._cancel_inline_edit())
        self._inline_edit_entry.bind("<FocusOut>", lambda e: self._save_inline_edit())

        self._inline_edit_row = row
        self._inline_edit_title_label = title_label

    def _save_inline_edit(self):
        """Save the inline edit."""
        if not self._inline_edit_entry or not self._inline_edit_task_id:
            return

        new_title = self._inline_edit_entry.get().strip()
        if new_title:
            self.task_manager.update_daily_task(self._inline_edit_task_id, {'title': new_title})

        self._cleanup_inline_edit()
        self.refresh()

    def _cancel_inline_edit(self):
        """Cancel the inline edit without saving."""
        self._cleanup_inline_edit()
        self.refresh()

    def _cleanup_inline_edit(self):
        """Clean up inline edit widgets."""
        if self._inline_edit_entry:
            try:
                self._inline_edit_entry.destroy()
            except tk.TclError:
                pass
            self._inline_edit_entry = None
        self._inline_edit_task_id = None
        self._inline_edit_row = None
        self._inline_edit_title_label = None

    # ===== NAVIGATION =====

    def _prev_period(self):
        """Go to previous period based on current view."""
        if self.current_view == "Month":
            if self.current_date.month == 1:
                self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
            else:
                self.current_date = self.current_date.replace(month=self.current_date.month - 1)
            self.focused_cell = None
        elif self.current_view == "Week":
            self.current_date = self.current_date - timedelta(weeks=1)
            self._build_week_view_structure()
        elif self.current_view == "Day":
            new_date = datetime.strptime(self.selected_date, '%Y-%m-%d') - timedelta(days=1)
            self.selected_date = new_date.strftime('%Y-%m-%d')
            self.current_date = new_date
            self._build_day_view_structure()

        self.refresh()

    def _next_period(self):
        """Go to next period based on current view."""
        if self.current_view == "Month":
            if self.current_date.month == 12:
                self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
            else:
                self.current_date = self.current_date.replace(month=self.current_date.month + 1)
            self.focused_cell = None
        elif self.current_view == "Week":
            self.current_date = self.current_date + timedelta(weeks=1)
            self._build_week_view_structure()
        elif self.current_view == "Day":
            new_date = datetime.strptime(self.selected_date, '%Y-%m-%d') + timedelta(days=1)
            self.selected_date = new_date.strftime('%Y-%m-%d')
            self.current_date = new_date
            self._build_day_view_structure()

        self.refresh()

    def _go_to_today(self):
        """Go to today's date."""
        self.current_date = datetime.now()
        self.selected_date = datetime.now().strftime('%Y-%m-%d')
        self.focused_cell = None

        if self.current_view == "Week":
            self._build_week_view_structure()
        elif self.current_view == "Day":
            self._build_day_view_structure()

        self.refresh()
        if self.current_view == "Month":
            self._focus_selected_date()

    def _export_calendar(self):
        """Export tasks to .ics file."""
        from tkinter import filedialog, messagebox

        year = self.current_date.year
        month = self.current_date.month
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)

        filename = filedialog.asksaveasfilename(
            defaultextension=".ics",
            filetypes=[("iCalendar", "*.ics")],
            initialfilename=f"produceros_tasks_{year}_{month:02d}.ics"
        )

        if not filename:
            return

        try:
            self.task_manager.export_to_ics(filename, first_day.strftime('%Y-%m-%d'),
                                           last_day.strftime('%Y-%m-%d'))
            messagebox.showinfo("Export Complete", f"Calendar exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")


class AddTaskDialog(ctk.CTkToplevel):
    """Dialog for adding a task/event to a specific date."""

    def __init__(self, parent, task_manager, date_str: str, on_save=None,
                 allow_date_edit: bool = False, default_time: str = None):
        super().__init__(parent)

        self.task_manager = task_manager
        self.date_str = date_str
        self.on_save = on_save
        self.allow_date_edit = allow_date_edit
        self.default_time = default_time

        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        date_display = date_obj.strftime("%A, %B %d, %Y")

        self.title("Add Task")
        self.geometry("420x480")
        self.minsize(380, 400)
        self.resizable(True, True)

        self.configure(fg_color=COLORS['bg_main'])
        self.transient(parent)
        self.grab_set()

        self.bind("<Escape>", lambda e: self.destroy())

        self._build_ui(date_display)

    def _build_ui(self, date_display: str):
        """Build the dialog UI with scrollable content."""
        from ui.date_picker import DatePickerWidget

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(
            self, fg_color=COLORS['bg_card'], corner_radius=8,
            scrollbar_button_color=COLORS['bg_hover']
        )
        scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))

        if self.allow_date_edit:
            ctk.CTkLabel(
                scroll, text="Date",
                font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
                text_color=COLORS['fg_secondary']
            ).pack(anchor="w", padx=12, pady=(12, 4))

            date_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            date_frame.pack(fill="x", padx=12, pady=(0, 8))

            self.date_picker = DatePickerWidget(
                date_frame, initial_date=self.date_str,
                on_date_change=self._on_date_change
            )
            self.date_picker.pack(anchor="w")
        else:
            ctk.CTkLabel(
                scroll, text=date_display,
                font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
                text_color=COLORS['accent']
            ).pack(anchor="w", padx=12, pady=(12, 8))

        ctk.CTkLabel(
            scroll, text="Title *",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=COLORS['fg_secondary']
        ).pack(anchor="w", padx=12, pady=(4, 4))

        self.title_entry = ctk.CTkEntry(
            scroll, font=ctk.CTkFont(family="Inter", size=12),
            fg_color=COLORS['bg_input'], border_color=COLORS['border'],
            height=36, placeholder_text="Task or event title..."
        )
        self.title_entry.pack(fill="x", padx=12, pady=(0, 12))
        self.title_entry.bind("<Return>", lambda e: self._save_task())

        # All day checkbox - default unchecked if time provided
        default_all_day = self.default_time is None
        self.all_day_var = ctk.BooleanVar(value=default_all_day)
        self.all_day_check = ctk.CTkCheckBox(
            scroll, text="All Day",
            font=ctk.CTkFont(family="Inter", size=12),
            variable=self.all_day_var,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            command=self._toggle_time_inputs
        )
        self.all_day_check.pack(anchor="w", padx=12, pady=(0, 8))

        self.time_frame = ctk.CTkFrame(scroll, fg_color="transparent")

        start_frame = ctk.CTkFrame(self.time_frame, fg_color="transparent")
        start_frame.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(
            start_frame, text="Start Time",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=COLORS['fg_secondary']
        ).pack(anchor="w")

        self.start_time = ctk.CTkEntry(
            start_frame, font=ctk.CTkFont(family="JetBrains Mono", size=12),
            fg_color=COLORS['bg_input'], border_color=COLORS['border'],
            height=32, placeholder_text="09:00", width=90
        )
        self.start_time.pack(anchor="w", pady=(4, 0))

        if self.default_time:
            self.start_time.insert(0, self.default_time)

        end_frame = ctk.CTkFrame(self.time_frame, fg_color="transparent")
        end_frame.pack(side="left")

        ctk.CTkLabel(
            end_frame, text="End Time",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=COLORS['fg_secondary']
        ).pack(anchor="w")

        self.end_time = ctk.CTkEntry(
            end_frame, font=ctk.CTkFont(family="JetBrains Mono", size=12),
            fg_color=COLORS['bg_input'], border_color=COLORS['border'],
            height=32, placeholder_text="10:00", width=90
        )
        self.end_time.pack(anchor="w", pady=(4, 0))

        if self.default_time:
            try:
                hour, minute = map(int, self.default_time.split(':'))
                end_hour = hour + 1
                self.end_time.insert(0, f"{end_hour:02d}:{minute:02d}")
            except (ValueError, AttributeError):
                pass

        if not default_all_day:
            self.time_frame.pack(fill="x", padx=12, pady=(0, 8), after=self.all_day_check)

        ctk.CTkLabel(
            scroll, text="Context",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=COLORS['fg_secondary']
        ).pack(anchor="w", padx=12, pady=(8, 4))

        self.context_var = ctk.StringVar(value="@Studio")
        contexts = ["@Studio", "@Mixing", "@Marketing", "@Admin", "@Other"]
        self.context_menu = ctk.CTkOptionMenu(
            scroll, variable=self.context_var, values=contexts,
            font=ctk.CTkFont(family="Inter", size=11),
            fg_color=COLORS['bg_input'], button_color=COLORS['bg_hover'],
            dropdown_fg_color=COLORS['bg_card'],
            width=160, height=32
        )
        self.context_menu.pack(anchor="w", padx=12, pady=(0, 12))

        ctk.CTkLabel(
            scroll, text="Notes (optional)",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=COLORS['fg_secondary']
        ).pack(anchor="w", padx=12, pady=(0, 4))

        self.notes_entry = ctk.CTkTextbox(
            scroll, font=ctk.CTkFont(family="Inter", size=11),
            fg_color=COLORS['bg_input'], border_color=COLORS['border'],
            height=60, corner_radius=4
        )
        self.notes_entry.pack(fill="x", padx=12, pady=(0, 12))

        self.scroll = scroll

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))

        ctk.CTkButton(
            btn_frame, text="Cancel",
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color=COLORS['bg_hover'], hover_color=COLORS['bg_dark'],
            height=36, width=80, corner_radius=4,
            text_color=COLORS['fg_secondary'],
            command=self.destroy
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_frame, text="Add Task",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            fg_color=COLORS['accent'], hover_color=COLORS['accent_hover'],
            height=36, width=100, corner_radius=4,
            text_color="#ffffff",
            command=self._save_task
        ).pack(side="right")

    def _toggle_time_inputs(self):
        """Show/hide time inputs based on all_day checkbox."""
        if self.all_day_var.get():
            self.time_frame.pack_forget()
        else:
            self.time_frame.pack(fill="x", padx=12, pady=(0, 8), after=self.all_day_check)

    def _on_date_change(self, new_date: str):
        """Handle date change from date picker."""
        self.date_str = new_date

    def _save_task(self):
        """Save the task."""
        title = self.title_entry.get().strip()
        if not title:
            self.title_entry.configure(border_color="#EF4444")
            return

        if self.allow_date_edit:
            scheduled_date = self.date_picker.get_date()
        else:
            scheduled_date = self.date_str

        task_data = {
            'title': title,
            'scheduled_date': scheduled_date,
            'context': self.context_var.get(),
            'notes': self.notes_entry.get("1.0", "end").strip(),
            'all_day': self.all_day_var.get(),
            'priority': 0
        }

        if not self.all_day_var.get():
            start = self.start_time.get().strip()
            end = self.end_time.get().strip()
            if start:
                task_data['start_time'] = start
            if end:
                task_data['end_time'] = end

        self.task_manager.add_daily_task(task_data)

        if self.on_save:
            self.on_save()
        self.destroy()
