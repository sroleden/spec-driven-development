---
name: design-feature
description: Produce design.md for an approved spec — data model changes, the API contract, service functions and UI states. The contract lets backend, UI and test agents work in parallel. Use after spec.md is ready, or when asked to "design" a feature.
argument-hint: "[feature number]"
---

# Design a feature (contract-first)

`design.md` is a **contract**. Three agents will build against it simultaneously without seeing each other's
code, so it must be precise enough that they cannot disagree.

## Procedure

1. Read `specs/NNN-*/spec.md` (stop if Status is `Draft` or there are open questions), `CLAUDE.md`, and the
   current code: `app/models.py`, `app/services/`, `app/routes/`, `app/templates/`. Reuse what exists.
2. Copy [design-template.md](design-template.md) to `specs/NNN-*/design.md` and fill in every section:
   - **Data model** — new/changed SQLModel tables with field names, types, constraints, defaults.
   - **Service layer** — function signatures in `app/services/<module>.py`, their behaviour and which error
     (`NotFound` / `Conflict` / `ValidationFailed`) they raise for each failure.
   - **API contract** — for each endpoint: method, path, request JSON, response JSON with status code, and
     every error status. Give a literal example body for each.
   - **UI** — pages/partials touched, an ASCII wireframe, and each UI state (empty, normal, error, sold out…)
     with the exact user-visible text the tester may assert on.
   - **AC mapping** — table mapping every AC ID to the endpoint/UI state that satisfies it.
3. Self-check:
   - [ ] Every AC appears in the AC mapping.
   - [ ] Every error in the spec has a status code and an example body.
   - [ ] Names match existing code conventions (snake_case fields, `/api/...` JSON routes).
   - [ ] Nothing the spec lists as out of scope.
4. Continue with the `break-into-tasks` skill.
