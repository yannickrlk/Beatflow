# Implement Task Workflow

Follow the Claude Workflow to implement the current task from CURRENT_TASK.md.

## Step 1: Read Context Files

Read these 3 files to understand the current state:
1. `CONTEXT.md` - Project overview, architecture, what's completed
2. `CURRENT_TASK.md` - Specific objectives for the current task
3. `implementation_plan.md` - Roadmap with phases and pending items

## Step 2: Plan the Implementation

Create a TodoWrite with a breakdown of the tasks from CURRENT_TASK.md. Each todo item should be specific and actionable.

## Step 3: Implement Each Objective

For each objective in CURRENT_TASK.md:
- Focus on the files mentioned in the task
- Follow the technical requirements exactly
- Test as you go when possible
- Mark todos as completed when done

## Step 4: Update Documentation

After completing the implementation, update all 3 files:

### CONTEXT.md
- Update "Current State (What Works)" section with new features
- Update "Not Yet Implemented" section
- Update "Last implementation" line at bottom

### CURRENT_TASK.md
- Mark all completed items with `[x]`
- Update status to COMPLETE
- Add any notes about the implementation

### implementation_plan.md
- Mark completed items with `[x]`
- Update phase status (In Progress → Complete)

## Step 5: Report Completion

Provide a summary of:
- What was implemented
- Files modified
- Any issues encountered
- Next steps (if any)
