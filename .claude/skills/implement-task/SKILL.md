---
name: implement-task
description: Implement tasks from a feature's tasks.md lane against the design.md contract, one task at a time, ticking each checkbox. Use when asked to build/implement a feature task or lane.
argument-hint: "[feature number] [lane: backend|ui]"
---

# Implement tasks from a lane

## Procedure

1. Read `CLAUDE.md`, `specs/NNN-*/spec.md`, `design.md` and `tasks.md`. Identify your lane.
2. For each unchecked task in your lane, in order:
   1. Re-read the ACs it cites and the matching section of `design.md`.
   2. Implement exactly that — names, paths, status codes and visible text **exactly as in the design**.
   3. Only touch files your role owns (CLAUDE.md rule 4). If you need a change elsewhere, note it under
      *Blocked / notes* in `tasks.md` instead.
   4. Run `uv run ruff check --fix . && uv run ruff format .` on what you touched, and `uv run pytest -q`
      to make sure you did not break existing features (tests for the new feature may not exist yet — that
      is fine).
   5. Tick the checkbox: `- [x] TB2 ...`.
3. If the design is ambiguous or wrong, **do not improvise**. Stop and report: what is unclear, and your
   suggested fix to `design.md`.
4. Finish with a short report: tasks done, files changed, anything blocked.

## Coding conventions (from CLAUDE.md)
- Services: plain functions `(session: Session, ...)`; raise `NotFound` / `Conflict` / `ValidationFailed`
  from `app.services.errors`.
- API routes translate service errors to 404 / 409 / 422 via the handlers in `app/main.py`.
- Pages: Jinja2 templates extending `base.html`; HTMX partials live in `app/templates/partials/`.
