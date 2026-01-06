# Claude Workflow Guide

## When User Says: "implement the next task"

### Step 1: Read Context Files (Before Starting)
Always verify these 3 files to understand the current state:

| File | Purpose |
|------|---------|
| `CONTEXT.md` | Full project overview, architecture, what's completed |
| `CURRENT_TASK.md` | Specific objectives for the current task |
| `implementation_plan.md` | Roadmap with phases and pending items |

### Step 2: Implement the Task
- Follow the objectives in `CURRENT_TASK.md`
- Focus on the files mentioned in the task
- Do NOT modify `sample_browser.py` (legacy file)

### Step 3: Update Documentation (After Completing)
Update all 3 files to reflect completed work:

1. **CONTEXT.md**:
   - Update "Current State (What Works)" section
   - Update "Not Yet Implemented" section
   - Update "Last implementation" line at bottom

2. **CURRENT_TASK.md**:
   - Replace with the NEXT task from `implementation_plan.md`
   - Include: Context, Objectives, Files to modify, Notes

3. **implementation_plan.md**:
   - Mark completed items with `[x]`
   - Move to next phase if needed

### Step 4: Create New Docs If Needed
If helpful for Gemini collaboration, create additional files like:
- `ARCHITECTURE.md` for complex system changes
- `API.md` for new component interfaces

---

## Collaboration Model

```
┌─────────────┐     ┌─────────────┐
│   Claude    │     │   Gemini    │
│ (Implement) │◄───►│ (Brainstorm)│
└─────────────┘     └─────────────┘
       │                   │
       └───────┬───────────┘
               ▼
    ┌─────────────────────┐
    │  Shared Doc Files   │
    │  - CONTEXT.md       │
    │  - CURRENT_TASK.md  │
    │  - implementation_  │
    │    plan.md          │
    └─────────────────────┘
```

- **Claude**: Reads tasks, implements code, updates docs
- **Gemini**: Reads context, brainstorms solutions, suggests approaches
- **Docs**: Bridge between both AIs for context continuity

---

## Quick Reference

```
User: "implement the next task"

Claude:
1. Read CONTEXT.md, CURRENT_TASK.md, implementation_plan.md
2. Create TodoWrite with task breakdown
3. Implement each objective
4. Update all 3 doc files
5. Report completion to user
```
