"""Calendar View - Month calendar for task planning and visualization."""

import customtkinter as ctk
from ui.theme import COLORS, SPACING
from core.task_manager import get_task_manager
from datetime import datetime, timedelta
import calendar


class CalendarView(ctk.CTkFrame):
    """Month calendar view with task indicators."""

    def __init__(self, parent, on_date_select=None, **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_main'], **kwargs)
        self.task_manager = get_task_manager()
        self.on_date_select = on_date_select

        # Current displayed month
        self.current_date = datetime.now()
        self.selected_date = datetime.now().strftime('%Y-%m-%d')

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        """Build the calendar UI."""
        # Header with month navigation
        header = ctk.CTkFrame(self, fg_color="transparent", height=50)
        header.pack(fill="x", padx=SPACING['lg'], pady=(SPACING['lg'], SPACING['sm']))
        header.pack_propagate(False)

        # Previous month button
        self.prev_btn = ctk.CTkButton(
            header,
            text="<",
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            width=40,
            height=36,
            fg_color=COLORS['bg_card'],
            hover_color=COLORS['bg_hover'],
            corner_radius=6,
            command=self._prev_month
        )
        self.prev_btn.pack(side="left")

        # Month/Year label
        self.month_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=COLORS['fg']
        )
        self.month_label.pack(side="left", padx=SPACING['lg'])

        # Next month button
        self.next_btn = ctk.CTkButton(
            header,
            text=">",
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            width=40,
            height=36,
            fg_color=COLORS['bg_card'],
            hover_color=COLORS['bg_hover'],
            corner_radius=6,
            command=self._next_month
        )
        self.next_btn.pack(side="left")

        # Today button
        ctk.CTkButton(
            header,
            text="Today",
            font=ctk.CTkFont(family="Inter", size=12),
            width=70,
            height=32,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            corner_radius=6,
            command=self._go_to_today
        ).pack(side="right")

        # Export button
        ctk.CTkButton(
            header,
            text="Export .ics",
            font=ctk.CTkFont(family="Inter", size=12),
            width=80,
            height=32,
            fg_color=COLORS['bg_card'],
            hover_color=COLORS['bg_hover'],
            corner_radius=6,
            command=self._export_calendar
        ).pack(side="right", padx=SPACING['sm'])

        # Day headers (Mon, Tue, etc.)
        days_header = ctk.CTkFrame(self, fg_color="transparent")
        days_header.pack(fill="x", padx=SPACING['lg'], pady=SPACING['sm'])

        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for day in day_names:
            ctk.CTkLabel(
                days_header,
                text=day,
                font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
                text_color=COLORS['fg_secondary'],
                width=60
            ).pack(side="left", expand=True)

        # Calendar grid
        self.calendar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.calendar_frame.pack(fill="both", expand=True, padx=SPACING['lg'], pady=SPACING['sm'])

        # Selected date info
        self.info_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], corner_radius=8)
        self.info_frame.pack(fill="x", padx=SPACING['lg'], pady=SPACING['md'])

    def refresh(self):
        """Refresh the calendar display."""
        self._update_month_label()
        self._build_calendar_grid()
        self._update_date_info()

    def _update_month_label(self):
        """Update the month/year label."""
        month_name = self.current_date.strftime("%B %Y")
        self.month_label.configure(text=month_name)

    def _build_calendar_grid(self):
        """Build the calendar day grid."""
        # Clear existing
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        # Get calendar data
        year = self.current_date.year
        month = self.current_date.month
        cal = calendar.Calendar(firstweekday=0)  # Monday first

        # Get tasks for this month
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)

        tasks_by_date = self._get_tasks_for_range(
            first_day.strftime('%Y-%m-%d'),
            last_day.strftime('%Y-%m-%d')
        )

        today = datetime.now().strftime('%Y-%m-%d')

        # Build weeks
        for week in cal.monthdayscalendar(year, month):
            week_frame = ctk.CTkFrame(self.calendar_frame, fg_color="transparent")
            week_frame.pack(fill="x", pady=2)

            for day in week:
                if day == 0:
                    # Empty cell for days outside month
                    cell = ctk.CTkFrame(week_frame, fg_color="transparent", width=60, height=60)
                    cell.pack(side="left", expand=True, padx=2)
                    cell.pack_propagate(False)
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    tasks = tasks_by_date.get(date_str, [])
                    self._create_day_cell(week_frame, day, date_str, tasks, today)

    def _create_day_cell(self, parent, day: int, date_str: str, tasks: list, today: str):
        """Create a single day cell."""
        is_today = date_str == today
        is_selected = date_str == self.selected_date
        has_tasks = len(tasks) > 0
        completed = sum(1 for t in tasks if t.get('completed'))

        # Determine colors
        if is_selected:
            bg_color = COLORS['accent']
            text_color = COLORS['fg']
        elif is_today:
            bg_color = COLORS['bg_hover']
            text_color = COLORS['fg']
        else:
            bg_color = COLORS['bg_card']
            text_color = COLORS['fg'] if has_tasks else COLORS['fg_secondary']

        cell = ctk.CTkFrame(
            parent,
            fg_color=bg_color,
            width=60,
            height=60,
            corner_radius=6
        )
        cell.pack(side="left", expand=True, padx=2)
        cell.pack_propagate(False)

        # Day number
        day_label = ctk.CTkLabel(
            cell,
            text=str(day),
            font=ctk.CTkFont(family="Inter", size=14, weight="bold" if is_today else "normal"),
            text_color=text_color
        )
        day_label.pack(pady=(SPACING['xs'], 0))

        # Task indicator dots
        if has_tasks:
            dots_frame = ctk.CTkFrame(cell, fg_color="transparent", height=12)
            dots_frame.pack()

            # Show up to 3 dots
            for i in range(min(len(tasks), 3)):
                task = tasks[i]
                dot_color = COLORS['success'] if task.get('completed') else COLORS['accent']
                dot = ctk.CTkFrame(
                    dots_frame,
                    fg_color=dot_color,
                    width=6,
                    height=6,
                    corner_radius=3
                )
                dot.pack(side="left", padx=1)

            # Task count
            if len(tasks) > 0:
                count_text = f"{completed}/{len(tasks)}"
                ctk.CTkLabel(
                    cell,
                    text=count_text,
                    font=ctk.CTkFont(family="JetBrains Mono", size=9),
                    text_color=COLORS['fg_dim']
                ).pack()

        # Make clickable
        cell.bind("<Button-1>", lambda e, d=date_str: self._on_date_click(d))
        day_label.bind("<Button-1>", lambda e, d=date_str: self._on_date_click(d))

    def _get_tasks_for_range(self, start_date: str, end_date: str) -> dict:
        """Get tasks grouped by date for a date range."""
        # Get all tasks and filter by date range
        # This is a simplified approach - could be optimized with a SQL query
        result = {}

        # Query all tasks for each date in range
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        current = start
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            tasks = self.task_manager.get_daily_tasks(date_str)
            if tasks:
                result[date_str] = tasks
            current += timedelta(days=1)

        return result

    def _on_date_click(self, date_str: str):
        """Handle date click."""
        self.selected_date = date_str
        self.refresh()

        if self.on_date_select:
            self.on_date_select(date_str)

    def _update_date_info(self):
        """Update the selected date info panel."""
        # Clear existing
        for widget in self.info_frame.winfo_children():
            widget.destroy()

        # Date header
        date_obj = datetime.strptime(self.selected_date, '%Y-%m-%d')
        date_display = date_obj.strftime("%A, %B %d, %Y")

        header = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        header.pack(fill="x", padx=SPACING['md'], pady=SPACING['sm'])

        ctk.CTkLabel(
            header,
            text=date_display,
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=COLORS['fg']
        ).pack(side="left")

        # Get tasks for selected date
        tasks = self.task_manager.get_daily_tasks(self.selected_date)

        if not tasks:
            ctk.CTkLabel(
                self.info_frame,
                text="No tasks for this date",
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=COLORS['fg_secondary']
            ).pack(pady=SPACING['sm'])
            return

        # Task count
        completed = sum(1 for t in tasks if t.get('completed'))
        ctk.CTkLabel(
            header,
            text=f"{completed}/{len(tasks)} completed",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg_secondary']
        ).pack(side="right")

        # Task list (max 5)
        for task in tasks[:5]:
            self._create_task_row(task)

        if len(tasks) > 5:
            ctk.CTkLabel(
                self.info_frame,
                text=f"+ {len(tasks) - 5} more tasks",
                font=ctk.CTkFont(family="Inter", size=11),
                text_color=COLORS['fg_dim']
            ).pack(pady=SPACING['xs'])

    def _create_task_row(self, task: dict):
        """Create a compact task row."""
        row = ctk.CTkFrame(self.info_frame, fg_color="transparent", height=28)
        row.pack(fill="x", padx=SPACING['md'], pady=2)
        row.pack_propagate(False)

        # Completion indicator
        is_completed = task.get('completed', False)
        indicator_color = COLORS['success'] if is_completed else COLORS['fg_dim']

        indicator = ctk.CTkFrame(row, fg_color=indicator_color, width=8, height=8, corner_radius=4)
        indicator.pack(side="left", padx=(0, SPACING['sm']))

        # Title
        title_color = COLORS['fg_dim'] if is_completed else COLORS['fg']
        ctk.CTkLabel(
            row,
            text=task['title'],
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=title_color,
            anchor="w"
        ).pack(side="left", fill="x", expand=True)

        # Context tag
        if task.get('context'):
            context_colors = {
                "@Studio": "#9B59B6",
                "@Mixing": "#3498DB",
                "@Marketing": "#E74C3C",
                "@Admin": "#95A5A6",
                "@Other": "#7F8C8D"
            }
            color = context_colors.get(task['context'], "#7F8C8D")
            ctk.CTkLabel(
                row,
                text=task['context'],
                font=ctk.CTkFont(family="Inter", size=10),
                text_color=color
            ).pack(side="right")

    def _prev_month(self):
        """Go to previous month."""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        self.refresh()

    def _next_month(self):
        """Go to next month."""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        self.refresh()

    def _go_to_today(self):
        """Go to today's date."""
        self.current_date = datetime.now()
        self.selected_date = datetime.now().strftime('%Y-%m-%d')
        self.refresh()

    def _export_calendar(self):
        """Export tasks to .ics file."""
        from tkinter import filedialog, messagebox

        # Get date range (current month)
        year = self.current_date.year
        month = self.current_date.month
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)

        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".ics",
            filetypes=[("iCalendar", "*.ics")],
            initialfilename=f"produceros_tasks_{year}_{month:02d}.ics"
        )

        if not filename:
            return

        try:
            self.task_manager.export_to_ics(
                filename,
                first_day.strftime('%Y-%m-%d'),
                last_day.strftime('%Y-%m-%d')
            )
            messagebox.showinfo("Export Complete", f"Calendar exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
