# Current Task: Phase 21.2 - Studio Flow Advanced Features

## Status
- **Phase 21 (Studio Flow Core)**: COMPLETE
- **Phase 21.1 (UX Enhancements)**: COMPLETE
- **Phase 21.2 (Advanced Features)**: COMPLETE

## Objective
Add deep integrations, productivity insights, and collaboration features to Studio Flow including Focus Mode with Pomodoro timer, Productivity Dashboard with charts, Calendar Integration with .ics export, and Collaborative Projects.

## Implementation Summary

### Completed Features

1. **Focus Mode (Pomodoro Timer)**
   - `ui/focus_mode.py` - Full implementation
   - Fullscreen-like window (800x600) with ESC to close
   - 25-minute countdown timer with Start/Pause/Stop controls
   - Progress bar and session tracking
   - `QuickFocusDialog` for task selection
   - `FocusModeButton` component for task rows
   - Sessions saved to `focus_sessions` database table

2. **Productivity Dashboard**
   - `ui/productivity_dashboard.py` - Full implementation
   - Stats cards: Today's Tasks, Focus Time, Sessions, Active Projects
   - Weekly completion chart (bar chart with last 7 days)
   - Context breakdown chart (pie chart by @Studio, @Mixing, etc.)
   - Focus sessions timeline (area chart)
   - Insights panel with productivity tips
   - Fallback to text-based charts if matplotlib unavailable

3. **Calendar View**
   - `ui/calendar_view.py` - Full implementation
   - Month calendar grid with navigation (< > buttons)
   - Task indicators on dates (colored dots showing completion status)
   - Date selection with task list panel
   - "Today" button for quick navigation
   - Export to .ics button with file dialog

4. **Database Updates**
   - Added `time_spent` column to `daily_tasks` and `project_tasks`
   - Added `assigned_to` column to `project_tasks`
   - Created `focus_sessions` table for Pomodoro tracking

5. **Task Manager Methods**
   - `add_time_to_task()`, `get_task_time()` - Time tracking
   - `start_focus_session()`, `complete_focus_session()`, `get_focus_sessions()` - Pomodoro
   - `get_completion_stats_by_date()`, `get_completion_stats_by_context()` - Dashboard stats
   - `get_most_productive_day()`, `get_average_completion_time()` - Insights
   - `export_to_ics()` - Calendar export with RFC 5545 compliance

6. **UI Integration**
   - `ui/tasks_view.py` - Added Dashboard and Calendar tabs (4-tab layout)
   - `ui/today_view.py` - Added Focus Mode button in header

---

## New Dependencies

**Added to `requirements.txt`**:
- `matplotlib>=3.7.0` - For productivity charts
- `icalendar>=5.0.0` - For RFC 5545 compliant calendar export

**Installation**:
```bash
py -3.12 -m pip install matplotlib icalendar
```

---

## Database Schema Updates

### 1. Modify Tables in `core/database.py`

Add these columns to existing tables:

```sql
-- Add to daily_tasks table
ALTER TABLE daily_tasks ADD COLUMN time_spent INTEGER DEFAULT 0;  -- seconds

-- Add to project_tasks table  
ALTER TABLE project_tasks ADD COLUMN time_spent INTEGER DEFAULT 0;  -- seconds
ALTER TABLE project_tasks ADD COLUMN assigned_to INTEGER;  -- foreign key to clients table
ALTER TABLE project_tasks ADD COLUMN FOREIGN KEY (assigned_to) REFERENCES clients(id) ON DELETE SET NULL;

-- Create focus_sessions table for Pomodoro tracking
CREATE TABLE IF NOT EXISTS focus_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    is_daily_task BOOLEAN DEFAULT 1,
    duration INTEGER NOT NULL,  -- seconds (typically 1500 for 25min)
    completed BOOLEAN DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES daily_tasks(id) ON DELETE CASCADE
)
```

---

## Core Logic Updates

### 2. Update `core/task_manager.py`

Add these new methods:

```python
# ===== TIME TRACKING =====
def add_time_to_task(self, task_id: int, seconds: int, is_daily: bool = True) -> bool:
    """Add time spent to a task."""
    table = "daily_tasks" if is_daily else "project_tasks"
    # UPDATE {table} SET time_spent = time_spent + ? WHERE id = ?
    pass

def get_task_time(self, task_id: int, is_daily: bool = True) -> int:
    """Get total time spent on a task in seconds."""
    # SELECT time_spent FROM {table} WHERE id = ?
    pass

# ===== FOCUS SESSIONS (POMODORO) =====
def start_focus_session(self, task_id: int, is_daily: bool = True, duration: int = 1500) -> int:
    """Start a new focus session. Returns session ID."""
    # INSERT INTO focus_sessions (task_id, is_daily_task, duration, started_at)
    pass

def complete_focus_session(self, session_id: int) -> bool:
    """Mark focus session as completed."""
    # UPDATE focus_sessions SET completed = 1, ended_at = ? WHERE id = ?
    # Also update task time_spent
    pass

def get_focus_sessions(self, task_id: int = None, date: str = None) -> List[Dict]:
    """Get focus sessions, optionally filtered by task or date."""
    # SELECT * FROM focus_sessions WHERE ...
    pass

# ===== PRODUCTIVITY STATS =====
def get_completion_stats_by_date(self, start_date: str, end_date: str) -> List[Dict]:
    """Get daily completion counts for date range."""
    # SELECT DATE(completed_at) as date, COUNT(*) as count
    # FROM daily_tasks WHERE completed = 1 AND completed_at BETWEEN ? AND ?
    # GROUP BY DATE(completed_at)
    pass

def get_completion_stats_by_context(self) -> List[Dict]:
    """Get completion counts grouped by context."""
    # SELECT context, COUNT(*) as count, SUM(time_spent) as total_time
    # FROM daily_tasks WHERE completed = 1
    # GROUP BY context
    pass

def get_most_productive_day(self) -> str:
    """Get the day of week with most completions."""
    # SELECT strftime('%w', completed_at) as day_of_week, COUNT(*) as count
    # FROM daily_tasks WHERE completed = 1
    # GROUP BY day_of_week ORDER BY count DESC LIMIT 1
    pass

def get_average_completion_time(self) -> float:
    """Get average time to complete a task (in hours)."""
    # Calculate average time between created_at and completed_at
    pass

# ===== COLLABORATIVE TASKS =====
def assign_task_to_contact(self, task_id: int, contact_id: int) -> bool:
    """Assign a project task to a network contact."""
    # UPDATE project_tasks SET assigned_to = ? WHERE id = ?
    pass

def get_tasks_assigned_to(self, contact_id: int) -> List[Dict]:
    """Get all tasks assigned to a specific contact."""
    # SELECT * FROM project_tasks WHERE assigned_to = ?
    pass

def get_my_tasks(self) -> List[Dict]:
    """Get tasks not assigned to anyone (my tasks)."""
    # SELECT * FROM project_tasks WHERE assigned_to IS NULL
    pass

# ===== CALENDAR EXPORT =====
def export_to_ics(self, filepath: str, include_daily: bool = True, include_projects: bool = True) -> bool:
    """Export tasks to .ics calendar file."""
    from icalendar import Calendar, Event
    from datetime import datetime, timedelta
    import pytz
    
    cal = Calendar()
    cal.add('prodid', '-//Beatflow Studio Flow//beatflow.app//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'Beatflow Tasks')
    
    # Add daily tasks
    if include_daily:
        tasks = self.get_daily_tasks()
        for task in tasks:
            event = Event()
            event.add('summary', task['title'])
            event.add('uid', f"beatflow-daily-{task['id']}@beatflow.app")
            
            # Parse scheduled_date
            if task.get('scheduled_date'):
                dt = datetime.strptime(task['scheduled_date'], '%Y-%m-%d')
                event.add('dtstart', dt.date())
                event.add('dtend', (dt + timedelta(days=1)).date())
            
            if task.get('context'):
                event.add('categories', [task['context']])
            
            if task.get('notes'):
                event.add('description', task['notes'])
            
            event.add('dtstamp', datetime.now(pytz.UTC))
            cal.add_component(event)
    
    # Add project tasks
    if include_projects:
        projects = self.get_projects()
        for project in projects:
            tasks = self.get_project_tasks(project['id'])
            for task in tasks:
                event = Event()
                event.add('summary', f"[{project['title']}] {task['title']}")
                event.add('uid', f"beatflow-project-{task['id']}@beatflow.app")
                
                if task.get('due_date'):
                    dt = datetime.strptime(task['due_date'], '%Y-%m-%d')
                    event.add('dtstart', dt.date())
                    event.add('dtend', (dt + timedelta(days=1)).date())
                
                if task.get('description'):
                    event.add('description', task['description'])
                
                event.add('dtstamp', datetime.now(pytz.UTC))
                cal.add_component(event)
    
    # Write to file
    with open(filepath, 'wb') as f:
        f.write(cal.to_ical())
    
    return True
```

---

## UI Components

### 3. Create `ui/focus_mode.py` - Pomodoro Focus Mode

```python
"""Focus Mode - Distraction-free Pomodoro timer for single task."""

import customtkinter as ctk
from ui.theme import COLORS, SPACING
from core.task_manager import get_task_manager
import threading
import time
from datetime import datetime, timedelta

class FocusMode(ctk.CTkToplevel):
    """Fullscreen focus mode with Pomodoro timer."""
    
    def __init__(self, parent, task: dict, is_daily: bool = True):
        super().__init__(parent)
        self.task = task
        self.is_daily = is_daily
        self.task_manager = get_task_manager()
        
        # Fullscreen setup
        self.attributes('-fullscreen', True)
        self.attributes('-topmost', True)
        self.configure(fg_color=COLORS['bg_darkest'])
        
        # Timer state
        self.duration = 25 * 60  # 25 minutes in seconds
        self.remaining = self.duration
        self.is_running = False
        self.session_id = None
        
        self._build_ui()
        self.bind('<Escape>', self._on_exit)
    
    def _build_ui(self):
        """Build the focus mode UI."""
        # Dim overlay
        overlay = ctk.CTkFrame(self, fg_color=COLORS['bg_darkest'])
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Center container
        container = ctk.CTkFrame(overlay, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Task title
        title_label = ctk.CTkLabel(
            container,
            text=self.task['title'],
            font=ctk.CTkFont(family="Inter", size=32, weight="bold"),
            text_color=COLORS['fg']
        )
        title_label.pack(pady=(0, SPACING['xl']))
        
        # Timer display
        self.timer_label = ctk.CTkLabel(
            container,
            text="25:00",
            font=ctk.CTkFont(family="JetBrains Mono", size=96, weight="bold"),
            text_color=COLORS['accent']
        )
        self.timer_label.pack(pady=SPACING['xl'])
        
        # Progress circle (optional - can use CTkProgressBar)
        self.progress = ctk.CTkProgressBar(
            container,
            width=400,
            height=20,
            progress_color=COLORS['accent'],
            fg_color=COLORS['bg_dark']
        )
        self.progress.set(1.0)
        self.progress.pack(pady=SPACING['lg'])
        
        # Controls
        controls = ctk.CTkFrame(container, fg_color="transparent")
        controls.pack(pady=SPACING['xl'])
        
        self.start_btn = ctk.CTkButton(
            controls,
            text="Start Focus",
            width=200,
            height=50,
            font=ctk.CTkFont(size=16),
            fg_color=COLORS['accent'],
            hover_color="#e55a2b",
            command=self._on_start
        )
        self.start_btn.pack(side="left", padx=SPACING['sm'])
        
        self.pause_btn = ctk.CTkButton(
            controls,
            text="Pause",
            width=200,
            height=50,
            font=ctk.CTkFont(size=16),
            fg_color=COLORS['bg_card'],
            hover_color=COLORS['bg_hover'],
            command=self._on_pause,
            state="disabled"
        )
        self.pause_btn.pack(side="left", padx=SPACING['sm'])
        
        # Exit hint
        exit_label = ctk.CTkLabel(
            container,
            text="Press ESC to exit focus mode",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_dim']
        )
        exit_label.pack(pady=(SPACING['xl'], 0))
    
    def _on_start(self):
        """Start the Pomodoro timer."""
        if not self.is_running:
            self.is_running = True
            self.start_btn.configure(state="disabled")
            self.pause_btn.configure(state="normal")
            
            # Start focus session in database
            self.session_id = self.task_manager.start_focus_session(
                self.task['id'],
                self.is_daily,
                self.duration
            )
            
            # Start timer thread
            self.timer_thread = threading.Thread(target=self._run_timer, daemon=True)
            self.timer_thread.start()
    
    def _on_pause(self):
        """Pause the timer."""
        self.is_running = False
        self.start_btn.configure(state="normal", text="Resume")
        self.pause_btn.configure(state="disabled")
    
    def _run_timer(self):
        """Timer countdown loop."""
        while self.remaining > 0 and self.is_running:
            time.sleep(1)
            self.remaining -= 1
            
            # Update UI (must use after() for thread safety)
            self.after(0, self._update_display)
        
        if self.remaining == 0:
            self.after(0, self._on_timer_complete)
    
    def _update_display(self):
        """Update timer display."""
        minutes = self.remaining // 60
        seconds = self.remaining % 60
        self.timer_label.configure(text=f"{minutes:02d}:{seconds:02d}")
        
        # Update progress bar
        progress = self.remaining / self.duration
        self.progress.set(progress)
    
    def _on_timer_complete(self):
        """Handle timer completion."""
        # Mark session as complete
        if self.session_id:
            self.task_manager.complete_focus_session(self.session_id)
        
        # Show completion message
        self.timer_label.configure(text="Complete!", text_color="#4CAF50")
        self.start_btn.configure(text="Start Break (5 min)", state="normal")
        self.pause_btn.configure(state="disabled")
        
        # Optional: Play sound notification
        # pygame.mixer.Sound('notification.wav').play()
    
    def _on_exit(self, event=None):
        """Exit focus mode."""
        self.is_running = False
        self.destroy()
```

### 4. Create `ui/productivity_dashboard.py` - Charts and Insights

```python
"""Productivity Dashboard - Charts and insights for task completion."""

import customtkinter as ctk
from ui.theme import COLORS, SPACING
from core.task_manager import get_task_manager
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class ProductivityDashboard(ctk.CTkFrame):
    """Dashboard showing productivity charts and insights."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_main'], **kwargs)
        self.task_manager = get_task_manager()
        self._build_ui()
        self.refresh()
    
    def _build_ui(self):
        """Build the dashboard UI."""
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS['bg_dark'], height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header,
            text="Productivity Dashboard",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=COLORS['fg']
        )
        title_label.pack(side="left", padx=SPACING['lg'], pady=SPACING['sm'])
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            header,
            text="↻ Refresh",
            width=100,
            height=32,
            fg_color=COLORS['bg_card'],
            hover_color=COLORS['bg_hover'],
            command=self.refresh
        )
        refresh_btn.pack(side="right", padx=SPACING['md'])
        
        # Content area (scrollable)
        self.content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=SPACING['lg'], pady=SPACING['md'])
    
    def refresh(self):
        """Refresh all charts and insights."""
        # Clear existing content
        for widget in self.content.winfo_children():
            widget.destroy()
        
        # Insights cards
        self._create_insights_cards()
        
        # Charts
        self._create_completion_chart()
        self._create_context_breakdown_chart()
    
    def _create_insights_cards(self):
        """Create insight cards with key metrics."""
        cards_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        cards_frame.pack(fill="x", pady=SPACING['md'])
        
        # Get stats
        most_productive_day = self.task_manager.get_most_productive_day()
        avg_time = self.task_manager.get_average_completion_time()
        
        # Card 1: Most Productive Day
        self._create_insight_card(
            cards_frame,
            "Most Productive Day",
            self._get_day_name(most_productive_day),
            "You complete the most tasks on this day"
        ).pack(side="left", padx=SPACING['sm'], fill="x", expand=True)
        
        # Card 2: Average Completion Time
        self._create_insight_card(
            cards_frame,
            "Avg. Completion Time",
            f"{avg_time:.1f} hours",
            "Average time from creation to completion"
        ).pack(side="left", padx=SPACING['sm'], fill="x", expand=True)
    
    def _create_insight_card(self, parent, title: str, value: str, description: str):
        """Create an insight card widget."""
        card = ctk.CTkFrame(parent, fg_color=COLORS['bg_card'], corner_radius=8)
        
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color=COLORS['fg_secondary'],
            anchor="w"
        )
        title_label.pack(fill="x", padx=SPACING['md'], pady=(SPACING['md'], SPACING['xs']))
        
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS['accent'],
            anchor="w"
        )
        value_label.pack(fill="x", padx=SPACING['md'], pady=SPACING['xs'])
        
        desc_label = ctk.CTkLabel(
            card,
            text=description,
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_dim'],
            anchor="w",
            wraplength=200
        )
        desc_label.pack(fill="x", padx=SPACING['md'], pady=(SPACING['xs'], SPACING['md']))
        
        return card
    
    def _create_completion_chart(self):
        """Create tasks completed over time chart."""
        # Get data for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        stats = self.task_manager.get_completion_stats_by_date(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        # Prepare data
        dates = [datetime.strptime(s['date'], '%Y-%m-%d') for s in stats]
        counts = [s['count'] for s in stats]
        
        # Create matplotlib figure
        fig = Figure(figsize=(10, 4), facecolor=COLORS['bg_card'])
        ax = fig.add_subplot(111)
        
        # Plot
        ax.plot(dates, counts, color=COLORS['accent'], linewidth=2, marker='o')
        ax.fill_between(dates, counts, alpha=0.3, color=COLORS['accent'])
        
        # Styling
        ax.set_facecolor(COLORS['bg_card'])
        ax.set_title('Tasks Completed (Last 30 Days)', color=COLORS['fg'], fontsize=14, pad=15)
        ax.set_xlabel('Date', color=COLORS['fg_secondary'])
        ax.set_ylabel('Tasks Completed', color=COLORS['fg_secondary'])
        ax.tick_params(colors=COLORS['fg_dim'])
        ax.grid(True, alpha=0.1, color=COLORS['fg_dim'])
        
        # Embed in CTk
        chart_frame = ctk.CTkFrame(self.content, fg_color=COLORS['bg_card'])
        chart_frame.pack(fill="x", pady=SPACING['md'])
        
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=SPACING['md'], pady=SPACING['md'])
    
    def _create_context_breakdown_chart(self):
        """Create context breakdown pie/bar chart."""
        stats = self.task_manager.get_completion_stats_by_context()
        
        if not stats:
            return
        
        # Prepare data
        contexts = [s['context'] or 'No Context' for s in stats]
        counts = [s['count'] for s in stats]
        
        # Create matplotlib figure
        fig = Figure(figsize=(10, 4), facecolor=COLORS['bg_card'])
        ax = fig.add_subplot(111)
        
        # Bar chart
        colors = ['#9B59B6', '#3498DB', '#E74C3C', '#95A5A6', '#7F8C8D']
        ax.barh(contexts, counts, color=colors[:len(contexts)])
        
        # Styling
        ax.set_facecolor(COLORS['bg_card'])
        ax.set_title('Tasks by Context', color=COLORS['fg'], fontsize=14, pad=15)
        ax.set_xlabel('Tasks Completed', color=COLORS['fg_secondary'])
        ax.tick_params(colors=COLORS['fg_dim'])
        ax.grid(True, axis='x', alpha=0.1, color=COLORS['fg_dim'])
        
        # Embed in CTk
        chart_frame = ctk.CTkFrame(self.content, fg_color=COLORS['bg_card'])
        chart_frame.pack(fill="x", pady=SPACING['md'])
        
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=SPACING['md'], pady=SPACING['md'])
    
    def _get_day_name(self, day_num: str) -> str:
        """Convert day number to name."""
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        return days[int(day_num)] if day_num else 'Unknown'
```

### 5. Create `ui/calendar_view.py` - Month Calendar Widget

```python
"""Calendar View - Month calendar with task visualization."""

import customtkinter as ctk
from ui.theme import COLORS, SPACING
from core.task_manager import get_task_manager
from datetime import datetime, timedelta
import calendar

class CalendarView(ctk.CTkFrame):
    """Month calendar view showing tasks on dates."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_main'], **kwargs)
        self.task_manager = get_task_manager()
        self.current_date = datetime.now()
        self._build_ui()
        self.refresh()
    
    def _build_ui(self):
        """Build the calendar UI."""
        # Header with month navigation
        header = ctk.CTkFrame(self, fg_color=COLORS['bg_dark'], height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Previous month button
        prev_btn = ctk.CTkButton(
            header,
            text="◀",
            width=40,
            height=32,
            fg_color=COLORS['bg_card'],
            hover_color=COLORS['bg_hover'],
            command=self._prev_month
        )
        prev_btn.pack(side="left", padx=SPACING['md'])
        
        # Month/Year label
        self.month_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=COLORS['fg']
        )
        self.month_label.pack(side="left", padx=SPACING['lg'])
        
        # Next month button
        next_btn = ctk.CTkButton(
            header,
            text="▶",
            width=40,
            height=32,
            fg_color=COLORS['bg_card'],
            hover_color=COLORS['bg_hover'],
            command=self._next_month
        )
        next_btn.pack(side="left")
        
        # Export button
        export_btn = ctk.CTkButton(
            header,
            text="Export to .ics",
            width=120,
            height=32,
            fg_color=COLORS['accent'],
            hover_color="#e55a2b",
            command=self._on_export
        )
        export_btn.pack(side="right", padx=SPACING['md'])
        
        # Calendar grid
        self.calendar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.calendar_frame.pack(fill="both", expand=True, padx=SPACING['lg'], pady=SPACING['md'])
    
    def refresh(self):
        """Refresh calendar display."""
        # Update month label
        self.month_label.configure(
            text=self.current_date.strftime("%B %Y")
        )
        
        # Clear existing calendar
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
        
        # Create calendar grid
        self._create_calendar_grid()
    
    def _create_calendar_grid(self):
        """Create the calendar grid for current month."""
        # Day headers
        days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        for i, day in enumerate(days):
            label = ctk.CTkLabel(
                self.calendar_frame,
                text=day,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS['fg_secondary']
            )
            label.grid(row=0, column=i, padx=2, pady=2, sticky="nsew")
        
        # Get calendar data
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        
        # Create day cells
        for week_num, week in enumerate(cal, start=1):
            for day_num, day in enumerate(week):
                if day == 0:
                    # Empty cell
                    continue
                
                date_obj = datetime(self.current_date.year, self.current_date.month, day)
                self._create_day_cell(week_num, day_num, day, date_obj)
        
        # Configure grid weights
        for i in range(7):
            self.calendar_frame.grid_columnconfigure(i, weight=1)
        for i in range(len(cal) + 1):
            self.calendar_frame.grid_rowconfigure(i, weight=1)
    
    def _create_day_cell(self, row: int, col: int, day: int, date_obj: datetime):
        """Create a single day cell."""
        # Get tasks for this date
        date_str = date_obj.strftime('%Y-%m-%d')
        tasks = self.task_manager.get_daily_tasks(date=date_str)
        
        # Cell frame
        is_today = date_obj.date() == datetime.now().date()
        cell = ctk.CTkFrame(
            self.calendar_frame,
            fg_color=COLORS['accent'] if is_today else COLORS['bg_card'],
            corner_radius=4
        )
        cell.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
        
        # Day number
        day_label = ctk.CTkLabel(
            cell,
            text=str(day),
            font=ctk.CTkFont(size=14, weight="bold" if is_today else "normal"),
            text_color=COLORS['bg_darkest'] if is_today else COLORS['fg']
        )
        day_label.pack(anchor="ne", padx=4, pady=4)
        
        # Task count indicator
        if tasks:
            count_label = ctk.CTkLabel(
                cell,
                text=f"{len(tasks)} tasks",
                font=ctk.CTkFont(size=10),
                text_color=COLORS['bg_darkest'] if is_today else COLORS['fg_secondary']
            )
            count_label.pack(anchor="sw", padx=4, pady=4)
    
    def _prev_month(self):
        """Navigate to previous month."""
        self.current_date = self.current_date.replace(day=1) - timedelta(days=1)
        self.refresh()
    
    def _next_month(self):
        """Navigate to next month."""
        next_month = self.current_date.replace(day=28) + timedelta(days=4)
        self.current_date = next_month.replace(day=1)
        self.refresh()
    
    def _on_export(self):
        """Export tasks to .ics file."""
        from tkinter import filedialog, messagebox
        
        filepath = filedialog.asksaveasfilename(
            title="Export Calendar",
            defaultextension=".ics",
            filetypes=[("iCalendar files", "*.ics"), ("All files", "*.*")],
            initialfile=f"beatflow_tasks_{datetime.now().strftime('%Y%m%d')}.ics"
        )
        
        if filepath:
            success = self.task_manager.export_to_ics(filepath)
            if success:
                messagebox.showinfo("Export Successful", f"Calendar exported to:\n{filepath}")
            else:
                messagebox.showerror("Export Failed", "Failed to export calendar.")
```

### 6. Update `ui/tasks_view.py`

Add tabs for Dashboard and Calendar:

```python
# In _build_ui(), update tab switcher:
self.tab_switcher = ctk.CTkSegmentedButton(
    header,
    values=["Today", "Projects", "Dashboard", "Calendar"],
    command=self._on_tab_change,
    width=400,
    height=32
)

# Create new views:
self.dashboard_view = ProductivityDashboard(self.content_frame)
self.calendar_view = CalendarView(self.content_frame)

# In _on_tab_change(), add cases:
elif value == "Dashboard":
    self.current_tab = "dashboard"
    self.dashboard_view.pack(fill="both", expand=True)
    self.dashboard_view.refresh()
elif value == "Calendar":
    self.current_tab = "calendar"
    self.calendar_view.pack(fill="both", expand=True)
    self.calendar_view.refresh()
```

### 7. Update `ui/today_view.py`

Add Focus Mode button to task rows:

```python
# In _create_task_row(), add focus button:
focus_btn = ctk.CTkButton(
    row,
    text="🎯",
    width=30,
    height=30,
    fg_color="transparent",
    hover_color=COLORS['bg_hover'],
    command=lambda: self._on_focus_task(task)
)
focus_btn.pack(side="right", padx=SPACING['xs'])

def _on_focus_task(self, task: dict):
    """Start focus mode for this task."""
    from ui.focus_mode import FocusMode
    focus_window = FocusMode(self, task, is_daily=True)
```

---

## Verification Checklist

- [ ] matplotlib and icalendar installed successfully
- [ ] Database migration adds new columns
- [ ] Focus Mode opens in fullscreen
- [ ] Pomodoro timer counts down correctly
- [ ] Focus session saves to database
- [ ] Productivity Dashboard shows charts
- [ ] Charts display correctly with matplotlib
- [ ] Calendar view shows current month
- [ ] Tasks appear on correct dates in calendar
- [ ] Export to .ics creates valid calendar file
- [ ] .ics file imports into Google Calendar/Outlook
- [ ] Collaborative task assignment works
- [ ] Assigned tasks show contact name/avatar

---

## Testing Steps

1. **Install Dependencies**: `py -3.12 -m pip install matplotlib icalendar`
2. **Focus Mode**:
   - Go to Today tab → Click 🎯 on a task
   - Verify fullscreen overlay appears
   - Click "Start Focus" → Timer should count down
   - Wait 25 minutes or press ESC to exit
3. **Productivity Dashboard**:
   - Go to Dashboard tab
   - Verify charts render correctly
   - Check insights cards show data
4. **Calendar Integration**:
   - Go to Calendar tab
   - Verify current month displays
   - Navigate months with ◀ ▶ buttons
   - Click "Export to .ics"
   - Import .ics into Google Calendar
5. **Collaborative Tasks**:
   - Go to Projects → Select project
   - Assign task to Network contact
   - Verify assignee shows on task

---

## Files to Create

1. `ui/focus_mode.py` - Pomodoro focus mode
2. `ui/productivity_dashboard.py` - Charts and insights
3. `ui/calendar_view.py` - Month calendar widget

## Files to Modify

1. `core/database.py` - Add columns and focus_sessions table
2. `core/task_manager.py` - Add time tracking, stats, export methods
3. `ui/tasks_view.py` - Add Dashboard and Calendar tabs
4. `ui/today_view.py` - Add Focus Mode button
5. `requirements.txt` - Already updated with matplotlib, icalendar

---

## Notes for Implementation

- **Matplotlib Integration**: Use `FigureCanvasTkAgg` for embedding charts in CustomTkinter
- **Thread Safety**: Use `self.after()` when updating UI from timer thread
- **Calendar Export**: Follow RFC 5545 spec for .ics compatibility
- **Focus Mode**: Keep UI minimal and distraction-free
- **Charts**: Use Beatflow color scheme for consistency
