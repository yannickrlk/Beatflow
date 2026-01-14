"""Projects View - Project management with list/Kanban toggle and template selection."""

import json
import customtkinter as ctk
from ui.theme import COLORS, SPACING
from core.task_manager import get_task_manager


class ProjectTemplateDialog(ctk.CTkToplevel):
    """Dialog for selecting project template or creating blank project."""

    def __init__(self, parent, task_manager):
        super().__init__(parent)
        self.task_manager = task_manager
        self.selected_template = None
        self.project_title = None
        self.create_blank = False

        self.title("New Project")
        self.geometry("500x580")
        self.minsize(420, 450)
        self.resizable(True, True)

        # Configure colors
        self.configure(fg_color=COLORS['bg_main'])

        # Center on parent
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        """Build the dialog UI with grid layout."""
        # Grid layout for proper expansion
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header (row 0)
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=SPACING['lg'], pady=(SPACING['lg'], SPACING['sm']))

        header_label = ctk.CTkLabel(
            header_frame,
            text="Create New Project",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=COLORS['fg']
        )
        header_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Choose a template to get started quickly",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg_secondary']
        )
        subtitle_label.pack(anchor="w", pady=(SPACING['xs'], 0))

        # Templates scrollable list (row 1, expands)
        templates_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS['bg_card'],
            corner_radius=8,
            scrollbar_button_color=COLORS['bg_hover']
        )
        templates_frame.grid(row=1, column=0, sticky="nsew", padx=SPACING['lg'], pady=SPACING['sm'])

        # Get templates
        templates = self.task_manager.get_project_templates()

        for template in templates:
            self._create_template_card(templates_frame, template)

        # Bottom buttons (row 2, fixed)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=SPACING['lg'], pady=SPACING['md'])

        blank_btn = ctk.CTkButton(
            btn_frame,
            text="Start Blank Project",
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['bg_card'],
            text_color=COLORS['fg'],
            height=40,
            corner_radius=6,
            command=self._on_blank_project
        )
        blank_btn.pack(fill="x", pady=(0, SPACING['sm']))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            text_color=COLORS['fg_secondary'],
            height=36,
            corner_radius=4,
            command=self.destroy
        )
        cancel_btn.pack(fill="x")

    def _create_template_card(self, parent, template):
        """Create a clickable template card."""
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS['bg_card'],
            corner_radius=8,
            cursor="hand2"
        )
        card.pack(fill="x", pady=SPACING['xs'])

        # Template name
        name_label = ctk.CTkLabel(
            card,
            text=template['name'],
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=COLORS['fg'],
            anchor="w"
        )
        name_label.pack(fill="x", padx=SPACING['md'], pady=(SPACING['sm'], SPACING['xs']))

        # Description
        desc_label = ctk.CTkLabel(
            card,
            text=template['description'],
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=COLORS['fg_secondary'],
            anchor="w"
        )
        desc_label.pack(fill="x", padx=SPACING['md'], pady=(0, SPACING['xs']))

        # Task count
        tasks = template.get('tasks', [])
        count_label = ctk.CTkLabel(
            card,
            text=f"{len(tasks)} tasks",
            font=ctk.CTkFont(family="Inter", size=10),
            text_color=COLORS['fg_dim']
        )
        count_label.pack(anchor="w", padx=SPACING['md'], pady=(0, SPACING['sm']))

        # Click handler for entire card
        def on_click(event=None):
            self._on_select_template(template)

        card.bind("<Button-1>", on_click)
        name_label.bind("<Button-1>", on_click)
        desc_label.bind("<Button-1>", on_click)
        count_label.bind("<Button-1>", on_click)

        # Hover effects
        def on_enter(event=None):
            card.configure(fg_color=COLORS['bg_hover'])

        def on_leave(event=None):
            card.configure(fg_color=COLORS['bg_card'])

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

    def _on_select_template(self, template):
        """Handle template selection."""
        # Ask for project title
        title_dialog = ctk.CTkInputDialog(
            text=f"Enter project title:",
            title=f"New {template['name']} Project"
        )
        title = title_dialog.get_input()

        if title and title.strip():
            self.selected_template = template
            self.project_title = title.strip()
            self.destroy()

    def _on_blank_project(self):
        """Create blank project."""
        # Ask for project title
        title_dialog = ctk.CTkInputDialog(
            text="Enter project title:",
            title="New Blank Project"
        )
        title = title_dialog.get_input()

        if title and title.strip():
            self.create_blank = True
            self.project_title = title.strip()
            self.destroy()


class ProjectsView(ctk.CTkFrame):
    """Projects view with list and Kanban modes."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_main'], **kwargs)
        self.task_manager = get_task_manager()
        self.view_mode = "list"  # list or kanban
        self.project_widgets = []
        self._build_ui()
        self.after(100, self.refresh)

    def _build_ui(self):
        """Build the UI."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=56)
        header.pack(fill="x", padx=SPACING['lg'], pady=(SPACING['md'], 0))
        header.pack_propagate(False)

        # View toggle (List / Kanban)
        self.view_toggle = ctk.CTkSegmentedButton(
            header,
            values=["List", "Kanban"],
            command=self._on_view_toggle,
            font=ctk.CTkFont(family="Inter", size=11),
            fg_color=COLORS['bg_hover'],
            selected_color=COLORS['accent'],
            selected_hover_color=COLORS['accent_hover'],
            unselected_color=COLORS['bg_hover'],
            unselected_hover_color=COLORS['bg_card'],
            width=140,
            height=32,
            corner_radius=4,
            dynamic_resizing=False
        )
        self.view_toggle.set("List")
        self.view_toggle.pack(side="left")

        # + New Project button
        new_btn = ctk.CTkButton(
            header,
            text="+ New Project",
            font=ctk.CTkFont(family="Inter", size=12),
            width=130,
            height=36,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            corner_radius=4,
            command=self._on_new_project
        )
        new_btn.pack(side="right")

        # Project count
        self.count_label = ctk.CTkLabel(
            header,
            text="0 projects",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS['fg_dim']
        )
        self.count_label.pack(side="right", padx=SPACING['md'])

        # Content area
        self.content_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS['bg_hover'],
            scrollbar_button_hover_color=COLORS['accent']
        )
        self.content_frame.pack(fill="both", expand=True, padx=SPACING['lg'], pady=SPACING['md'])

    def refresh(self):
        """Refresh projects list."""
        # Clear content
        for widget in self.project_widgets:
            widget.destroy()
        self.project_widgets = []

        # Get projects
        projects = self.task_manager.get_projects(status='active')

        # Update count
        self.count_label.configure(text=f"{len(projects)} project{'s' if len(projects) != 1 else ''}")

        if not projects:
            # Show empty state
            empty_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            empty_frame.pack(expand=True, pady=SPACING['xl'])
            self.project_widgets.append(empty_frame)

            empty_icon = ctk.CTkLabel(
                empty_frame,
                text="\U0001f4cb",
                font=ctk.CTkFont(size=48),
                text_color=COLORS['fg_dim']
            )
            empty_icon.pack(pady=(SPACING['xl'], SPACING['md']))

            empty_msg = ctk.CTkLabel(
                empty_frame,
                text="No Projects Yet",
                font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
                text_color=COLORS['fg']
            )
            empty_msg.pack()

            empty_hint = ctk.CTkLabel(
                empty_frame,
                text="Create a project to track your albums,\nsample packs, or client work",
                font=ctk.CTkFont(family="Inter", size=13),
                text_color=COLORS['fg_secondary'],
                justify="center"
            )
            empty_hint.pack(pady=(SPACING['xs'], SPACING['lg']))

            empty_btn = ctk.CTkButton(
                empty_frame,
                text="+ Create Project",
                font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
                fg_color=COLORS['accent'],
                hover_color=COLORS['accent_hover'],
                height=44,
                width=160,
                corner_radius=8,
                command=self._on_new_project
            )
            empty_btn.pack()
            return

        # Display projects based on view mode
        if self.view_mode == "list":
            self._show_list_view(projects)
        else:
            self._show_kanban_view(projects)

    def _show_list_view(self, projects):
        """Display projects in list view."""
        for project in projects:
            self._create_project_card(project)

    def _create_project_card(self, project: dict):
        """Create a project card widget."""
        card = ctk.CTkFrame(
            self.content_frame,
            fg_color=COLORS['bg_card'],
            corner_radius=8
        )
        card.pack(fill="x", pady=SPACING['xs'])
        self.project_widgets.append(card)

        # Color indicator bar on left
        color_bar = ctk.CTkFrame(
            card,
            width=4,
            fg_color=project.get('color', '#FF6B35'),
            corner_radius=2
        )
        color_bar.pack(side="left", fill="y", padx=(0, SPACING['sm']), pady=SPACING['sm'])

        # Content area
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=SPACING['sm'], pady=SPACING['md'])

        # Project title
        title_label = ctk.CTkLabel(
            content,
            text=project['title'],
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            text_color=COLORS['fg'],
            anchor="w"
        )
        title_label.pack(fill="x")

        # Description (if exists)
        if project.get('description'):
            desc_text = project['description'][:80] + "..." if len(project['description']) > 80 else project['description']
            desc_label = ctk.CTkLabel(
                content,
                text=desc_text,
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=COLORS['fg_secondary'],
                anchor="w"
            )
            desc_label.pack(fill="x", pady=(SPACING['xs'], 0))

        # Progress row
        progress_frame = ctk.CTkFrame(content, fg_color="transparent")
        progress_frame.pack(fill="x", pady=(SPACING['sm'], 0))

        # Task progress
        total = project.get('task_count', 0)
        completed = project.get('tasks_completed', 0)
        progress_text = f"{completed}/{total} tasks" if total > 0 else "No tasks yet"

        progress_label = ctk.CTkLabel(
            progress_frame,
            text=progress_text,
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=COLORS['fg_dim']
        )
        progress_label.pack(side="left")

        # Progress bar (if has tasks)
        if total > 0:
            progress_pct = completed / total
            progress_bar = ctk.CTkProgressBar(
                progress_frame,
                width=100,
                height=6,
                fg_color=COLORS['bg_hover'],
                progress_color=COLORS['accent'],
                corner_radius=3
            )
            progress_bar.set(progress_pct)
            progress_bar.pack(side="left", padx=SPACING['sm'])

        # Deadline badge (if exists)
        if project.get('deadline'):
            deadline_label = ctk.CTkLabel(
                progress_frame,
                text=f"Due: {project['deadline']}",
                font=ctk.CTkFont(family="Inter", size=10),
                text_color=COLORS['fg_dim'],
                fg_color=COLORS['bg_hover'],
                corner_radius=4,
                padx=6,
                pady=2
            )
            deadline_label.pack(side="right")

        # Action buttons on right
        actions_frame = ctk.CTkFrame(card, fg_color="transparent")
        actions_frame.pack(side="right", padx=SPACING['md'], pady=SPACING['md'])

        # Delete button
        delete_btn = ctk.CTkButton(
            actions_frame,
            text="\u2715",
            font=ctk.CTkFont(size=12),
            width=30,
            height=30,
            fg_color="transparent",
            hover_color=COLORS['error'],
            text_color=COLORS['fg_dim'],
            corner_radius=4,
            command=lambda p=project: self._on_delete_project(p['id'])
        )
        delete_btn.pack()

    def _show_kanban_view(self, projects):
        """Display Kanban board with columns."""
        # Create horizontal container for columns
        kanban_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        kanban_frame.pack(fill="both", expand=True)
        self.project_widgets.append(kanban_frame)

        # Get all project tasks grouped by status
        columns = {
            'todo': {'title': 'To Do', 'tasks': []},
            'in_progress': {'title': 'In Progress', 'tasks': []},
            'done': {'title': 'Done', 'tasks': []}
        }

        for project in projects:
            tasks = self.task_manager.get_project_tasks(project['id'])
            for task in tasks:
                task['project_title'] = project['title']
                task['project_color'] = project.get('color', '#FF6B35')
                status = task.get('status', 'todo')
                if status in columns:
                    columns[status]['tasks'].append(task)

        # Create columns
        for col_id, col_data in columns.items():
            col_frame = ctk.CTkFrame(kanban_frame, fg_color=COLORS['bg_dark'], corner_radius=8)
            col_frame.pack(side="left", fill="both", expand=True, padx=SPACING['xs'])

            # Column header
            header = ctk.CTkLabel(
                col_frame,
                text=f"{col_data['title']} ({len(col_data['tasks'])})",
                font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
                text_color=COLORS['fg']
            )
            header.pack(pady=SPACING['sm'])

            # Tasks in column
            for task in col_data['tasks']:
                task_card = ctk.CTkFrame(col_frame, fg_color=COLORS['bg_card'], corner_radius=6)
                task_card.pack(fill="x", padx=SPACING['sm'], pady=SPACING['xs'])

                # Project indicator
                proj_label = ctk.CTkLabel(
                    task_card,
                    text=task['project_title'],
                    font=ctk.CTkFont(family="Inter", size=9),
                    text_color=task['project_color']
                )
                proj_label.pack(anchor="w", padx=SPACING['sm'], pady=(SPACING['xs'], 0))

                # Task title
                title_label = ctk.CTkLabel(
                    task_card,
                    text=task['title'],
                    font=ctk.CTkFont(family="Inter", size=11),
                    text_color=COLORS['fg'],
                    anchor="w",
                    wraplength=150
                )
                title_label.pack(fill="x", padx=SPACING['sm'], pady=(0, SPACING['sm']))

    def _on_view_toggle(self, value):
        """Handle view mode toggle."""
        self.view_mode = value.lower()
        self.refresh()

    def _on_new_project(self):
        """Handle new project creation with template selection."""
        dialog = ProjectTemplateDialog(self, self.task_manager)
        self.wait_window(dialog)

        if dialog.selected_template and dialog.project_title:
            # Create project from template
            self.task_manager.create_project_from_template(
                dialog.selected_template['id'],
                dialog.project_title
            )
            self.refresh()
        elif dialog.create_blank and dialog.project_title:
            # Create blank project
            self.task_manager.create_project({
                'title': dialog.project_title,
                'description': '',
                'status': 'active'
            })
            self.refresh()

    def _on_delete_project(self, project_id: int):
        """Handle project deletion."""
        self.task_manager.delete_project(project_id)
        self.refresh()
