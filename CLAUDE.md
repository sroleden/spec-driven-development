# Dark Spark — project constitution

Dark Spark is an **event ticketing** sample app (FastAPI + Jinja2/HTMX + SQLite) used to demonstrate
**spec-driven development (SDD)** with Claude Code skills and agents. The specs are the source of truth;
code is a derived artifact that must trace back to an acceptance criterion.

## The SDD pipeline

```
idea.md → spec.md → design.md + tasks.md → code ∥ tests → review.md
          spec-writer   designer             backend-coder   spec-reviewer
                                             ui-coder
                                             tester
```

| Stage    | Agent (who)                            | Skill (how)                          | Output                          |
|----------|----------------------------------------|--------------------------------------|---------------------------------|
| Specify  | `spec-writer`                          | `write-spec`                         | `specs/NNN-x/spec.md`           |
| Design   | `designer`                             | `design-feature`, `break-into-tasks` | `design.md`, `tasks.md`         |
| Build    | `backend-coder`, `ui-coder` (parallel) | `implement-task`                     | code in `app/`                  |
| Test     | `tester` (parallel with coders)        | `write-tests`                        | `tests/test_NNN_*.py`           |
| Verify   | `spec-reviewer`                        | `verify-against-spec`                | `review.md`                     |

`/build-feature NNN` (skill `build-feature`) orchestrates the whole pipeline.

## Rules (all agents)

1. **No code without a spec.** Every change to `app/` must be justified by a task in `specs/NNN-*/tasks.md`,
   which links to an acceptance criterion (AC) ID in `spec.md`.
2. **AC IDs are the thread.** ACs are numbered `AC<feature>.<n>` (e.g. `AC3.2`). Tasks cite them, test names
   carry them (`test_AC3_2_...`), and `review.md` reports on each one.
3. **The design contract is binding.** Coders and the tester build against `design.md` (data model, API
   contract, UI states), not against each other's code. If the contract is wrong, stop and report it — do not
   silently diverge.
4. **File ownership** — agents working in parallel only edit files they own:
   - `spec-writer`, `designer`: `specs/**`
   - `backend-coder`: `app/models.py`, `app/db.py`, `app/services/**`, `app/routes/api.py`, `app/main.py`
   - `ui-coder`: `app/templates/**`, `app/static/**`, `app/routes/pages.py`
   - `tester`: `tests/**`
   - `spec-reviewer`: `specs/NNN-*/review.md` only
   Each agent ticks its own checkboxes in `tasks.md`.
5. **Humans approve specs.** Never move past `spec.md` while it has open questions.
6. Keep it small: this is a demo app. No auth, no payments, no migrations framework.

## Stack & conventions

- Python ≥3.12, managed with **uv**. Run things with `uv run ...`.
- `app/models.py` — SQLModel tables. `app/db.py` — engine, `get_session` and the `SessionDep` annotated dependency for routes (SQLite, `DARK_SPARK_DB`
  env var, default `dark_spark.db`).
- `app/services/` — business rules as plain functions taking a `Session`. Raise `app.services.errors`
  exceptions (`NotFound`, `Conflict`, `ValidationFailed`); routes translate them to HTTP 404/409/422.
- `app/routes/api.py` — JSON API under `/api`. `app/routes/pages.py` — HTML pages; forms post to page routes
  and HTMX swaps partials from `app/templates/partials/`.
- Templates use Jinja2, HTMX from CDN, one stylesheet `app/static/style.css`. No JS build step.
- Tests: pytest + FastAPI `TestClient`, fresh in-memory DB per test via the `client`/`session` fixtures in
  `tests/conftest.py`.

## Commands

```bash
uv sync                                   # install
uv run uvicorn app.main:app --reload      # run app at http://localhost:8000
uv run pytest                             # tests
uv run ruff check . && uv run ruff format --check .
uv run python -m app.seed                 # demo data (includes a sold-out event)
```

## Commit style

One commit per pipeline stage: `spec(003): ...`, `design(003): ...`, `feat(003): ...`, `test(003): ...`,
`review(003): ...`.
