# Studio Flow Manual Test Checklist

## Pre-requisites
```bash
# Install dependencies
py -3.12 -m pip install matplotlib icalendar

# Run automated tests first
py -3.12 tests/test_studio_flow.py
```

---

## Phase 21: Core Task Management

### Today View
- [ ] Open Beatflow and navigate to "Studio Flow" in sidebar
- [ ] Verify "Today" tab is selected by default
- [ ] Check date header shows correct date (e.g., "Sunday, January 12")

### Add Task
- [ ] Click in the task input field
- [ ] Type "Test task" and press Enter
- [ ] Verify task appears in the list below
- [ ] Verify task count updates (e.g., "0 of 1 completed")

### Tag Selection
- [ ] Click on different tag buttons (@Studio, @Mixing, @Marketing, @Admin, @Other)
- [ ] Verify button highlights when selected
- [ ] Add a new task with a selected tag
- [ ] Verify the task shows the correct tag color

### Complete Task
- [ ] Click the checkbox on a task
- [ ] Verify task is marked as completed (checkbox filled)
- [ ] Verify count updates (e.g., "1 of 1 completed")
- [ ] Verify completed task style changes (strikethrough or dimmed)

### Delete Task
- [ ] Right-click on a task
- [ ] Select "Delete" option
- [ ] Verify task is removed from list

### Priority Levels
- [ ] Add tasks with different priorities (if UI supports)
- [ ] Verify priority indicator dots show correct colors:
  - Gray = Normal (0)
  - Orange = High (1)
  - Red = Urgent (2)

---

## Phase 21: Projects View

### Navigate to Projects
- [ ] Click "Projects" tab
- [ ] Verify projects list loads

### Create Project
- [ ] Click "+ New Project" button
- [ ] Enter project title: "Test Album"
- [ ] Enter description: "Testing project creation"
- [ ] Click Save/Create
- [ ] Verify project appears in list

### Add Project Task
- [ ] Click on the created project
- [ ] Add a task: "Record vocals"
- [ ] Add another task: "Mix tracks"
- [ ] Verify tasks appear under project

### Toggle Project Task
- [ ] Click checkbox on a project task
- [ ] Verify completion status updates
- [ ] Verify project progress bar updates (if visible)

### Delete Project
- [ ] Right-click on a project
- [ ] Select "Delete"
- [ ] Confirm deletion
- [ ] Verify project is removed

---

## Phase 21.1: UX Enhancements

### Keyboard Shortcut
- [ ] Press Ctrl+T anywhere in Studio Flow
- [ ] Verify task input field gets focus

### Completion Animation
- [ ] Complete a task by clicking checkbox
- [ ] Watch for fade-out animation with checkmark

### Smart Placeholders
- [ ] Clear the task input field
- [ ] Wait a few seconds (placeholder rotation disabled, so static)
- [ ] Verify placeholder text is helpful

### Empty State
- [ ] Delete all tasks for today
- [ ] Verify empty state shows:
  - Checkmark icon
  - "No tasks for today" message
  - Helpful suggestion text

---

## Phase 21.1: Project Templates

### Create from Template
- [ ] Go to Projects tab
- [ ] Click "+ New Project"
- [ ] Select a template (Album Release, Sample Pack, or Client Beat)
- [ ] Verify project is created with pre-populated tasks
- [ ] Check tasks have calculated due dates

---

## Phase 21.2: Focus Mode

### Open Focus Mode
- [ ] Go to Today tab
- [ ] Click "Focus Mode" button (purple button in header)
- [ ] Verify QuickFocusDialog opens

### Select Task and Duration
- [ ] In dialog, select a task from the list
- [ ] Click different duration buttons (15m, 25m, 45m, 60m)
- [ ] Verify selected button highlights
- [ ] Click "Start Focus Session"

### Focus Mode Window
- [ ] Verify focus window opens (800x600)
- [ ] Check task title is displayed
- [ ] Verify timer shows correct initial time (e.g., "25:00")
- [ ] Verify progress bar is full (1.0)

### Timer Controls
- [ ] Click "Start" button
- [ ] Verify timer counts down
- [ ] Verify progress bar decreases
- [ ] Click "Pause" button
- [ ] Verify timer stops
- [ ] Click "Resume" (Start button text changes)
- [ ] Verify timer continues

### Exit Focus Mode
- [ ] Press ESC key
- [ ] Verify focus window closes
- [ ] OR click "Stop" button to exit

### Session Completion (optional - wait 25 min or modify code for shorter test)
- [ ] Let timer reach 00:00
- [ ] Verify "DONE!" message appears in green
- [ ] Verify session count updates at bottom

---

## Phase 21.2: Productivity Dashboard

### Navigate to Dashboard
- [ ] Click "Dashboard" tab
- [ ] Verify dashboard loads

### Stats Cards
- [ ] Check "Today's Tasks" card shows correct count
- [ ] Check "Focus Time" card shows minutes
- [ ] Check "Sessions" card shows session count
- [ ] Check "Active Projects" card shows count

### Charts (if matplotlib installed)
- [ ] Verify "Tasks Completed (Last 7 Days)" bar chart renders
- [ ] Verify "Tasks by Context" pie chart renders
- [ ] Verify "Focus Sessions (Last 7 Days)" area chart renders
- [ ] Check insights panel shows relevant tips

### Charts (if matplotlib NOT installed)
- [ ] Verify warning message about matplotlib
- [ ] Verify text-based stats display correctly

### Refresh
- [ ] Click "Refresh" button
- [ ] Verify charts/stats update

---

## Phase 21.2: Calendar View

### Navigate to Calendar
- [ ] Click "Calendar" tab
- [ ] Verify calendar loads with current month

### Month Display
- [ ] Check month/year label is correct (e.g., "January 2026")
- [ ] Verify day headers show (Mon, Tue, Wed, etc.)
- [ ] Verify days are arranged correctly in grid

### Navigation
- [ ] Click "<" button
- [ ] Verify previous month loads
- [ ] Click ">" button
- [ ] Verify next month loads
- [ ] Click "Today" button
- [ ] Verify returns to current month with today highlighted

### Task Indicators
- [ ] Add a task for today (if none exist)
- [ ] Verify today's date cell shows task count/dots
- [ ] Green dot = completed task
- [ ] Orange dot = pending task

### Date Selection
- [ ] Click on a date with tasks
- [ ] Verify info panel shows date and task list
- [ ] Check task completion status shows correctly

### Export to .ics
- [ ] Click "Export .ics" button
- [ ] Choose save location
- [ ] Verify .ics file is created
- [ ] (Optional) Import into Google Calendar to verify format

---

## Integration Tests

### Sample Linking (from Browse view)
- [ ] Go to Browse view
- [ ] Right-click on a sample
- [ ] Select "Create Task for This"
- [ ] Go to Studio Flow > Today
- [ ] Verify task was created with sample link

### Collection to Project
- [ ] Go to Browse view
- [ ] Right-click on a Collection
- [ ] Select "Create Project from Collection"
- [ ] Go to Studio Flow > Projects
- [ ] Verify project was created with template tasks

---

## Database Persistence

### Restart Test
- [ ] Add several tasks and projects
- [ ] Complete some tasks
- [ ] Start a focus session
- [ ] Close Beatflow completely
- [ ] Reopen Beatflow
- [ ] Go to Studio Flow
- [ ] Verify all data persisted:
  - [ ] Tasks still exist
  - [ ] Completion status preserved
  - [ ] Projects and project tasks preserved
  - [ ] Focus session history in database

---

## Error Handling

### Empty States
- [ ] New install with no tasks - verify empty state shows
- [ ] Delete all projects - verify empty state in Projects tab
- [ ] No completed tasks - verify dashboard handles gracefully

### Invalid Input
- [ ] Try adding task with empty title - should be ignored
- [ ] Export .ics and cancel dialog - should not error

---

## Performance

### Large Data
- [ ] Add 50+ tasks
- [ ] Verify Today view loads quickly
- [ ] Verify Dashboard renders without freezing
- [ ] Verify Calendar navigates smoothly

---

## Test Results

| Section | Pass | Fail | Notes |
|---------|------|------|-------|
| Today View | | | |
| Projects | | | |
| UX Enhancements | | | |
| Focus Mode | | | |
| Dashboard | | | |
| Calendar | | | |
| Integration | | | |
| Persistence | | | |
| Error Handling | | | |
| Performance | | | |

**Overall Result**: _______________

**Tester**: _______________

**Date**: _______________
