"""Today View - Daily quick todos list with UX enhancements."""

import os
import customtkinter as ctk
from ui.theme import COLORS, SPACING
from core.task_manager import get_task_manager
from datetime import datetime
from ui.focus_mode import QuickFocusDialog


# Smart placeholder tips that rotate
PLACEHOLDER_TIPS = [
    "What needs to be done today? Press Enter to add...",
    "Try: 'Mix 808 samples'",
    "Try: 'Organize downloads folder'",
    "Try: 'Analyze new samples'",
    "Try: 'Export beat to WAV'",
    "Try: 'Tag kick samples by key'"
]

# Context tag colors
CONTEXT_COLORS = {
    "@Studio": "#9B59B6",    # Purple
    "@Mixing": "#3498DB",    # Blue
    "@Marketing": "#E74C3C", # Red
    "@Admin": "#95A5A6",     # Gray
    "@Other": "#7F8C8D"      # Dark gray
}

# Priority indicator colors
PRIORITY_COLORS = {
    0: COLORS['fg_dim'],    # Normal - gray
    1: "#FFA500",           # High - orange
    2: "#FF4444"            # Urgent - red
}


class TodayView(ctk.CTkFrame):
    """Daily tasks view with quick add input and UX enhancements."""

    def __init__(self, parent, on_navigate_to_folder=None, **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_main'], **kwargs)
        self.task_manager = get_task_manager()
        self.task_widgets = []
        self.focused_task_id = None
        self.placeholder_index = 0
        self.on_navigate_to_folder = on_navigate_to_folder
        self._build_ui()
        self._setup_keyboard_shortcuts()
        self.after(100, self.refresh)
        # Disabled placeholder rotation - was causing input issues
        # self._rotate_placeholder()

    def _build_ui(self):
        """Build the UI."""
        # Header with date and stats
        header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header.pack(fill="x", padx=SPACING['lg'], pady=(SPACING['lg'], SPACING['sm']))
        header.pack_propagate(False)

        # Date label (e.g., "Sunday, January 12")
        today = datetime.now().strftime("%A, %B %d")
        date_label = ctk.CTkLabel(
            header,
            text=today,
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=COLORS['fg']
        )
        date_label.pack(side="left")

        # Focus Mode button
        focus_btn = ctk.CTkButton(
            header,
            text="Focus Mode",
            font=ctk.CTkFont(family="Inter", size=12),
            width=100,
            height=32,
            fg_color=COLORS['accent_secondary'],
            hover_color="#7C3AED",
            corner_radius=6,
            command=self._open_focus_mode
        )
        focus_btn.pack(side="right", padx=(SPACING['sm'], 0))

        # Task count (e.g., "3 of 8 completed")
        self.count_label = ctk.CTkLabel(
            header,
            text="0 tasks",
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=COLORS['fg_secondary']
        )
        self.count_label.pack(side="right", padx=SPACING['sm'])

        # Quick add input
        add_frame = ctk.CTkFrame(self, fg_color="transparent")
        add_frame.pack(fill="x", padx=SPACING['lg'], pady=SPACING['sm'])

        self.add_entry = ctk.CTkEntry(
            add_frame,
            placeholder_text="What needs to be done today? Press Enter to add...",
            height=44,
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color=COLORS['bg_card'],
            text_color="#FFFFFF",
            placeholder_text_color="#888888",
            border_width=1,
            border_color=COLORS['border'],
            corner_radius=8,
            state="normal"
        )
        self.add_entry.pack(fill="x")
        self.add_entry.bind("<Return>", self._on_add_task)

        # Context tag selector
        tags_frame = ctk.CTkFrame(self, fg_color="transparent")
        tags_frame.pack(fill="x", padx=SPACING['lg'], pady=(SPACING['xs'], SPACING['sm']))

        tags_label = ctk.CTkLabel(
            tags_frame,
            text="Tag:",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=COLORS['fg_secondary']
        )
        tags_label.pack(side="left", padx=(0, SPACING['sm']))

        # Store selected context
        self.selected_context = "@Studio"
        self.context_buttons = {}

        for ctx, color in CONTEXT_COLORS.items():
            is_selected = ctx == "@Studio"
            btn = ctk.CTkButton(
                tags_frame,
                text=ctx,
                font=ctk.CTkFont(family="Inter", size=11),
                width=80,
                height=28,
                fg_color=color if is_selected else "transparent",
                hover_color=color,
                text_color="#FFFFFF" if is_selected else COLORS['fg_secondary'],
                border_width=1,
                border_color=color,
                corner_radius=4,
                command=lambda c=ctx: self._on_select_context(c)
            )
            btn.pack(side="left", padx=SPACING['xs'])
            self.context_buttons[ctx] = btn

        # Task list (scrollable)
        self.task_list = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS['bg_hover'],
            scrollbar_button_hover_color=COLORS['accent']
        )
        self.task_list.pack(fill="both", expand=True, padx=SPACING['lg'], pady=SPACING['sm'])

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for the view."""
        # Ctrl+T to focus quick add input - bind to root window
        root = self.winfo_toplevel()
        root.bind("<Control-t>", self._on_quick_add_shortcut)

    def _on_quick_add_shortcut(self, event=None):
        """Global shortcut to focus quick add input."""
        self.add_entry.focus_set()
        return "break"

    def _open_focus_mode(self):
        """Open the focus mode dialog to start a Pomodoro session."""
        QuickFocusDialog(self.winfo_toplevel())

    def _rotate_placeholder(self):
        """Rotate placeholder tips every 5 seconds."""
        if self.add_entry.get() == "":  # Only rotate if input is empty
            self.add_entry.configure(placeholder_text=PLACEHOLDER_TIPS[self.placeholder_index])
        self.placeholder_index = (self.placeholder_index + 1) % len(PLACEHOLDER_TIPS)
        self.after(5000, self._rotate_placeholder)

    def refresh(self):
        """Refresh task list from database."""
        # Clear existing tasks
        for widget in self.task_widgets:
            widget.destroy()
        self.task_widgets = []

        # Get today's tasks
        today_str = datetime.now().strftime("%Y-%m-%d")
        tasks = self.task_manager.get_daily_tasks(date=today_str)

        if not tasks:
            # Show empty state
            empty_frame = ctk.CTkFrame(self.task_list, fg_color="transparent")
            empty_frame.pack(expand=True, pady=SPACING['xl'])
            self.task_widgets.append(empty_frame)

            empty_icon = ctk.CTkLabel(
                empty_frame,
                text="\u2713",
                font=ctk.CTkFont(size=48),
                text_color=COLORS['fg_dim']
            )
            empty_icon.pack(pady=(SPACING['xl'], SPACING['md']))

            empty_msg = ctk.CTkLabel(
                empty_frame,
                text="No tasks for today",
                font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
                text_color=COLORS['fg']
            )
            empty_msg.pack()

            empty_hint = ctk.CTkLabel(
                empty_frame,
                text="Add your first task, like 'Organize sample library'",
                font=ctk.CTkFont(family="Inter", size=13),
                text_color=COLORS['fg_secondary']
            )
            empty_hint.pack(pady=(SPACING['xs'], 0))

            self.count_label.configure(text="0 tasks")
            return

        # Update count
        completed = sum(1 for t in tasks if t['completed'])
        self.count_label.configure(text=f"{completed} of {len(tasks)} completed")

        # Display tasks
        for task in tasks:
            self._create_task_row(task)

    def _create_task_row(self, task: dict):
        """Create a task row widget with context tags and priority."""
        row = ctk.CTkFrame(
            self.task_list,
            fg_color=COLORS['bg_card'],
            corner_radius=8,
            height=56
        )
        row.pack(fill="x", pady=SPACING['xs'])
        row.pack_propagate(False)
        self.task_widgets.append(row)

        # Priority indicator (colored dot)
        priority = task.get('priority', 0)
        priority_dot = ctk.CTkLabel(
            row,
            text="\u25CF",
            font=ctk.CTkFont(size=10),
            text_color=PRIORITY_COLORS.get(priority, COLORS['fg_dim']),
            width=16
        )
        priority_dot.pack(side="left", padx=(SPACING['sm'], 0))

        # Checkbox
        checkbox_var = ctk.BooleanVar(value=task['completed'])
        checkbox = ctk.CTkCheckBox(
            row,
            text="",
            variable=checkbox_var,
            command=lambda t=task, r=row: self._on_toggle_task(t['id'], r),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            checkmark_color="#ffffff",
            width=24,
            height=24
        )
        checkbox.pack(side="left", padx=(SPACING['xs'], SPACING['sm']), pady=SPACING['sm'])

        # Task title
        title_color = COLORS['fg_dim'] if task['completed'] else COLORS['fg']
        title_label = ctk.CTkLabel(
            row,
            text=task['title'],
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=title_color,
            anchor="w"
        )
        title_label.pack(side="left", fill="x", expand=True, pady=SPACING['sm'])

        # Linked entity indicator
        if task.get('linked_entity_type'):
            link_btn = ctk.CTkButton(
                row,
                text="\U0001F517",  # 🔗 Link emoji
                font=ctk.CTkFont(size=14),
                width=30,
                height=30,
                fg_color="transparent",
                hover_color=COLORS['bg_hover'],
                text_color=COLORS['accent'],
                corner_radius=4,
                command=lambda t=task: self._on_navigate_to_linked(t)
            )
            link_btn.pack(side="right", padx=SPACING['xs'])

        # Context badge (if set)
        if task.get('context'):
            context_color = CONTEXT_COLORS.get(task['context'], COLORS['fg_dim'])
            context_label = ctk.CTkLabel(
                row,
                text=task['context'],
                font=ctk.CTkFont(family="Inter", size=10),
                text_color="#ffffff",
                fg_color=context_color,
                corner_radius=4,
                padx=8,
                pady=2
            )
            context_label.pack(side="right", padx=SPACING['xs'])

        # Delete button
        delete_btn = ctk.CTkButton(
            row,
            text="\u2715",
            font=ctk.CTkFont(size=12),
            width=30,
            height=30,
            fg_color="transparent",
            hover_color=COLORS['error'],
            text_color=COLORS['fg_dim'],
            corner_radius=4,
            command=lambda t=task: self._on_delete_task(t['id'])
        )
        delete_btn.pack(side="right", padx=SPACING['sm'])

        # Track focused task on click
        row.bind("<Button-1>", lambda e, t=task: setattr(self, 'focused_task_id', t['id']))

    def _on_navigate_to_linked(self, task: dict):
        """Navigate to linked entity (sample, folder, collection)."""
        entity_type = task.get('linked_entity_type')
        entity_id = task.get('linked_entity_id')

        if not entity_type or not entity_id:
            return

        if entity_type == "sample" and self.on_navigate_to_folder:
            # Navigate to folder containing sample
            folder_path = os.path.dirname(entity_id)
            self.on_navigate_to_folder(folder_path, entity_id)

    def _on_select_context(self, context: str):
        """Handle context tag selection."""
        # Update button styles
        for ctx, btn in self.context_buttons.items():
            color = CONTEXT_COLORS[ctx]
            if ctx == context:
                btn.configure(
                    fg_color=color,
                    text_color="#FFFFFF"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS['fg_secondary']
                )
        self.selected_context = context

    def _on_add_task(self, event=None):
        """Handle adding a new task."""
        title = self.add_entry.get().strip()

        if not title:
            return

        today_str = datetime.now().strftime("%Y-%m-%d")
        self.task_manager.add_daily_task({
            'title': title,
            'scheduled_date': today_str,
            'priority': 0,
            'context': self.selected_context
        })

        self.add_entry.delete(0, 'end')
        self.refresh()

    def _on_toggle_task(self, task_id: int, task_row=None):
        """Handle task completion toggle with animation."""
        new_status = self.task_manager.toggle_daily_task(task_id)

        if new_status and task_row:
            # Animate completion
            self._animate_completion(task_row)
        else:
            self.refresh()

    def _animate_completion(self, task_row):
        """Animate task completion with fade-out and checkmark."""
        # Create checkmark overlay
        checkmark = ctk.CTkLabel(
            task_row,
            text="\u2713",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS['accent']
        )
        checkmark.place(relx=0.5, rely=0.5, anchor="center")

        # Fade out animation
        def fade_step(step=0):
            if step < 8:
                # Gradually darken the row
                alpha = 1.0 - (step * 0.1)
                gray = int(30 + alpha * 10)
                try:
                    task_row.configure(fg_color=f"#{gray:02x}{gray:02x}{gray:02x}")
                except:
                    pass
                self.after(40, lambda: fade_step(step + 1))
            else:
                try:
                    checkmark.destroy()
                except:
                    pass
                self.refresh()

        fade_step()

    def _on_delete_task(self, task_id: int):
        """Handle task deletion."""
        self.task_manager.delete_daily_task(task_id)
        self.refresh()
