"""Focus Mode - Pomodoro timer for deep work sessions."""

import customtkinter as ctk
from ui.theme import COLORS, SPACING
from core.task_manager import get_task_manager
from datetime import datetime
import threading
import time


class FocusModeWindow(ctk.CTkToplevel):
    """Fullscreen Pomodoro focus mode window."""

    def __init__(self, parent, task_id: int, task_title: str, is_daily: bool = True,
                 duration_minutes: int = 25, on_complete=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.task_id = task_id
        self.task_title = task_title
        self.is_daily = is_daily
        self.duration_seconds = duration_minutes * 60
        self.remaining_seconds = self.duration_seconds
        self.on_complete = on_complete
        self.task_manager = get_task_manager()
        self.session_id = None

        self.is_running = False
        self.is_paused = False
        self.timer_thread = None

        self._setup_window()
        self._build_ui()

    def _setup_window(self):
        """Configure the window."""
        self.title("Focus Mode")
        self.configure(fg_color=COLORS['bg_darkest'])

        # Make it fullscreen-like but allow escape to close
        self.geometry("800x600")
        self.resizable(True, True)

        # Center on screen
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 800) // 2
        y = (screen_height - 600) // 2
        self.geometry(f"800x600+{x}+{y}")

        # Bind escape to close
        self.bind("<Escape>", self._on_close)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Grab focus
        self.focus_force()
        self.lift()

    def _build_ui(self):
        """Build the focus mode UI."""
        # Main container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True, fill="both", padx=SPACING['xl'], pady=SPACING['xl'])

        # Header - small label
        header = ctk.CTkLabel(
            container,
            text="FOCUS MODE",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=COLORS['accent']
        )
        header.pack(pady=(SPACING['lg'], SPACING['sm']))

        # Task title
        title_label = ctk.CTkLabel(
            container,
            text=self.task_title,
            font=ctk.CTkFont(family="Inter", size=24, weight="bold"),
            text_color=COLORS['fg'],
            wraplength=600
        )
        title_label.pack(pady=SPACING['md'])

        # Timer display (big centered)
        timer_frame = ctk.CTkFrame(container, fg_color="transparent")
        timer_frame.pack(expand=True, pady=SPACING['xl'])

        self.timer_label = ctk.CTkLabel(
            timer_frame,
            text=self._format_time(self.remaining_seconds),
            font=ctk.CTkFont(family="JetBrains Mono", size=96, weight="bold"),
            text_color=COLORS['fg']
        )
        self.timer_label.pack()

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            timer_frame,
            width=400,
            height=8,
            corner_radius=4,
            fg_color=COLORS['bg_card'],
            progress_color=COLORS['accent']
        )
        self.progress_bar.pack(pady=SPACING['lg'])
        self.progress_bar.set(1.0)

        # Status label
        self.status_label = ctk.CTkLabel(
            timer_frame,
            text="Press Start to begin your focus session",
            font=ctk.CTkFont(family="Inter", size=14),
            text_color=COLORS['fg_secondary']
        )
        self.status_label.pack(pady=SPACING['sm'])

        # Controls
        controls_frame = ctk.CTkFrame(container, fg_color="transparent")
        controls_frame.pack(pady=SPACING['lg'])

        # Start/Pause button
        self.start_btn = ctk.CTkButton(
            controls_frame,
            text="Start",
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            width=140,
            height=50,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            corner_radius=8,
            command=self._toggle_timer
        )
        self.start_btn.pack(side="left", padx=SPACING['md'])

        # Stop button
        self.stop_btn = ctk.CTkButton(
            controls_frame,
            text="Stop",
            font=ctk.CTkFont(family="Inter", size=16),
            width=100,
            height=50,
            fg_color=COLORS['bg_card'],
            hover_color=COLORS['bg_hover'],
            text_color=COLORS['fg_secondary'],
            corner_radius=8,
            command=self._stop_timer
        )
        self.stop_btn.pack(side="left", padx=SPACING['md'])

        # Session info at bottom
        info_frame = ctk.CTkFrame(container, fg_color="transparent")
        info_frame.pack(side="bottom", pady=SPACING['md'])

        self.sessions_label = ctk.CTkLabel(
            info_frame,
            text="",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg_dim']
        )
        self.sessions_label.pack()

        # Load session count
        self._update_session_count()

    def _format_time(self, seconds: int) -> str:
        """Format seconds as MM:SS."""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def _update_session_count(self):
        """Update the session count display."""
        today = datetime.now().strftime('%Y-%m-%d')
        sessions = self.task_manager.get_focus_sessions(date=today)
        completed = sum(1 for s in sessions if s.get('completed'))
        total_minutes = sum(s.get('duration', 0) for s in sessions if s.get('completed')) // 60
        self.sessions_label.configure(
            text=f"Today: {completed} sessions completed ({total_minutes} min focused)"
        )

    def _toggle_timer(self):
        """Start or pause the timer."""
        if not self.is_running:
            self._start_timer()
        elif self.is_paused:
            self._resume_timer()
        else:
            self._pause_timer()

    def _start_timer(self):
        """Start the focus session."""
        # Create session in database
        self.session_id = self.task_manager.start_focus_session(
            self.task_id,
            self.is_daily,
            self.duration_seconds
        )

        self.is_running = True
        self.is_paused = False
        self.start_btn.configure(text="Pause")
        self.status_label.configure(text="Stay focused! You've got this.")

        # Start timer thread
        self.timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self.timer_thread.start()

    def _pause_timer(self):
        """Pause the timer."""
        self.is_paused = True
        self.start_btn.configure(text="Resume")
        self.status_label.configure(text="Paused - Take a quick breath")

    def _resume_timer(self):
        """Resume the timer."""
        self.is_paused = False
        self.start_btn.configure(text="Pause")
        self.status_label.configure(text="Back to focus!")

    def _stop_timer(self):
        """Stop the timer and close."""
        self.is_running = False
        self.is_paused = False
        self._on_close()

    def _run_timer(self):
        """Timer thread - counts down."""
        while self.is_running and self.remaining_seconds > 0:
            if not self.is_paused:
                time.sleep(1)
                self.remaining_seconds -= 1

                # Update UI on main thread
                self.after(0, self._update_timer_display)
            else:
                time.sleep(0.1)  # Check pause status frequently

        # Timer completed
        if self.remaining_seconds <= 0:
            self.after(0, self._on_timer_complete)

    def _update_timer_display(self):
        """Update the timer display."""
        self.timer_label.configure(text=self._format_time(self.remaining_seconds))

        # Update progress
        progress = self.remaining_seconds / self.duration_seconds
        self.progress_bar.set(progress)

        # Change color as time runs low
        if self.remaining_seconds <= 60:
            self.timer_label.configure(text_color=COLORS['error'])
        elif self.remaining_seconds <= 300:  # 5 minutes
            self.timer_label.configure(text_color="#FFA500")  # Orange

    def _on_timer_complete(self):
        """Handle timer completion."""
        self.is_running = False

        # Complete session in database
        if self.session_id:
            self.task_manager.complete_focus_session(self.session_id)

        # Update UI
        self.timer_label.configure(
            text="DONE!",
            text_color=COLORS['success']
        )
        self.status_label.configure(
            text="Great work! Take a 5-minute break.",
            text_color=COLORS['success']
        )
        self.start_btn.configure(text="Close", command=self._on_close)
        self.progress_bar.set(0)

        # Update session count
        self._update_session_count()

        # Callback
        if self.on_complete:
            self.on_complete()

    def _on_close(self, event=None):
        """Handle window close."""
        self.is_running = False
        self.destroy()


class FocusModeButton(ctk.CTkFrame):
    """Compact focus mode trigger button for task rows."""

    def __init__(self, parent, task_id: int, task_title: str, is_daily: bool = True,
                 on_session_complete=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.task_id = task_id
        self.task_title = task_title
        self.is_daily = is_daily
        self.on_session_complete = on_session_complete

        # Focus button with timer icon
        self.btn = ctk.CTkButton(
            self,
            text="25m",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            width=40,
            height=24,
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            text_color=COLORS['fg_dim'],
            border_width=1,
            border_color=COLORS['border'],
            corner_radius=4,
            command=self._open_focus_mode
        )
        self.btn.pack()

    def _open_focus_mode(self):
        """Open focus mode window for this task."""
        window = FocusModeWindow(
            self.winfo_toplevel(),
            self.task_id,
            self.task_title,
            self.is_daily,
            duration_minutes=25,
            on_complete=self.on_session_complete
        )


class QuickFocusDialog(ctk.CTkToplevel):
    """Quick dialog to select task and start focus mode."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.task_manager = get_task_manager()
        self.selected_task = None

        self._setup_window()
        self._build_ui()
        self._load_tasks()

    def _setup_window(self):
        """Configure the dialog."""
        self.title("Start Focus Session")
        self.configure(fg_color=COLORS['bg_main'])
        self.geometry("420x520")
        self.minsize(350, 400)
        self.resizable(True, True)

        # Center on screen
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 420) // 2
        y = (screen_height - 520) // 2
        self.geometry(f"420x520+{x}+{y}")

        self.grab_set()
        self.focus_force()

    def _build_ui(self):
        """Build the dialog UI with grid layout."""
        # Grid layout for proper expansion
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header (row 0)
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=SPACING['lg'], pady=(SPACING['lg'], SPACING['sm']))

        header = ctk.CTkLabel(
            header_frame,
            text="Select a task to focus on",
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            text_color=COLORS['fg']
        )
        header.pack(anchor="w")

        # Duration selector
        duration_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        duration_frame.pack(fill="x", pady=(SPACING['sm'], 0))

        ctk.CTkLabel(
            duration_frame,
            text="Duration:",
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=COLORS['fg_secondary']
        ).pack(side="left")

        self.duration_var = ctk.StringVar(value="25")
        for mins in ["15", "25", "45", "60"]:
            btn = ctk.CTkButton(
                duration_frame,
                text=f"{mins}m",
                font=ctk.CTkFont(family="Inter", size=12),
                width=50,
                height=28,
                fg_color=COLORS['accent'] if mins == "25" else COLORS['bg_card'],
                hover_color=COLORS['accent_hover'],
                corner_radius=4,
                command=lambda m=mins: self._select_duration(m)
            )
            btn.pack(side="left", padx=SPACING['xs'])

        # Task list - scrollable (row 1, expands)
        list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS['bg_card'],
            corner_radius=8,
            scrollbar_button_color=COLORS['bg_hover']
        )
        list_frame.grid(row=1, column=0, sticky="nsew", padx=SPACING['lg'], pady=SPACING['sm'])
        self.task_list_frame = list_frame

        # Start button (row 2, fixed at bottom)
        self.start_btn = ctk.CTkButton(
            self,
            text="Start Focus Session",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            height=44,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            corner_radius=8,
            state="disabled",
            command=self._start_session
        )
        self.start_btn.grid(row=2, column=0, sticky="ew", padx=SPACING['lg'], pady=SPACING['lg'])

    def _select_duration(self, mins: str):
        """Update selected duration."""
        self.duration_var.set(mins)
        # Update button states (visual feedback)
        for child in self.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                for btn in child.winfo_children():
                    if isinstance(btn, ctk.CTkButton) and btn.cget("text").endswith("m"):
                        is_selected = btn.cget("text") == f"{mins}m"
                        btn.configure(
                            fg_color=COLORS['accent'] if is_selected else COLORS['bg_card']
                        )

    def _load_tasks(self):
        """Load today's uncompleted tasks."""
        today = datetime.now().strftime('%Y-%m-%d')
        tasks = self.task_manager.get_daily_tasks(today)
        uncompleted = [t for t in tasks if not t.get('completed')]

        if not uncompleted:
            label = ctk.CTkLabel(
                self.task_list_frame,
                text="No tasks for today.\nAdd tasks first!",
                font=ctk.CTkFont(family="Inter", size=13),
                text_color=COLORS['fg_secondary']
            )
            label.pack(pady=SPACING['xl'])
            return

        for task in uncompleted:
            self._add_task_row(task)

    def _add_task_row(self, task: dict):
        """Add a task selection row."""
        row = ctk.CTkFrame(self.task_list_frame, fg_color="transparent", height=40)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        # Radio-style button
        btn = ctk.CTkButton(
            row,
            text=task['title'],
            font=ctk.CTkFont(family="Inter", size=13),
            height=36,
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            text_color=COLORS['fg'],
            anchor="w",
            corner_radius=4,
            command=lambda t=task: self._select_task(t)
        )
        btn.pack(fill="x", padx=SPACING['xs'])
        btn.task_data = task

    def _select_task(self, task: dict):
        """Select a task."""
        self.selected_task = task
        self.start_btn.configure(state="normal")

        # Update visual selection
        for child in self.task_list_frame.winfo_children():
            for btn in child.winfo_children():
                if isinstance(btn, ctk.CTkButton) and hasattr(btn, 'task_data'):
                    is_selected = btn.task_data['id'] == task['id']
                    btn.configure(
                        fg_color=COLORS['accent'] if is_selected else "transparent",
                        text_color=COLORS['fg'] if is_selected else COLORS['fg']
                    )

    def _start_session(self):
        """Start focus session with selected task."""
        if not self.selected_task:
            return

        duration = int(self.duration_var.get())

        # Close this dialog
        self.destroy()

        # Open focus mode window
        FocusModeWindow(
            self.master,
            self.selected_task['id'],
            self.selected_task['title'],
            is_daily=True,
            duration_minutes=duration
        )
