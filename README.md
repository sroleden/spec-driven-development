# ⚡ Dark Spark — Spec-Driven Development with Claude Code

A sample **event ticketing** app (FastAPI · SQLModel · Jinja2/HTMX) that exists to demonstrate
**spec-driven development** with Claude Code **skills** and a **multi-agent team**
(spec-writer → designer → backend-coder ∥ ui-coder ∥ tester → spec-reviewer).

## What's where

| Path | What it shows |
|------|---------------|
| [`CLAUDE.md`](CLAUDE.md) | The project "constitution": pipeline, rules, file ownership, conventions |
| [`.claude/skills/`](.claude/skills) | 7 skills — the *how* of each stage, plus the `build-feature` orchestrator |
| [`.claude/agents/`](.claude/agents) | 6 agents — the *who*: role, tools, model, owned files |
| [`specs/`](specs) | One folder per feature: `idea → spec → design → tasks → review` |
| [`app/`](app), [`tests/`](tests) | The code the agents produced, tests named after acceptance criteria |

| Feature | How it was built |
|---------|------------------|
| 001 Event catalog | Sequential, one stage at a time (baseline) |
| 002 Seat reservation | backend-coder, ui-coder and tester **in parallel**, then spec-reviewer |
| 003 Waitlist | Full pipeline via `/build-feature 003` |

## Run the app

```bash
uv sync
uv run python -m app.seed                 # demo data, incl. a sold-out event
uv run uvicorn app.main:app --reload      # http://localhost:8000  (API docs at /docs)
uv run pytest                             # acceptance tests
```

## Run the SDD pipeline yourself

```bash
mkdir specs/004-my-feature && $EDITOR specs/004-my-feature/idea.md
claude
> /build-feature 004
```
Or step by step: *"Use the spec-writer agent for feature 004"*, then designer, then the three lane agents
in parallel, then spec-reviewer.
