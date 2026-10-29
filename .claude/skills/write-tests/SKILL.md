---
name: write-tests
description: Write pytest tests for a feature straight from its acceptance criteria and the design.md contract — without reading the implementation — so tests verify the spec rather than mirror the code. Use for the test lane of tasks.md or when asked to write acceptance tests.
argument-hint: "[feature number]"
---

# Write acceptance tests from the spec

You are the independent check. **Do not open the new feature's implementation in `app/`** — write tests
from `spec.md` + `design.md` only. (You may read `tests/conftest.py` and existing tests for patterns.)

## Procedure

1. Read `specs/NNN-*/spec.md`, `design.md`, the **test** lane of `tasks.md`, and `tests/conftest.py`.
2. Create `tests/test_NNN_<slug>.py`. For every AC write at least one test named
   `test_AC<N>_<n>_<behaviour>` (e.g. `test_AC3_2_cancel_promotes_first_in_line`).
   - Docstring = the AC's Given/When/Then, copied verbatim.
   - Arrange via the public API (or the `session` fixture for setup only), act via HTTP, assert on the
     **status code, JSON body and visible text exactly as written in design.md**.
   - Cover every error status listed in the design.
3. Run `uv run pytest tests/test_NNN_<slug>.py -q`. Failures are expected if the coders are not done yet;
   a failure caused by *your* mistake (typo, wrong fixture) is not — fix those.
4. Tick your tasks in `tasks.md`. Report: tests written per AC, and current pass/fail.
