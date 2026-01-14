"""DatePicker Widget for ProducerOS - Modern calendar date selection."""

import customtkinter as ctk
from datetime import datetime, timedelta
import calendar
from ui.theme import COLORS, SPACING


class DatePickerWidget(ctk.CTkFrame):
    """A date picker with text input and calendar popup."""

    def __init__(self, parent, initial_date: str = None, on_date_change=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.on_date_change = on_date_change
        self.popup = None

        # Parse initial date or use today
        if initial_date:
            try:
                self.selected_date = datetime.strptime(initial_date, '%Y-%m-%d')
            except ValueError:
                self.selected_date = datetime.now()
        else:
            self.selected_date = datetime.now()

        self._build_ui()

    def _build_ui(self):
        """Build the date picker UI."""
        # Container frame
        container = ctk.CTkFrame(self, fg_color=COLORS['bg_input'], corner_radius=4, height=36)
        container.pack(fill="x")
        container.pack_propagate(False)

        # Date entry
        self.date_entry = ctk.CTkEntry(
            container,
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color="transparent",
            border_width=0,
            placeholder_text="YYYY-MM-DD"
        )
        self.date_entry.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.date_entry.insert(0, self.selected_date.strftime('%Y-%m-%d'))
        self.date_entry.bind("<FocusOut>", self._on_entry_change)
        self.date_entry.bind("<Return>", self._on_entry_change)

        # Calendar button
        cal_btn = ctk.CTkButton(
            container,
            text="\U0001f4c5",  # Calendar emoji
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            width=32,
            height=32,
            corner_radius=4,
            command=self._toggle_popup
        )
        cal_btn.pack(side="right", padx=2, pady=2)

    def _on_entry_change(self, event=None):
        """Handle manual date entry."""
        value = self.date_entry.get().strip()
        try:
            new_date = datetime.strptime(value, '%Y-%m-%d')
            self.selected_date = new_date
            if self.on_date_change:
                self.on_date_change(value)
        except ValueError:
            # Reset to current selected date
            self.date_entry.delete(0, 'end')
            self.date_entry.insert(0, self.selected_date.strftime('%Y-%m-%d'))

    def _toggle_popup(self):
        """Toggle the calendar popup."""
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()
            self.popup = None
        else:
            self._show_popup()

    def _show_popup(self):
        """Show the calendar popup."""
        # Calculate position
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4

        # Create popup
        self.popup = ctk.CTkToplevel(self)
        self.popup.wm_overrideredirect(True)
        self.popup.wm_geometry(f"+{x}+{y}")
        self.popup.attributes("-topmost", True)

        # Popup container
        popup_frame = ctk.CTkFrame(
            self.popup,
            fg_color=COLORS['bg_card'],
            corner_radius=8,
            border_width=1,
            border_color=COLORS['border']
        )
        popup_frame.pack(fill="both", expand=True, padx=1, pady=1)

        # Calendar widget
        self.calendar_widget = CalendarPopup(
            popup_frame,
            current_date=self.selected_date,
            on_date_select=self._on_popup_date_select
        )
        self.calendar_widget.pack(fill="both", expand=True, padx=4, pady=4)

        # Bind click outside to close
        self.popup.bind("<FocusOut>", self._close_popup_on_focus_out)

    def _close_popup_on_focus_out(self, event):
        """Close popup when focus is lost."""
        # Small delay to allow for internal clicks
        self.after(100, self._check_and_close_popup)

    def _check_and_close_popup(self):
        """Check if popup should close."""
        if self.popup and self.popup.winfo_exists():
            try:
                # Check if focus is inside popup
                focused = self.popup.focus_get()
                if focused is None:
                    self.popup.destroy()
                    self.popup = None
            except:
                pass

    def _on_popup_date_select(self, date: datetime):
        """Handle date selection from popup."""
        self.selected_date = date
        self.date_entry.delete(0, 'end')
        self.date_entry.insert(0, date.strftime('%Y-%m-%d'))

        if self.popup:
            self.popup.destroy()
            self.popup = None

        if self.on_date_change:
            self.on_date_change(date.strftime('%Y-%m-%d'))

    def get_date(self) -> str:
        """Get the selected date as YYYY-MM-DD string."""
        return self.selected_date.strftime('%Y-%m-%d')

    def set_date(self, date_str: str):
        """Set the selected date from a YYYY-MM-DD string."""
        try:
            self.selected_date = datetime.strptime(date_str, '%Y-%m-%d')
            self.date_entry.delete(0, 'end')
            self.date_entry.insert(0, date_str)
        except ValueError:
            pass


class CalendarPopup(ctk.CTkFrame):
    """Compact calendar popup for date selection."""

    def __init__(self, parent, current_date: datetime = None, on_date_select=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.current_date = current_date or datetime.now()
        self.display_month = self.current_date.replace(day=1)
        self.on_date_select = on_date_select

        self._build_ui()

    def _build_ui(self):
        """Build the calendar UI."""
        # Header with month navigation
        header = ctk.CTkFrame(self, fg_color="transparent", height=32)
        header.pack(fill="x", pady=(0, 4))
        header.pack_propagate(False)

        # Previous month
        prev_btn = ctk.CTkButton(
            header,
            text="\u25C0",  # Left arrow
            font=ctk.CTkFont(size=10),
            width=28,
            height=28,
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            corner_radius=4,
            command=self._prev_month
        )
        prev_btn.pack(side="left")

        # Month/Year label
        self.month_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=COLORS['fg']
        )
        self.month_label.pack(side="left", expand=True)

        # Next month
        next_btn = ctk.CTkButton(
            header,
            text="\u25B6",  # Right arrow
            font=ctk.CTkFont(size=10),
            width=28,
            height=28,
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            corner_radius=4,
            command=self._next_month
        )
        next_btn.pack(side="right")

        # Day headers
        days_frame = ctk.CTkFrame(self, fg_color="transparent", height=24)
        days_frame.pack(fill="x")
        days_frame.pack_propagate(False)

        day_names = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for day in day_names:
            ctk.CTkLabel(
                days_frame,
                text=day,
                font=ctk.CTkFont(family="Inter", size=10),
                text_color=COLORS['fg_dim'],
                width=32
            ).pack(side="left")

        # Calendar grid
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True)

        self._refresh_calendar()

    def _refresh_calendar(self):
        """Refresh the calendar grid."""
        # Update month label
        self.month_label.configure(text=self.display_month.strftime("%B %Y"))

        # Clear existing grid
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        # Get calendar data
        year = self.display_month.year
        month = self.display_month.month
        cal = calendar.Calendar(firstweekday=0)

        today = datetime.now().date()
        selected = self.current_date.date()

        # Build weeks
        for week in cal.monthdayscalendar(year, month):
            week_frame = ctk.CTkFrame(self.grid_frame, fg_color="transparent", height=28)
            week_frame.pack(fill="x")
            week_frame.pack_propagate(False)

            for day in week:
                if day == 0:
                    # Empty cell
                    ctk.CTkFrame(week_frame, fg_color="transparent", width=32).pack(side="left")
                else:
                    date_obj = datetime(year, month, day).date()
                    is_today = date_obj == today
                    is_selected = date_obj == selected

                    # Determine colors
                    if is_selected:
                        bg = COLORS['accent']
                        fg = "#ffffff"
                    elif is_today:
                        bg = COLORS['bg_hover']
                        fg = COLORS['fg']
                    else:
                        bg = "transparent"
                        fg = COLORS['fg']

                    btn = ctk.CTkButton(
                        week_frame,
                        text=str(day),
                        font=ctk.CTkFont(family="Inter", size=11),
                        width=32,
                        height=26,
                        fg_color=bg,
                        hover_color=COLORS['accent'] if not is_selected else COLORS['accent_hover'],
                        corner_radius=4,
                        text_color=fg,
                        command=lambda d=day: self._on_day_click(d)
                    )
                    btn.pack(side="left")

    def _prev_month(self):
        """Go to previous month."""
        if self.display_month.month == 1:
            self.display_month = self.display_month.replace(year=self.display_month.year - 1, month=12)
        else:
            self.display_month = self.display_month.replace(month=self.display_month.month - 1)
        self._refresh_calendar()

    def _next_month(self):
        """Go to next month."""
        if self.display_month.month == 12:
            self.display_month = self.display_month.replace(year=self.display_month.year + 1, month=1)
        else:
            self.display_month = self.display_month.replace(month=self.display_month.month + 1)
        self._refresh_calendar()

    def _on_day_click(self, day: int):
        """Handle day click."""
        selected = datetime(self.display_month.year, self.display_month.month, day)
        self.current_date = selected

        if self.on_date_select:
            self.on_date_select(selected)
