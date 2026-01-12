"""
Studio Flow Test Suite
======================
Comprehensive tests for Phase 21, 21.1, and 21.2 features.

Run with: py -3.12 -m pytest tests/test_studio_flow.py -v
Or manually: py -3.12 tests/test_studio_flow.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from datetime import datetime, timedelta
from core.database import get_database
from core.task_manager import get_task_manager


class TestDailyTasks(unittest.TestCase):
    """Test daily task CRUD operations."""

    def setUp(self):
        self.tm = get_task_manager()
        self.today = datetime.now().strftime('%Y-%m-%d')

    def test_add_daily_task(self):
        """Test adding a daily task."""
        task_id = self.tm.add_daily_task({
            'title': 'Test Task',
            'scheduled_date': self.today,
            'context': '@Studio',
            'priority': 1
        })
        self.assertIsNotNone(task_id)
        self.assertGreater(task_id, 0)
        print(f"[OK] Added daily task with ID: {task_id}")

    def test_get_daily_tasks(self):
        """Test retrieving daily tasks."""
        # Add a task first
        self.tm.add_daily_task({
            'title': 'Get Test Task',
            'scheduled_date': self.today,
            'context': '@Mixing'
        })

        tasks = self.tm.get_daily_tasks(self.today)
        self.assertIsInstance(tasks, list)
        print(f"[OK] Retrieved {len(tasks)} daily tasks for {self.today}")

    def test_toggle_daily_task(self):
        """Test toggling task completion."""
        task_id = self.tm.add_daily_task({
            'title': 'Toggle Test Task',
            'scheduled_date': self.today
        })

        # Toggle to completed
        new_status = self.tm.toggle_daily_task(task_id)
        self.assertTrue(new_status)
        print(f"[OK] Toggled task {task_id} to completed")

        # Toggle back to not completed
        new_status = self.tm.toggle_daily_task(task_id)
        self.assertFalse(new_status)
        print(f"[OK] Toggled task {task_id} back to not completed")

    def test_delete_daily_task(self):
        """Test deleting a daily task."""
        task_id = self.tm.add_daily_task({
            'title': 'Delete Test Task',
            'scheduled_date': self.today
        })

        result = self.tm.delete_daily_task(task_id)
        self.assertTrue(result)
        print(f"[OK] Deleted daily task {task_id}")

    def test_context_tags(self):
        """Test all context tags work."""
        contexts = ['@Studio', '@Mixing', '@Marketing', '@Admin', '@Other']

        for ctx in contexts:
            task_id = self.tm.add_daily_task({
                'title': f'Task with {ctx}',
                'scheduled_date': self.today,
                'context': ctx
            })
            self.assertIsNotNone(task_id)
        print(f"[OK] All {len(contexts)} context tags work correctly")

    def test_priority_levels(self):
        """Test all priority levels."""
        for priority in [0, 1, 2]:  # Normal, High, Urgent
            task_id = self.tm.add_daily_task({
                'title': f'Priority {priority} Task',
                'scheduled_date': self.today,
                'priority': priority
            })
            self.assertIsNotNone(task_id)
        print("[OK] All priority levels (0, 1, 2) work correctly")


class TestProjects(unittest.TestCase):
    """Test project CRUD operations."""

    def setUp(self):
        self.tm = get_task_manager()

    def test_create_project(self):
        """Test creating a project."""
        project_id = self.tm.create_project({
            'title': 'Test Project',
            'description': 'A test project for unit testing',
            'deadline': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        })
        self.assertIsNotNone(project_id)
        self.assertGreater(project_id, 0)
        print(f"[OK] Created project with ID: {project_id}")

    def test_get_projects(self):
        """Test retrieving projects."""
        # Create a project first
        self.tm.create_project({'title': 'Get Test Project'})

        projects = self.tm.get_projects()
        self.assertIsInstance(projects, list)
        print(f"[OK] Retrieved {len(projects)} projects")

    def test_add_project_task(self):
        """Test adding tasks to a project."""
        project_id = self.tm.create_project({'title': 'Project with Tasks'})

        task_id = self.tm.add_project_task(project_id, {
            'title': 'First project task',
            'description': 'Task description',
            'due_date': datetime.now().strftime('%Y-%m-%d')
        })
        self.assertIsNotNone(task_id)
        print(f"[OK] Added task {task_id} to project {project_id}")

    def test_get_project_tasks(self):
        """Test retrieving project tasks."""
        project_id = self.tm.create_project({'title': 'Project for Task Retrieval'})
        self.tm.add_project_task(project_id, {'title': 'Task 1'})
        self.tm.add_project_task(project_id, {'title': 'Task 2'})

        tasks = self.tm.get_project_tasks(project_id)
        self.assertGreaterEqual(len(tasks), 2)
        print(f"[OK] Retrieved {len(tasks)} tasks from project {project_id}")

    def test_toggle_project_task(self):
        """Test toggling project task completion."""
        project_id = self.tm.create_project({'title': 'Toggle Test Project'})
        task_id = self.tm.add_project_task(project_id, {'title': 'Toggle Task'})

        new_status = self.tm.toggle_project_task(task_id)
        self.assertTrue(new_status)
        print(f"[OK] Toggled project task {task_id}")

    def test_delete_project(self):
        """Test deleting a project."""
        project_id = self.tm.create_project({'title': 'Delete Test Project'})

        result = self.tm.delete_project(project_id)
        self.assertTrue(result)
        print(f"[OK] Deleted project {project_id}")


class TestProjectTemplates(unittest.TestCase):
    """Test project template functionality."""

    def setUp(self):
        self.tm = get_task_manager()

    def test_get_templates(self):
        """Test retrieving project templates."""
        templates = self.tm.get_project_templates()
        self.assertIsInstance(templates, list)
        print(f"[OK] Retrieved {len(templates)} project templates")

    def test_create_from_template(self):
        """Test creating project from template."""
        templates = self.tm.get_project_templates()
        if templates:
            template = templates[0]
            project_id = self.tm.create_project_from_template(
                template['id'],
                f"Test {template['name']}"
            )
            self.assertIsNotNone(project_id)

            # Check tasks were created
            tasks = self.tm.get_project_tasks(project_id)
            self.assertGreater(len(tasks), 0)
            print(f"[OK] Created project from template '{template['name']}' with {len(tasks)} tasks")
        else:
            print("[WARN] No templates available to test")


class TestTimeTracking(unittest.TestCase):
    """Test time tracking functionality (Phase 21.2)."""

    def setUp(self):
        self.tm = get_task_manager()
        self.today = datetime.now().strftime('%Y-%m-%d')

    def test_add_time_to_task(self):
        """Test adding time to a task."""
        task_id = self.tm.add_daily_task({
            'title': 'Time Tracking Task',
            'scheduled_date': self.today
        })

        # Add 30 minutes (1800 seconds)
        result = self.tm.add_time_to_task(task_id, 1800, is_daily=True)
        self.assertTrue(result)

        # Check time was recorded
        time_spent = self.tm.get_task_time(task_id, is_daily=True)
        self.assertEqual(time_spent, 1800)
        print(f"[OK] Added 30 minutes to task {task_id}, total: {time_spent}s")

    def test_cumulative_time(self):
        """Test that time accumulates correctly."""
        task_id = self.tm.add_daily_task({
            'title': 'Cumulative Time Task',
            'scheduled_date': self.today
        })

        self.tm.add_time_to_task(task_id, 600)  # 10 min
        self.tm.add_time_to_task(task_id, 600)  # 10 min
        self.tm.add_time_to_task(task_id, 600)  # 10 min

        time_spent = self.tm.get_task_time(task_id)
        self.assertEqual(time_spent, 1800)  # 30 min total
        print(f"[OK] Cumulative time tracking works: {time_spent}s")


class TestFocusSessions(unittest.TestCase):
    """Test Pomodoro focus session functionality (Phase 21.2)."""

    def setUp(self):
        self.tm = get_task_manager()
        self.today = datetime.now().strftime('%Y-%m-%d')

    def test_start_focus_session(self):
        """Test starting a focus session."""
        task_id = self.tm.add_daily_task({
            'title': 'Focus Session Task',
            'scheduled_date': self.today
        })

        session_id = self.tm.start_focus_session(task_id, is_daily=True, duration=1500)
        self.assertIsNotNone(session_id)
        self.assertGreater(session_id, 0)
        print(f"[OK] Started focus session {session_id} for task {task_id}")

    def test_complete_focus_session(self):
        """Test completing a focus session."""
        task_id = self.tm.add_daily_task({
            'title': 'Complete Session Task',
            'scheduled_date': self.today
        })

        session_id = self.tm.start_focus_session(task_id, is_daily=True, duration=1500)
        result = self.tm.complete_focus_session(session_id)
        self.assertTrue(result)

        # Check time was added to task
        time_spent = self.tm.get_task_time(task_id)
        self.assertEqual(time_spent, 1500)
        print(f"[OK] Completed focus session, task time: {time_spent}s")

    def test_get_focus_sessions(self):
        """Test retrieving focus sessions."""
        task_id = self.tm.add_daily_task({
            'title': 'Get Sessions Task',
            'scheduled_date': self.today
        })

        self.tm.start_focus_session(task_id, duration=1500)
        self.tm.start_focus_session(task_id, duration=900)

        sessions = self.tm.get_focus_sessions(task_id=task_id)
        self.assertGreaterEqual(len(sessions), 2)
        print(f"[OK] Retrieved {len(sessions)} focus sessions for task {task_id}")

    def test_get_sessions_by_date(self):
        """Test retrieving focus sessions by date."""
        sessions = self.tm.get_focus_sessions(date=self.today)
        self.assertIsInstance(sessions, list)
        print(f"[OK] Retrieved {len(sessions)} focus sessions for {self.today}")


class TestProductivityStats(unittest.TestCase):
    """Test productivity statistics (Phase 21.2)."""

    def setUp(self):
        self.tm = get_task_manager()

    def test_completion_stats_by_date(self):
        """Test getting completion stats by date range."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        stats = self.tm.get_completion_stats_by_date(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        self.assertIsInstance(stats, list)
        print(f"[OK] Got completion stats for last 7 days: {len(stats)} data points")

    def test_completion_stats_by_context(self):
        """Test getting completion stats by context."""
        stats = self.tm.get_completion_stats_by_context()
        self.assertIsInstance(stats, list)
        print(f"[OK] Got context breakdown: {len(stats)} contexts")
        for s in stats:
            print(f"  - {s.get('context', 'None')}: {s.get('count', 0)} tasks")

    def test_overall_stats(self):
        """Test getting overall completion stats."""
        stats = self.tm.get_completion_stats()
        self.assertIn('daily_total', stats)
        self.assertIn('daily_completed', stats)
        self.assertIn('active_projects', stats)
        print(f"[OK] Overall stats: {stats['daily_completed']}/{stats['daily_total']} daily tasks, {stats['active_projects']} projects")


class TestCalendarExport(unittest.TestCase):
    """Test calendar export functionality (Phase 21.2)."""

    def setUp(self):
        self.tm = get_task_manager()
        self.today = datetime.now().strftime('%Y-%m-%d')

    def test_export_to_ics(self):
        """Test exporting tasks to .ics file."""
        import tempfile

        # Check if icalendar and pytz are installed
        try:
            import icalendar
            import pytz
        except ImportError:
            print("[SKIP] icalendar or pytz not installed, skipping test")
            return

        # Create some tasks
        self.tm.add_daily_task({
            'title': 'Export Test Task 1',
            'scheduled_date': self.today,
            'context': '@Studio'
        })
        self.tm.add_daily_task({
            'title': 'Export Test Task 2',
            'scheduled_date': self.today,
            'context': '@Mixing'
        })

        # Export to temp file
        with tempfile.NamedTemporaryFile(suffix='.ics', delete=False) as f:
            filepath = f.name

        # Call with correct parameters (include_daily=True, include_projects=True)
        result = self.tm.export_to_ics(filepath, include_daily=True, include_projects=True)
        self.assertTrue(result)

        # Verify file exists and has content
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, 'r') as f:
            content = f.read()
            self.assertIn('BEGIN:VCALENDAR', content)
            self.assertIn('BEGIN:VEVENT', content)

        # Cleanup
        os.remove(filepath)
        print(f"[OK] Exported tasks to .ics file successfully")


class TestSampleLinking(unittest.TestCase):
    """Test sample/entity linking functionality (Phase 21.1)."""

    def setUp(self):
        self.tm = get_task_manager()
        self.today = datetime.now().strftime('%Y-%m-%d')

    def test_link_task_to_sample(self):
        """Test linking a task to a sample."""
        task_id = self.tm.add_daily_task({
            'title': 'Work on kick sample',
            'scheduled_date': self.today
        })

        result = self.tm.link_task_to_entity(task_id, 'sample', 'C:/Samples/kick.wav')
        self.assertTrue(result)
        print(f"[OK] Linked task {task_id} to sample")

    def test_get_linked_entity(self):
        """Test retrieving linked entity."""
        task_id = self.tm.add_daily_task({
            'title': 'Process 808 sample',
            'scheduled_date': self.today
        })
        self.tm.link_task_to_entity(task_id, 'sample', 'C:/Samples/808.wav')

        entity = self.tm.get_linked_entity(task_id)
        self.assertIsNotNone(entity)
        self.assertEqual(entity['type'], 'sample')
        self.assertEqual(entity['id'], 'C:/Samples/808.wav')
        print(f"[OK] Retrieved linked entity: {entity}")

    def test_create_task_from_sample(self):
        """Test creating a task from a sample path."""
        task_id = self.tm.create_task_from_sample('C:/Samples/snare_punchy.wav')
        self.assertIsNotNone(task_id)

        entity = self.tm.get_linked_entity(task_id)
        self.assertIsNotNone(entity)
        print(f"[OK] Created task {task_id} from sample path")


class TestRecurringTasks(unittest.TestCase):
    """Test recurring task functionality (Phase 21.1 infrastructure)."""

    def setUp(self):
        self.tm = get_task_manager()
        self.today = datetime.now().strftime('%Y-%m-%d')

    def test_set_recurrence(self):
        """Test setting task recurrence."""
        task_id = self.tm.add_daily_task({
            'title': 'Daily standup',
            'scheduled_date': self.today
        })

        result = self.tm.set_task_recurrence(task_id, 'daily', 1)
        self.assertTrue(result)
        print(f"[OK] Set daily recurrence on task {task_id}")

    def test_generate_recurring(self):
        """Test generating recurring task instances."""
        task_id = self.tm.add_daily_task({
            'title': 'Recurring Test Task',
            'scheduled_date': self.today
        })
        self.tm.set_task_recurrence(task_id, 'daily', 1)

        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        count = self.tm.generate_recurring_tasks(tomorrow)
        # May or may not generate depending on existing tasks
        print(f"[OK] Generated {count} recurring task instances")


class TestDatabaseSchema(unittest.TestCase):
    """Test database schema integrity."""

    def setUp(self):
        self.db = get_database()

    def test_daily_tasks_columns(self):
        """Test daily_tasks table has all required columns."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(daily_tasks)")
        columns = {row[1] for row in cursor.fetchall()}

        required = {'id', 'title', 'completed', 'priority', 'context', 'scheduled_date', 'time_spent'}
        missing = required - columns
        self.assertEqual(len(missing), 0, f"Missing columns: {missing}")
        print(f"[OK] daily_tasks has all required columns: {required}")

    def test_focus_sessions_table(self):
        """Test focus_sessions table exists and has correct columns."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(focus_sessions)")
        columns = {row[1] for row in cursor.fetchall()}

        required = {'id', 'task_id', 'is_daily_task', 'duration', 'completed', 'started_at'}
        missing = required - columns
        self.assertEqual(len(missing), 0, f"Missing columns: {missing}")
        print(f"[OK] focus_sessions table has all required columns")

    def test_project_tasks_columns(self):
        """Test project_tasks table has time tracking columns."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(project_tasks)")
        columns = {row[1] for row in cursor.fetchall()}

        self.assertIn('time_spent', columns)
        print(f"[OK] project_tasks has time_spent column")


def run_all_tests():
    """Run all tests and print summary."""
    print("=" * 60)
    print("STUDIO FLOW TEST SUITE")
    print("=" * 60)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestDailyTasks,
        TestProjects,
        TestProjectTemplates,
        TestTimeTracking,
        TestFocusSessions,
        TestProductivityStats,
        TestCalendarExport,
        TestSampleLinking,
        TestRecurringTasks,
        TestDatabaseSchema,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    if result.wasSuccessful():
        print()
        print("[PASS] ALL TESTS PASSED!")
    else:
        print()
        print("[FAIL] SOME TESTS FAILED")
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split(chr(10))[0]}")
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.split(chr(10))[0]}")

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
