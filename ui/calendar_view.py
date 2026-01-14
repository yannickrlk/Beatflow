"""Calendar View - Optimized month calendar for task planning."""

import customtkinter as ctk
from ui.theme import COLORS, SPACING
from core.task_manager import get_task_manager
from datetime import datetime, timedelta
import calendar
import tkinter as tk


class CalendarView(ctk.CTkFrame):
    """Optimized month calendar view with task indicators."""

    def __init__(self, parent, on_date_select=None, **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_main'], **kwargs)
        self.task_manager = get_task_manager()
        self.on_date_select = on_date_select

        # Current displayed month
        self.current_date = datetime.now()
        self.selected_date = datetime.now().strftime('%Y-%m-%d')

        # Cache for cell buttons (reuse instead of recreate)
        self.day_buttons = {}
        self.tasks_cache = {}

        self._build_ui()
        self._create_grid_cells()
        self.refresh()

    def _build_ui(self):
        """Build the calendar UI structure."""
        # Header with month navigation
        header = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], height=50, corner_radius=8)
        header.pack(fill="x", padx=8, pady=(8, 4))
        header.pack_propagate(False)

        # Navigation buttons and label
        self.prev_btn = ctk.CTkButton(
            header, text="<", font=ctk.CTkFont(size=14, weight="bold"),
            width=32, height=32, fg_color=COLORS['bg_hover'],
            hover_color=COLORS['accent'], corner_radius=4,
            command=self._prev_month
        )
        self.prev_btn.pack(side="left", padx=8, pady=9)

        self.month_label = ctk.CTkLabel(
            header, text="", font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            text_color=COLORS['fg']
        )
        self.month_label.pack(side="left", padx=8)

        self.next_btn = ctk.CTkButton(
            header, text=">", font=ctk.CTkFont(size=14, weight="bold"),
            width=32, height=32, fg_color=COLORS['bg_hover'],
            hover_color=COLORS['accent'], corner_radius=4,
            command=self._next_month
        )
        self.next_btn.pack(side="left")

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

        # Main container
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=8, pady=4)
        main_container.grid_columnconfigure(0, weight=3)
        main_container.grid_columnconfigure(1, weight=1)
        main_container.grid_rowconfigure(0, weight=1)

        # Calendar section
        self.calendar_section = ctk.CTkFrame(main_container, fg_color=COLORS['bg_card'], corner_radius=8)
        self.calendar_section.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        # Day headers
        days_header = ctk.CTkFrame(self.calendar_section, fg_color=COLORS['bg_dark'], height=32)
        days_header.pack(fill="x", padx=2, pady=(2, 0))
        days_header.pack_propagate(False)

        for i, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            color = COLORS['fg_dim'] if i >= 5 else COLORS['fg_secondary']
            ctk.CTkLabel(
                days_header, text=day, font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                text_color=color
            ).pack(side="left", expand=True, pady=6)

        # Calendar grid frame
        self.calendar_frame = ctk.CTkFrame(self.calendar_section, fg_color="transparent")
        self.calendar_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Configure grid
        for col in range(7):
            self.calendar_frame.grid_columnconfigure(col, weight=1, uniform="day")
        for row in range(6):
            self.calendar_frame.grid_rowconfigure(row, weight=1, uniform="week")

        # Info panel
        self.info_frame = ctk.CTkFrame(main_container, fg_color=COLORS['bg_card'], corner_radius=8)
        self.info_frame.grid(row=0, column=1, sticky="nsew")

    def _create_grid_cells(self):
        """Create all 42 day cells once (6 rows x 7 cols)."""
        for row in range(6):
            for col in range(7):
                cell_key = (row, col)
                btn = ctk.CTkButton(
                    self.calendar_frame,
                    text="",
                    font=ctk.CTkFont(family="Inter", size=13),
                    fg_color=COLORS['bg_card'],
                    hover_color=COLORS['bg_hover'],
                    corner_radius=4,
                    anchor="nw",
                    command=lambda r=row, c=col: self._on_cell_click(r, c)
                )
                btn.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)
                # Right-click binding for context menu
                btn.bind("<Button-3>", lambda e, r=row, c=col: self._on_cell_right_click(e, r, c))
                self.day_buttons[cell_key] = btn

    def refresh(self):
        """Refresh the calendar display efficiently."""
        self._update_month_label()
        self._load_tasks_for_month()
        self._update_calendar_cells()
        self._update_date_info()

    def _update_month_label(self):
        """Update the month/year label."""
        self.month_label.configure(text=self.current_date.strftime("%B %Y"))

    def _load_tasks_for_month(self):
        """Load all tasks for the month in a single query."""
        year = self.current_date.year
        month = self.current_date.month

        # Get date range
        first_day = f"{year}-{month:02d}-01"
        if month == 12:
            last_day = f"{year}-12-31"
        else:
            next_month = datetime(year, month + 1, 1) - timedelta(days=1)
            last_day = next_month.strftime('%Y-%m-%d')

        # Single query for all tasks in range
        self.tasks_cache = self.task_manager.get_tasks_for_month(year, month)

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
                        completed = sum(1 for t in tasks if t.get('completed'))
                        if len(tasks) <= 3:
                            dots = "●" * completed + "○" * (len(tasks) - completed)
                            text = f"{day}\n{dots}"
                        else:
                            text = f"{day}\n{completed}/{len(tasks)}"

                    # Set colors
                    if is_selected:
                        fg_color = COLORS['accent']
                        text_color = "#ffffff"
                        hover = COLORS['accent_hover']
                    elif is_today:
                        fg_color = COLORS['bg_hover']
                        text_color = COLORS['accent']
                        hover = COLORS['bg_card']
                    elif is_weekend:
                        fg_color = COLORS['bg_dark']
                        text_color = COLORS['fg_dim']
                        hover = COLORS['bg_hover']
                    else:
                        fg_color = COLORS['bg_card']
                        text_color = COLORS['fg'] if has_tasks else COLORS['fg_secondary']
                        hover = COLORS['bg_hover']

                    btn.configure(
                        text=text,
                        fg_color=fg_color,
                        text_color=text_color,
                        hover_color=hover,
                        state="normal"
                    )
                    btn._date_str = date_str
                else:
                    # Empty cell
                    btn.configure(
                        text="",
                        fg_color=COLORS['bg_dark'] if is_weekend else COLORS['bg_card'],
                        hover_color=COLORS['bg_dark'],
                        state="disabled"
                    )
                    btn._date_str = None

    def _on_cell_click(self, row: int, col: int):
        """Handle cell click."""
        btn = self.day_buttons[(row, col)]
        date_str = getattr(btn, '_date_str', None)
        if date_str:
            self.selected_date = date_str
            self._update_calendar_cells()
            self._update_date_info()
            if self.on_date_select:
                self.on_date_select(date_str)

    def _on_cell_right_click(self, event, row: int, col: int):
        """Handle right-click on a cell - show context menu."""
        btn = self.day_buttons[(row, col)]
        date_str = getattr(btn, '_date_str', None)
        if not date_str:
            return

        # Create context menu
        menu = tk.Menu(self, tearoff=0, bg=COLORS['bg_card'], fg=COLORS['fg'],
                      activebackground=COLORS['accent'], activeforeground="#ffffff",
                      font=("Inter", 10))
        menu.add_command(label="+ Add Task/Event", command=lambda: self._open_add_task_dialog(date_str))
        menu.add_separator()
        menu.add_command(label="View Day", command=lambda: self._on_cell_click(row, col))

        # Show menu at cursor position
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _open_add_task_dialog(self, date_str: str):
        """Open dialog to add a new task/event."""
        dialog = AddTaskDialog(self, self.task_manager, date_str, on_save=self.refresh)
        dialog.focus()

    def _add_task_to_selected(self):
        """Add a task to the currently selected date (with date picker)."""
        dialog = AddTaskDialog(self, self.task_manager, self.selected_date,
                              on_save=self.refresh, allow_date_edit=True)
        dialog.focus()

    def _update_date_info(self):
        """Update the selected date info panel."""
        # Clear existing
        for widget in self.info_frame.winfo_children():
            widget.destroy()

        date_obj = datetime.strptime(self.selected_date, '%Y-%m-%d')
        is_today = date_obj.date() == datetime.now().date()

        # Header
        header = ctk.CTkFrame(self.info_frame, fg_color=COLORS['bg_dark'], height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text=date_obj.strftime("%A"),
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=COLORS['fg_secondary']
        ).pack(anchor="w", padx=12, pady=(8, 0))

        date_row = ctk.CTkFrame(header, fg_color="transparent")
        date_row.pack(fill="x", padx=12)

        ctk.CTkLabel(
            date_row, text=date_obj.strftime("%b %d, %Y"),
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=COLORS['fg']
        ).pack(side="left")

        if is_today:
            ctk.CTkLabel(
                date_row, text="TODAY",
                font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                text_color="#ffffff", fg_color=COLORS['accent'],
                corner_radius=3, padx=4, pady=1
            ).pack(side="left", padx=6)

        # Tasks for selected date
        tasks = self.tasks_cache.get(self.selected_date, [])

        # Task count
        count_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent", height=30)
        count_frame.pack(fill="x", padx=12, pady=6)
        count_frame.pack_propagate(False)

        if tasks:
            completed = sum(1 for t in tasks if t.get('completed'))
            ctk.CTkLabel(
                count_frame, text=f"{len(tasks)} task{'s' if len(tasks) != 1 else ''}",
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=COLORS['fg_secondary']
            ).pack(side="left")

            color = "#22C55E" if completed == len(tasks) else COLORS['accent']
            ctk.CTkLabel(
                count_frame, text=f"{completed}/{len(tasks)}",
                font=ctk.CTkFont(family="JetBrains Mono", size=11),
                text_color=color
            ).pack(side="right")
        else:
            ctk.CTkLabel(
                count_frame, text="No tasks",
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=COLORS['fg_dim']
            ).pack(side="left")

        # Divider
        ctk.CTkFrame(self.info_frame, fg_color=COLORS['border'], height=1).pack(fill="x", padx=12)

        # Task list
        if not tasks:
            empty = ctk.CTkFrame(self.info_frame, fg_color="transparent")
            empty.pack(expand=True)
            ctk.CTkLabel(
                empty, text="No tasks scheduled",
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=COLORS['fg_dim']
            ).pack(pady=20)
            return

        task_list = ctk.CTkScrollableFrame(
            self.info_frame, fg_color="transparent",
            scrollbar_button_color=COLORS['bg_hover']
        )
        task_list.pack(fill="both", expand=True, padx=4, pady=4)

        for task in tasks:
            self._create_task_row(task_list, task)

    def _create_task_row(self, parent, task: dict):
        """Create a compact task row."""
        done = task.get('completed', False)
        row = ctk.CTkFrame(parent, fg_color=COLORS['bg_dark'] if done else COLORS['bg_hover'],
                          corner_radius=4, height=36)
        row.pack(fill="x", pady=2, padx=4)
        row.pack_propagate(False)

        check = "✓" if done else "○"
        color = "#22C55E" if done else COLORS['fg_dim']
        ctk.CTkLabel(row, text=check, font=ctk.CTkFont(size=12),
                    text_color=color, width=20).pack(side="left", padx=(8, 4))

        title = task['title'][:22] + ('...' if len(task['title']) > 22 else '')
        ctk.CTkLabel(row, text=title, font=ctk.CTkFont(family="Inter", size=11),
                    text_color=COLORS['fg_dim'] if done else COLORS['fg'],
                    anchor="w").pack(side="left", fill="x", expand=True)

        if task.get('context'):
            ctx_colors = {"@Studio": "#9B59B6", "@Mixing": "#3498DB",
                         "@Marketing": "#E74C3C", "@Admin": "#95A5A6"}
            ctk.CTkLabel(
                row, text=task['context'].replace('@', ''),
                font=ctk.CTkFont(family="Inter", size=9),
                text_color=ctx_colors.get(task['context'], "#7F8C8D"),
                fg_color=COLORS['bg_card'], corner_radius=3, padx=3
            ).pack(side="right", padx=8)

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

    def __init__(self, parent, task_manager, date_str: str, on_save=None, allow_date_edit: bool = False):
        super().__init__(parent)

        self.task_manager = task_manager
        self.date_str = date_str
        self.on_save = on_save
        self.allow_date_edit = allow_date_edit

        # Parse date for display
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        date_display = date_obj.strftime("%A, %B %d, %Y")

        self.title("Add Task")
        self.geometry("420x480")
        self.minsize(380, 400)
        self.resizable(True, True)

        self.configure(fg_color=COLORS['bg_main'])
        self.transient(parent)
        self.grab_set()

        self._build_ui(date_display)

    def _build_ui(self, date_display: str):
        """Build the dialog UI with scrollable content."""
        from ui.date_picker import DatePickerWidget

        # Main container with grid for proper expansion
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Scrollable content area
        scroll = ctk.CTkScrollableFrame(
            self, fg_color=COLORS['bg_card'], corner_radius=8,
            scrollbar_button_color=COLORS['bg_hover']
        )
        scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))

        # Date section
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

        # Title
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

        # All day checkbox
        self.all_day_var = ctk.BooleanVar(value=True)
        self.all_day_check = ctk.CTkCheckBox(
            scroll, text="All Day",
            font=ctk.CTkFont(family="Inter", size=12),
            variable=self.all_day_var,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            command=self._toggle_time_inputs
        )
        self.all_day_check.pack(anchor="w", padx=12, pady=(0, 8))

        # Time inputs frame (will be shown/hidden)
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

        # Context dropdown
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

        # Notes
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

        # Store scroll reference for time toggle
        self.scroll = scroll

        # Buttons frame (fixed at bottom, outside scroll)
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
            # Re-pack after all_day checkbox
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

        # Get date (from picker if editable, otherwise from stored value)
        if self.allow_date_edit:
            scheduled_date = self.date_picker.get_date()
        else:
            scheduled_date = self.date_str

        # Prepare task data
        task_data = {
            'title': title,
            'scheduled_date': scheduled_date,
            'context': self.context_var.get(),
            'notes': self.notes_entry.get("1.0", "end").strip(),
            'all_day': self.all_day_var.get(),
            'priority': 0
        }

        # Add time if not all day
        if not self.all_day_var.get():
            start = self.start_time.get().strip()
            end = self.end_time.get().strip()
            if start:
                task_data['start_time'] = start
            if end:
                task_data['end_time'] = end

        # Save task
        self.task_manager.add_daily_task(task_data)

        # Callback and close
        if self.on_save:
            self.on_save()
        self.destroy()
