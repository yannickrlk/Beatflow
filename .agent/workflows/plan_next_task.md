---
description: Plan the next task, research dependencies, and prepare the project for the next developer phase.
---

1. **Read Documentation**
   - Read `implementation_plan.md` to identify the next incomplete phase or task.
   - Read `CONTEXT.md` to understand the current project state and architecture.
   - Read `current_task.md` to understand immediate context.
   - Read `requirements.txt` to check existing dependencies.

2. **Research & Plan**
   - precise the goal of the next task.
   - Identify any new external libraries or tools needed.
   - If unsure about specific requirements (e.g., "Which database?", "Which UI library?"), use `notify_user` to ask the user.
   - research the best libraries or approaches if needed (using `search_web` if available or internal knowledge).

3. **User Approval (Stop)**
   - **CRITICAL**: Do NOT write any code or modify `requirements.txt` yet.
   - Use `notify_user` to present the plan:
     - The Objective (what will be built).
     - Proposed Dependencies (if any).
     - Any architectural changes.
     - Ask: "Are you OK with this plan?"

4. **Prepare Project (If Approved)**
   - **Only proceed if the user says "OK" or approves.**
   - **Add Dependencies**:
     - If new libraries are needed, append them to `requirements.txt`.
   - **Update Documentation**:
     - Update `implementation_plan.md`: Mark previous tasks as completed, add details for the new task.
     - Update `CONTEXT.md`: Update "Current State", "Project Overview", or "Key Components" if relevant.
     - Update `current_task.md`: Write a detailed, technical task description for the next developer/agent. This should be very specific (files to edit, functions to create).

5. **Handover**
   - Use `notify_user` to confirm that the project is ready for the coding phase.
