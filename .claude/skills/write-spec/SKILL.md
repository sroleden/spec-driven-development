---
name: write-spec
description: Turn a feature idea (specs/NNN-*/idea.md or a description) into a testable spec.md with user stories and numbered acceptance criteria. Use when starting a new feature or when asked to "write/refine a spec".
argument-hint: "[feature number, e.g. 003]"
---

# Write a feature spec

A spec says **what** and **why**, never **how**. No endpoints, tables or file names here — that is the
designer's job.

## Procedure

1. Locate the feature folder `specs/NNN-<slug>/` (argument `$ARGUMENTS`, or the highest-numbered folder that
   has an `idea.md` but no `spec.md`). Read `idea.md`, `CLAUDE.md`, and every existing `specs/*/spec.md` so you
   reuse established domain terms (Event, Reservation, capacity, ...).
2. List what is ambiguous. **Ask the user up to 4 clarifying questions** before writing (business rules,
   limits, edge cases). If you cannot ask (running unattended), record them under *Open questions* instead.
3. Copy [spec-template.md](spec-template.md) to `specs/NNN-<slug>/spec.md` and fill it in:
   - 2–4 user stories in "As a … I want … so that …" form.
   - Acceptance criteria numbered `AC<N>.<n>` where `<N>` is the feature number without leading zeros
     (feature 003 → `AC3.1`, `AC3.2`, ...). Write each in **Given / When / Then** form.
   - Every AC must be independently testable by an HTTP request or a page interaction. One behaviour per AC.
   - Cover the unhappy paths: invalid input, not found, limits, duplicates.
   - *Out of scope* is mandatory — it stops the coders gold-plating.
4. Self-check before finishing:
   - [ ] No implementation details (no URLs, SQL, class names).
   - [ ] Every user story is covered by at least one AC.
   - [ ] Each AC has exactly one observable outcome.
   - [ ] Status is `Draft` if there are open questions, otherwise `Ready for design`.
5. Reply with a 3-line summary and the list of AC IDs. Do not start designing.
