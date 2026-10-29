---
name: verify-against-spec
description: Verify a finished feature against its spec — run the tests and produce review.md mapping every acceptance criterion to test and code evidence with PASS/FAIL, routing each failure to the owning agent. Use after implementation, or when asked to review a feature against its spec.
argument-hint: "[feature number]"
---

# Verify a feature against its spec

## Procedure

1. Read `specs/NNN-*/spec.md`, `design.md`, `tasks.md`.
2. Run `uv run pytest -q` (whole suite — regressions count) and `uv run ruff check .`.
3. For **each AC**:
   - Find the test(s) named `test_AC<N>_<n>_*`. Missing test → FAIL (owner: tester).
   - Check the test actually asserts the AC's *Then* clause (not just status 200).
   - Find the code that satisfies it (file:line). Check it matches the design contract.
   - Verdict: PASS / FAIL, and for FAIL the owning agent (`backend-coder`, `ui-coder`, `tester`, or
     `designer` if the contract itself is wrong).
4. Also check: unticked tasks, files edited outside an agent's ownership, scope creep beyond the spec.
5. Write `specs/NNN-*/review.md`:

```markdown
# Review NNN — <Feature name>
**Result:** PASS | FAIL   ·   **Tests:** <x passed, y failed>   ·   **Lint:** clean | <issues>

| AC | Test | Code | Verdict | Owner / fix |
|----|------|------|---------|-------------|

## Other findings
```

6. Reply with the result line and the list of failures with owners. Do **not** fix code yourself.
