"""Task Manager for ProducerOS - Daily todos and project management."""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from core.database import get_database


# Default project templates
DEFAULT_TEMPLATES = [
    {
        "name": "Album Release",
        "description": "Complete workflow for releasing an album",
        "tasks": [
            {"title": "Record all tracks", "order_index": 0, "due_days": 30},
            {"title": "Mix tracks", "order_index": 1, "due_days": 45},
            {"title": "Master album", "order_index": 2, "due_days": 60},
            {"title": "Create album artwork", "order_index": 3, "due_days": 65},
            {"title": "Upload to distributor", "order_index": 4, "due_days": 75},
            {"title": "Marketing campaign", "order_index": 5, "due_days": 90}
        ]
    },
    {
        "name": "Sample Pack",
        "description": "Create and release a sample pack",
        "tasks": [
            {"title": "Record samples", "order_index": 0, "due_days": 7},
            {"title": "Process and edit", "order_index": 1, "due_days": 10},
            {"title": "Tag and organize", "order_index": 2, "due_days": 12},
            {"title": "Create demo track", "order_index": 3, "due_days": 14},
            {"title": "Export to ZIP", "order_index": 4, "due_days": 14}
        ]
    },
    {
        "name": "Client Beat",
        "description": "Custom beat for a client",
        "tasks": [
            {"title": "Initial meeting with client", "order_index": 0, "due_days": 1},
            {"title": "Create beat draft", "order_index": 1, "due_days": 3},
            {"title": "Client revisions", "order_index": 2, "due_days": 5},
            {"title": "Final delivery", "order_index": 3, "due_days": 7}
        ]
    }
]


class TaskManager:
    """Manages daily tasks and projects for music producer workflows."""

    def __init__(self):
        self.db = get_database()
        self._init_default_templates()

    # ===== DAILY TASKS =====

    def add_daily_task(self, data: Dict) -> int:
        """
        Add a new daily task.

        Args:
            data: Dict with task fields (title, priority, context, time_estimate, notes,
                  scheduled_date, start_time, end_time, all_day).

        Returns:
            The ID of the created task.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO daily_tasks (title, priority, context, time_estimate, notes,
                                    scheduled_date, start_time, end_time, all_day)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('title', ''),
            data.get('priority', 0),
            data.get('context', '@Studio'),
            data.get('time_estimate'),
            data.get('notes', ''),
            data.get('scheduled_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('start_time'),
            data.get('end_time'),
            1 if data.get('all_day', True) else 0
        ))
        conn.commit()
        return cursor.lastrowid

    def get_daily_tasks(self, date: str = None, completed: bool = None) -> List[Dict]:
        """
        Get daily tasks, optionally filtered by date and completion status.

        Args:
            date: Filter by scheduled_date (YYYY-MM-DD format).
            completed: Filter by completion status (True/False/None for all).

        Returns:
            List of task dicts.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM daily_tasks WHERE 1=1'
        params = []

        if date:
            query += ' AND scheduled_date = ?'
            params.append(date)

        if completed is not None:
            query += ' AND completed = ?'
            params.append(1 if completed else 0)

        query += ' ORDER BY completed ASC, priority DESC, created_at ASC'

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_tasks_for_month(self, year: int, month: int) -> Dict[str, List[Dict]]:
        """
        Get all tasks for a month grouped by date (single query for performance).

        Args:
            year: The year (e.g., 2026).
            month: The month (1-12).

        Returns:
            Dict mapping date strings to lists of task dicts.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # Query all tasks for the month
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year}-12-31"
        else:
            end_date = f"{year}-{month + 1:02d}-01"

        query = '''
            SELECT * FROM daily_tasks
            WHERE scheduled_date >= ? AND scheduled_date < ?
            ORDER BY scheduled_date, completed ASC, priority DESC
        '''
        cursor.execute(query, (start_date, end_date))

        # Group by date
        result = {}
        for row in cursor.fetchall():
            task = dict(row)
            date = task.get('scheduled_date')
            if date:
                if date not in result:
                    result[date] = []
                result[date].append(task)

        return result

    def toggle_daily_task(self, task_id: int) -> bool:
        """
        Toggle task completion status.

        Args:
            task_id: The task's ID.

        Returns:
            New completion status (True if now completed).
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # Get current status
        cursor.execute('SELECT completed FROM daily_tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if not row:
            return False

        new_status = not row[0]
        completed_at = datetime.now().isoformat() if new_status else None

        cursor.execute('''
            UPDATE daily_tasks
            SET completed = ?, completed_at = ?
            WHERE id = ?
        ''', (new_status, completed_at, task_id))
        conn.commit()
        return new_status

    def update_daily_task(self, task_id: int, data: Dict) -> bool:
        """
        Update a daily task.

        Args:
            task_id: The task's ID.
            data: Dict with fields to update.

        Returns:
            True if updated, False otherwise.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        fields = ['title', 'priority', 'context', 'time_estimate', 'notes', 'scheduled_date']
        updates = []
        values = []

        for field in fields:
            if field in data:
                updates.append(f'{field} = ?')
                values.append(data[field])

        if not updates:
            return False

        values.append(task_id)
        query = f'UPDATE daily_tasks SET {", ".join(updates)} WHERE id = ?'
        cursor.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0

    def delete_daily_task(self, task_id: int) -> bool:
        """
        Delete a daily task.

        Args:
            task_id: The task's ID.

        Returns:
            True if deleted, False otherwise.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM daily_tasks WHERE id = ?', (task_id,))
        conn.commit()
        return cursor.rowcount > 0

    # ===== PROJECTS =====

    def create_project(self, data: Dict) -> int:
        """
        Create a new project.

        Args:
            data: Dict with project fields (title, description, deadline, color, status).

        Returns:
            The ID of the created project.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO projects (title, description, deadline, color, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data.get('title', ''),
            data.get('description', ''),
            data.get('deadline'),
            data.get('color', '#FF6B35'),
            data.get('status', 'active')
        ))
        conn.commit()
        return cursor.lastrowid

    def get_projects(self, status: str = None) -> List[Dict]:
        """
        Get all projects, optionally filtered by status.

        Args:
            status: Filter by status ('active', 'on_hold', 'completed', 'archived').

        Returns:
            List of project dicts with task counts.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        if status:
            cursor.execute('SELECT * FROM projects WHERE status = ? ORDER BY created_at DESC', (status,))
        else:
            cursor.execute('SELECT * FROM projects ORDER BY created_at DESC')

        projects = [dict(row) for row in cursor.fetchall()]

        # Add task counts for each project
        for project in projects:
            cursor.execute('''
                SELECT COUNT(*) as total, SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed
                FROM project_tasks WHERE project_id = ?
            ''', (project['id'],))
            counts = cursor.fetchone()
            project['task_count'] = counts[0] or 0
            project['tasks_completed'] = counts[1] or 0

        return projects

    def get_project(self, project_id: int) -> Optional[Dict]:
        """
        Get a project by ID.

        Args:
            project_id: The project's ID.

        Returns:
            Project dict or None if not found.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_project(self, project_id: int, data: Dict) -> bool:
        """
        Update project details.

        Args:
            project_id: The project's ID.
            data: Dict with fields to update.

        Returns:
            True if updated, False otherwise.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        fields = ['title', 'description', 'deadline', 'color', 'status']
        updates = []
        values = []

        for field in fields:
            if field in data:
                updates.append(f'{field} = ?')
                values.append(data[field])

        if not updates:
            return False

        values.append(project_id)
        query = f'UPDATE projects SET {", ".join(updates)} WHERE id = ?'
        cursor.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0

    def delete_project(self, project_id: int) -> bool:
        """
        Delete project and all its tasks.

        Args:
            project_id: The project's ID.

        Returns:
            True if deleted, False otherwise.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        # Delete project tasks first (if CASCADE not working)
        cursor.execute('DELETE FROM project_tasks WHERE project_id = ?', (project_id,))
        cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        conn.commit()
        return cursor.rowcount > 0

    def archive_project(self, project_id: int) -> bool:
        """
        Archive a completed project.

        Args:
            project_id: The project's ID.

        Returns:
            True if archived, False otherwise.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE projects SET status = 'archived', completed_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), project_id))
        conn.commit()
        return cursor.rowcount > 0

    # ===== PROJECT TASKS =====

    def add_project_task(self, project_id: int, data: Dict) -> int:
        """
        Add a task to a project.

        Args:
            project_id: The project's ID.
            data: Dict with task fields.

        Returns:
            The ID of the created task.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # Get next order_index
        cursor.execute('SELECT MAX(order_index) FROM project_tasks WHERE project_id = ?', (project_id,))
        max_order = cursor.fetchone()[0] or 0

        cursor.execute('''
            INSERT INTO project_tasks (project_id, title, description, due_date, priority, status, order_index)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            project_id,
            data.get('title', ''),
            data.get('description', ''),
            data.get('due_date'),
            data.get('priority', 0),
            data.get('status', 'todo'),
            max_order + 1
        ))
        conn.commit()
        return cursor.lastrowid

    def get_project_tasks(self, project_id: int) -> List[Dict]:
        """
        Get all tasks for a project, ordered by order_index.

        Args:
            project_id: The project's ID.

        Returns:
            List of task dicts.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM project_tasks
            WHERE project_id = ?
            ORDER BY order_index, created_at
        ''', (project_id,))
        return [dict(row) for row in cursor.fetchall()]

    def toggle_project_task(self, task_id: int) -> bool:
        """
        Toggle project task completion.

        Args:
            task_id: The task's ID.

        Returns:
            New completion status.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT completed FROM project_tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if not row:
            return False

        new_status = not row[0]
        completed_at = datetime.now().isoformat() if new_status else None
        new_status_str = 'done' if new_status else 'todo'

        cursor.execute('''
            UPDATE project_tasks
            SET completed = ?, completed_at = ?, status = ?
            WHERE id = ?
        ''', (new_status, completed_at, new_status_str, task_id))
        conn.commit()
        return new_status

    def update_task_status(self, task_id: int, status: str) -> bool:
        """
        Update task status (todo, in_progress, done).

        Args:
            task_id: The task's ID.
            status: New status.

        Returns:
            True if updated, False otherwise.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        completed = status == 'done'
        completed_at = datetime.now().isoformat() if completed else None

        cursor.execute('''
            UPDATE project_tasks
            SET status = ?, completed = ?, completed_at = ?
            WHERE id = ?
        ''', (status, completed, completed_at, task_id))
        conn.commit()
        return cursor.rowcount > 0

    def delete_project_task(self, task_id: int) -> bool:
        """
        Delete a project task.

        Args:
            task_id: The task's ID.

        Returns:
            True if deleted, False otherwise.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM project_tasks WHERE id = ?', (task_id,))
        conn.commit()
        return cursor.rowcount > 0

    # ===== STATISTICS =====

    def get_completion_stats(self) -> Dict:
        """
        Get overall completion statistics.

        Returns:
            Dict with stats (daily_total, daily_completed, projects_active, etc.)
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        today = datetime.now().strftime('%Y-%m-%d')

        # Daily task stats for today
        cursor.execute('''
            SELECT COUNT(*) as total, SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed
            FROM daily_tasks WHERE scheduled_date = ?
        ''', (today,))
        daily = cursor.fetchone()

        # Project stats
        cursor.execute('SELECT COUNT(*) FROM projects WHERE status = ?', ('active',))
        active_projects = cursor.fetchone()[0]

        # Overdue tasks
        cursor.execute('''
            SELECT COUNT(*) FROM project_tasks
            WHERE due_date < ? AND completed = 0 AND due_date IS NOT NULL
        ''', (today,))
        overdue = cursor.fetchone()[0]

        return {
            'daily_total': daily[0] or 0,
            'daily_completed': daily[1] or 0,
            'active_projects': active_projects,
            'overdue_tasks': overdue
        }

    def get_overdue_tasks(self) -> List[Dict]:
        """
        Get all overdue tasks (past due_date, not completed).

        Returns:
            List of overdue task dicts.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT pt.*, p.title as project_title
            FROM project_tasks pt
            JOIN projects p ON pt.project_id = p.id
            WHERE pt.due_date < ? AND pt.completed = 0 AND pt.due_date IS NOT NULL
            ORDER BY pt.due_date
        ''', (today,))
        return [dict(row) for row in cursor.fetchall()]

    # ===== SAMPLE LINKING =====

    def link_task_to_entity(self, task_id: int, entity_type: str, entity_id: str, is_daily: bool = True) -> bool:
        """
        Link a task to a ProducerOS entity (sample, folder, collection).

        Args:
            task_id: The task's ID.
            entity_type: Type of entity ('sample', 'folder', 'collection').
            entity_id: ID or path of the entity.
            is_daily: True for daily_tasks, False for project_tasks.

        Returns:
            True if linked successfully.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        table = "daily_tasks" if is_daily else "project_tasks"

        cursor.execute(f'''
            UPDATE {table}
            SET linked_entity_type = ?, linked_entity_id = ?
            WHERE id = ?
        ''', (entity_type, entity_id, task_id))
        conn.commit()
        return cursor.rowcount > 0

    def get_linked_entity(self, task_id: int, is_daily: bool = True) -> Optional[Dict]:
        """
        Get the linked entity for a task.

        Args:
            task_id: The task's ID.
            is_daily: True for daily_tasks, False for project_tasks.

        Returns:
            Dict with 'type' and 'id' keys, or None if no entity linked.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        table = "daily_tasks" if is_daily else "project_tasks"

        cursor.execute(f'''
            SELECT linked_entity_type, linked_entity_id FROM {table} WHERE id = ?
        ''', (task_id,))
        row = cursor.fetchone()

        if row and row[0]:
            return {"type": row[0], "id": row[1]}
        return None

    def create_task_from_sample(self, sample_path: str, title: str = None) -> int:
        """
        Create a daily task linked to a sample.

        Args:
            sample_path: Path to the sample file.
            title: Optional task title (defaults to "Work on <filename>").

        Returns:
            The ID of the created task.
        """
        if not title:
            title = f"Work on {os.path.basename(sample_path)}"

        task_id = self.add_daily_task({
            'title': title,
            'scheduled_date': datetime.now().strftime("%Y-%m-%d"),
            'context': '@Studio'
        })
        self.link_task_to_entity(task_id, "sample", sample_path, is_daily=True)
        return task_id

    def create_project_from_collection(self, collection_id: int, collection_name: str) -> int:
        """
        Create a project from a collection with auto-generated tasks.

        Args:
            collection_id: The collection's ID.
            collection_name: The collection's name.

        Returns:
            The ID of the created project.
        """
        project_id = self.create_project({
            "title": f"{collection_name} Sample Pack",
            "description": f"Complete and export {collection_name} collection"
        })

        # Add template tasks for sample pack workflow
        tasks = [
            {"title": "Tag all samples", "order_index": 0},
            {"title": "Create demo track", "order_index": 1},
            {"title": "Export to ZIP", "order_index": 2}
        ]

        for task_data in tasks:
            self.add_project_task(project_id, task_data)

        return project_id

    # ===== TIME BLOCKING =====

    def set_task_time(self, task_id: int, time_slot: str) -> bool:
        """
        Set time slot for a task (morning, afternoon, evening, or HH:MM).

        Args:
            task_id: The task's ID.
            time_slot: Time slot string.

        Returns:
            True if set successfully.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE daily_tasks SET scheduled_time = ? WHERE id = ?
        ''', (time_slot, task_id))
        conn.commit()
        return cursor.rowcount > 0

    def get_tasks_by_time(self, date: str, time_slot: str) -> List[Dict]:
        """
        Get tasks for a specific time slot.

        Args:
            date: Date in YYYY-MM-DD format.
            time_slot: Time slot to filter by.

        Returns:
            List of task dicts.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM daily_tasks WHERE scheduled_date = ? AND scheduled_time = ?
            ORDER BY priority DESC, created_at ASC
        ''', (date, time_slot))
        return [dict(row) for row in cursor.fetchall()]

    # ===== RECURRING TASKS =====

    def set_task_recurrence(self, task_id: int, recurrence_type: str, interval: int = 1) -> bool:
        """
        Set recurrence rule for a task.

        Args:
            task_id: The task's ID.
            recurrence_type: Type of recurrence ('daily', 'weekly', 'monthly').
            interval: Interval between occurrences.

        Returns:
            True if set successfully.
        """
        rule = json.dumps({"type": recurrence_type, "interval": interval})
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE daily_tasks SET recurrence_rule = ? WHERE id = ?
        ''', (rule, task_id))
        conn.commit()
        return cursor.rowcount > 0

    def generate_recurring_tasks(self, date: str = None) -> int:
        """
        Generate task instances for recurring tasks.

        Args:
            date: Date to generate for (defaults to today).

        Returns:
            Count of generated tasks.
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        conn = self.db._get_connection()
        cursor = conn.cursor()

        # Get all tasks with recurrence rules
        cursor.execute('''
            SELECT * FROM daily_tasks WHERE recurrence_rule IS NOT NULL AND recurrence_rule != ''
        ''')
        recurring_tasks = [dict(row) for row in cursor.fetchall()]

        count = 0
        for task in recurring_tasks:
            rule = json.loads(task['recurrence_rule'])

            # Check if instance already exists for this date
            cursor.execute('''
                SELECT 1 FROM daily_tasks
                WHERE title = ? AND scheduled_date = ? AND id != ?
            ''', (task['title'], date, task['id']))

            if cursor.fetchone():
                continue  # Already exists

            # Create new instance
            self.add_daily_task({
                'title': task['title'],
                'priority': task['priority'],
                'context': task['context'],
                'time_estimate': task['time_estimate'],
                'notes': task.get('notes', ''),
                'scheduled_date': date
            })
            count += 1

        return count

    # ===== PROJECT TEMPLATES =====

    def _init_default_templates(self):
        """Initialize default project templates if they don't exist."""
        existing = self.get_project_templates()
        existing_names = [t['name'] for t in existing]

        for template in DEFAULT_TEMPLATES:
            if template['name'] not in existing_names:
                self.create_project_template(
                    template['name'],
                    template['description'],
                    template['tasks']
                )

    def create_project_template(self, name: str, description: str, tasks: List[Dict]) -> int:
        """
        Create a reusable project template.

        Args:
            name: Template name.
            description: Template description.
            tasks: List of task dicts with title, order_index, due_days.

        Returns:
            The ID of the created template.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        tasks_json = json.dumps(tasks)
        cursor.execute('''
            INSERT INTO project_templates (name, description, tasks_json)
            VALUES (?, ?, ?)
        ''', (name, description, tasks_json))
        conn.commit()
        return cursor.lastrowid

    def get_project_templates(self) -> List[Dict]:
        """
        Get all project templates.

        Returns:
            List of template dicts with parsed tasks.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM project_templates ORDER BY name')
        templates = []
        for row in cursor.fetchall():
            template = dict(row)
            template['tasks'] = json.loads(template['tasks_json'])
            templates.append(template)
        return templates

    def get_project_template(self, template_id: int) -> Optional[Dict]:
        """
        Get a project template by ID.

        Args:
            template_id: The template's ID.

        Returns:
            Template dict or None if not found.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM project_templates WHERE id = ?', (template_id,))
        row = cursor.fetchone()
        if row:
            template = dict(row)
            template['tasks'] = json.loads(template['tasks_json'])
            return template
        return None

    def create_project_from_template(self, template_id: int, project_title: str = None) -> int:
        """
        Create a new project from a template.

        Args:
            template_id: The template's ID.
            project_title: Optional custom title (defaults to template name).

        Returns:
            The ID of the created project.
        """
        template = self.get_project_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        title = project_title or template['name']
        project_id = self.create_project({
            "title": title,
            "description": template['description']
        })

        # Add tasks with calculated due dates
        today = datetime.now()
        for task in template['tasks']:
            due_date = None
            if 'due_days' in task:
                due_date = (today + timedelta(days=task['due_days'])).strftime('%Y-%m-%d')

            self.add_project_task(project_id, {
                'title': task['title'],
                'order_index': task.get('order_index', 0),
                'due_date': due_date
            })

        return project_id

    def delete_project_template(self, template_id: int) -> bool:
        """
        Delete a project template.

        Args:
            template_id: The template's ID.

        Returns:
            True if deleted, False otherwise.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM project_templates WHERE id = ?', (template_id,))
        conn.commit()
        return cursor.rowcount > 0

    # ===== FILTERS & SEARCH =====

    def search_tasks(self, query: str, filters: Dict = None) -> List[Dict]:
        """
        Search tasks with optional filters.

        Args:
            query: Search query for title.
            filters: Optional filters dict with context, priority, time_estimate_max.

        Returns:
            List of matching task dicts.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        sql = 'SELECT * FROM daily_tasks WHERE title LIKE ?'
        params = [f'%{query}%']

        if filters:
            if 'context' in filters:
                sql += ' AND context = ?'
                params.append(filters['context'])
            if 'priority' in filters:
                sql += ' AND priority = ?'
                params.append(filters['priority'])
            if 'time_estimate_max' in filters:
                sql += ' AND (time_estimate IS NULL OR time_estimate <= ?)'
                params.append(filters['time_estimate_max'])

        sql += ' ORDER BY priority DESC, created_at ASC'
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    # ===== TIME TRACKING =====

    def add_time_to_task(self, task_id: int, seconds: int, is_daily: bool = True) -> bool:
        """Add time spent to a task."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        table = "daily_tasks" if is_daily else "project_tasks"
        cursor.execute(f'''
            UPDATE {table} SET time_spent = COALESCE(time_spent, 0) + ? WHERE id = ?
        ''', (seconds, task_id))
        conn.commit()
        return cursor.rowcount > 0

    def get_task_time(self, task_id: int, is_daily: bool = True) -> int:
        """Get total time spent on a task in seconds."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        table = "daily_tasks" if is_daily else "project_tasks"
        cursor.execute(f'SELECT time_spent FROM {table} WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        return row[0] or 0 if row else 0

    # ===== FOCUS SESSIONS (POMODORO) =====

    def start_focus_session(self, task_id: int, is_daily: bool = True, duration: int = 1500) -> int:
        """Start a new focus session. Returns session ID."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO focus_sessions (task_id, is_daily_task, duration, started_at)
            VALUES (?, ?, ?, ?)
        ''', (task_id, is_daily, duration, datetime.now().isoformat()))
        conn.commit()
        return cursor.lastrowid

    def complete_focus_session(self, session_id: int) -> bool:
        """Mark focus session as completed and update task time."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # Get session info
        cursor.execute('SELECT task_id, is_daily_task, duration FROM focus_sessions WHERE id = ?', (session_id,))
        row = cursor.fetchone()
        if not row:
            return False

        task_id, is_daily, duration = row

        # Update session
        cursor.execute('''
            UPDATE focus_sessions SET completed = 1, ended_at = ? WHERE id = ?
        ''', (datetime.now().isoformat(), session_id))

        # Update task time_spent
        self.add_time_to_task(task_id, duration, bool(is_daily))

        conn.commit()
        return True

    def get_focus_sessions(self, task_id: int = None, date: str = None) -> List[Dict]:
        """Get focus sessions, optionally filtered by task or date."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        sql = 'SELECT * FROM focus_sessions WHERE 1=1'
        params = []

        if task_id:
            sql += ' AND task_id = ?'
            params.append(task_id)

        if date:
            sql += ' AND DATE(started_at) = ?'
            params.append(date)

        sql += ' ORDER BY started_at DESC'
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    # ===== PRODUCTIVITY STATS =====

    def get_completion_stats_by_date(self, start_date: str, end_date: str) -> List[Dict]:
        """Get daily completion counts for date range."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DATE(completed_at) as date, COUNT(*) as count
            FROM daily_tasks
            WHERE completed = 1 AND completed_at IS NOT NULL
              AND DATE(completed_at) BETWEEN ? AND ?
            GROUP BY DATE(completed_at)
            ORDER BY date
        ''', (start_date, end_date))
        return [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]

    def get_completion_stats_by_context(self) -> List[Dict]:
        """Get completion counts grouped by context."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT context, COUNT(*) as count, COALESCE(SUM(time_spent), 0) as total_time
            FROM daily_tasks
            WHERE completed = 1
            GROUP BY context
            ORDER BY count DESC
        ''')
        return [{'context': row[0], 'count': row[1], 'total_time': row[2]} for row in cursor.fetchall()]

    def get_most_productive_day(self) -> str:
        """Get the day of week with most completions."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT strftime('%w', completed_at) as day_of_week, COUNT(*) as count
            FROM daily_tasks
            WHERE completed = 1 AND completed_at IS NOT NULL
            GROUP BY day_of_week
            ORDER BY count DESC
            LIMIT 1
        ''')
        row = cursor.fetchone()
        return row[0] if row else '0'

    def get_average_completion_time(self) -> float:
        """Get average time to complete a task (in hours)."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT AVG(
                (julianday(completed_at) - julianday(created_at)) * 24
            ) as avg_hours
            FROM daily_tasks
            WHERE completed = 1 AND completed_at IS NOT NULL AND created_at IS NOT NULL
        ''')
        row = cursor.fetchone()
        return row[0] or 0.0 if row else 0.0

    # ===== COLLABORATIVE TASKS =====

    def assign_task_to_contact(self, task_id: int, contact_id: int) -> bool:
        """Assign a project task to a network contact."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE project_tasks SET assigned_to = ? WHERE id = ?
        ''', (contact_id, task_id))
        conn.commit()
        return cursor.rowcount > 0

    def get_tasks_assigned_to(self, contact_id: int) -> List[Dict]:
        """Get all tasks assigned to a specific contact."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pt.*, p.title as project_title
            FROM project_tasks pt
            JOIN projects p ON pt.project_id = p.id
            WHERE pt.assigned_to = ?
            ORDER BY pt.created_at DESC
        ''', (contact_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_my_tasks(self) -> List[Dict]:
        """Get tasks not assigned to anyone (my tasks)."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pt.*, p.title as project_title
            FROM project_tasks pt
            JOIN projects p ON pt.project_id = p.id
            WHERE pt.assigned_to IS NULL
            ORDER BY pt.created_at DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]

    # ===== CALENDAR EXPORT =====

    def export_to_ics(self, filepath: str, include_daily: bool = True, include_projects: bool = True) -> bool:
        """Export tasks to .ics calendar file."""
        try:
            from icalendar import Calendar, Event
            from datetime import timedelta
            import pytz
        except ImportError:
            return False

        cal = Calendar()
        cal.add('prodid', '-//ProducerOS Studio Flow//produceros.app//')
        cal.add('version', '2.0')
        cal.add('x-wr-calname', 'ProducerOS Tasks')

        # Add daily tasks
        if include_daily:
            tasks = self.get_daily_tasks()
            for task in tasks:
                event = Event()
                event.add('summary', task['title'])
                event.add('uid', f"produceros-daily-{task['id']}@produceros.app")

                if task.get('scheduled_date'):
                    try:
                        dt = datetime.strptime(task['scheduled_date'], '%Y-%m-%d')
                        event.add('dtstart', dt.date())
                        event.add('dtend', (dt + timedelta(days=1)).date())
                    except:
                        pass

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
                    event.add('uid', f"produceros-project-{task['id']}@produceros.app")

                    if task.get('due_date'):
                        try:
                            dt = datetime.strptime(task['due_date'], '%Y-%m-%d')
                            event.add('dtstart', dt.date())
                            event.add('dtend', (dt + timedelta(days=1)).date())
                        except:
                            pass

                    if task.get('description'):
                        event.add('description', task['description'])

                    event.add('dtstamp', datetime.now(pytz.UTC))
                    cal.add_component(event)

        # Write to file
        with open(filepath, 'wb') as f:
            f.write(cal.to_ical())

        return True


# Singleton instance
_task_manager_instance: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """Get the global TaskManager instance."""
    global _task_manager_instance
    if _task_manager_instance is None:
        _task_manager_instance = TaskManager()
    return _task_manager_instance
