---
name: break-into-tasks
description: Split a feature's design.md into small, ordered tasks in tasks.md, each owned by one agent (backend / ui / test) and linked to AC IDs, so work can run in parallel. Use right after design-feature.
argument-hint: "[feature number]"
---

# Break a design into tasks

## Procedure

1. Read `specs/NNN-*/spec.md` and `design.md`.
2. Copy [tasks-template.md](tasks-template.md) to `specs/NNN-*/tasks.md`.
3. Write tasks in three lanes, one per agent, matching the file ownership in `CLAUDE.md`:
   - **backend** → `backend-coder` (models, services, `api.py`)
   - **ui** → `ui-coder` (templates, static, `pages.py`)
   - **test** → `tester` (`tests/`)
4. Each task is one checkbox line: `- [ ] T<lane-letter><n> <imperative description> (ACN.x, ACN.y)`
   e.g. `- [ ] TB2 Add join_waitlist service raising Conflict when already waiting (AC3.1, AC3.4)`.
   - A task is small: one function, one endpoint, one template state, or one group of tests.
   - Every AC must be referenced by at least one **test** task and one **backend or ui** task.
   - Lanes must not depend on each other — only on `design.md`. If the UI needs a service function, it uses the
     signature from the design, not the implementation.
5. Add the traceability matrix at the bottom (AC → tasks).
6. Reply with task counts per lane.
