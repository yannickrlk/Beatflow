# Beatflow Project Instructions

## Workflow (ALWAYS follow this)
Before implementing any task, follow the workflow in CLAUDE_WORKFLOW.md:
1. Read CONTEXT.md, CURRENT_TASK.md, and implementation_plan.md
2. Implement the task
3. Update all 3 documentation files after completion

## Key Files
- `CONTEXT.md` - Project overview, architecture, components
- `CURRENT_TASK.md` - Current task objectives and details
- `implementation_plan.md` - Roadmap with completed/pending items
- `CLAUDE_WORKFLOW.md` - Step-by-step workflow guide

## Tech Stack
- **Python 3.12** (NOT 3.14 - crashes with librosa/numba)
- CustomTkinter for GUI
- Pygame for audio playback
- SQLite for metadata caching
- Mutagen for reading audio tags
- Librosa/Numba for BPM/Key detection

## Code Style
- Keep changes minimal and focused
- Don't add unnecessary features or abstractions
- Update documentation after completing tasks
