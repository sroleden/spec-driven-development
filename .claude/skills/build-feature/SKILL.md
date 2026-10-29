---
name: build-feature
description: Orchestrate the full multi-agent spec-driven pipeline for one feature — spec-writer, designer, then backend-coder, ui-coder and tester in parallel, then spec-reviewer with a fix loop. Use when asked to "build feature NNN end to end".
argument-hint: "<feature number, e.g. 003>"
disable-model-invocation: true
---

# Build a feature with the agent team

Feature: `$ARGUMENTS`. You (the main session) are the **orchestrator**: you launch agents and pass results
between them; you do not write specs or code yourself.

## Stage 1 — Specify (sequential, human in the loop)
- If `specs/$ARGUMENTS-*/spec.md` is missing: launch the **spec-writer** agent for feature `$ARGUMENTS`.
- Relay any *Open questions* the spec-writer returned to the user (subagents can't ask them directly),
  then re-launch spec-writer with the answers.
- Show the user the AC list. **Wait for approval** (or edits) before continuing; then set Status to
  `Approved`.

## Stage 2 — Design (sequential)
- If `design.md` or `tasks.md` is missing: launch the **designer** agent.
- Show the user the API contract summary and the task counts per lane.

## Stage 3 — Build & test (PARALLEL)
Launch these three agents **in a single message, so they run concurrently**:
1. **backend-coder** — "Implement the backend lane of specs/$ARGUMENTS-*/tasks.md."
2. **ui-coder** — "Implement the ui lane of specs/$ARGUMENTS-*/tasks.md."
3. **tester** — "Implement the test lane of specs/$ARGUMENTS-*/tasks.md."

They share no code with each other — only `design.md`. Wait for all three.
If any agent reports the design is ambiguous, send it back to the **designer**, then re-run only the
affected lane.

## Stage 4 — Verify (fan-in + fix loop)
- Launch the **spec-reviewer** agent.
- If the result is FAIL: group failures by owner and re-launch **only those agents** (in parallel if more
  than one) with the failing rows of `review.md` as their task. Then re-run spec-reviewer.
- Stop after 2 fix rounds and hand remaining failures to the user.

## Finish
Report a table: stage, agent(s), outcome. Suggest the commits from CLAUDE.md
(`spec(NNN)`, `design(NNN)`, `feat(NNN)`, `test(NNN)`, `review(NNN)`).
