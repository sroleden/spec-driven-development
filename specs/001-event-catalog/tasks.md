# Tasks 001 — Event catalog

**Spec:** [spec.md](spec.md) · **Design:** [design.md](design.md)

Lanes run **in parallel**; each agent only edits files it owns (see CLAUDE.md) and only ticks its own lane.
*(Feature 001 was built sequentially — backend, then ui, then test — as the "before" baseline.)*

## backend — `backend-coder`
- [x] TB1 Add `EventBase`, `Event`, `EventCreate`, `EventRead` to `app/models.py` (AC1.1, AC1.8)
- [x] TB2 Add `create_event` with the five validation rules in design order (AC1.1–AC1.5)
- [x] TB3 Add `list_upcoming`, `get_event`, `seats_available`, `to_read` (AC1.6–AC1.9)
- [x] TB4 Add `POST /api/events`, `GET /api/events`, `GET /api/events/{id}` (AC1.1–AC1.9)

## ui — `ui-coder`
- [x] TU1 Event list page `/` with cards and empty state (AC1.6, AC1.7)
- [x] TU2 Create form `/events/new` with error display and redirect on success (AC1.1–AC1.5)
- [x] TU3 Event detail page and 404 page (AC1.8, AC1.9)

## test — `tester`
- [x] TT1 API tests for creation happy path and each validation error (AC1.1–AC1.5)
- [x] TT2 API tests for listing, empty list, details, not found (AC1.6–AC1.9)
- [x] TT3 Page tests for list, empty state, form error, detail, 404 (AC1.1, AC1.4, AC1.7–AC1.9)

## Traceability
| AC    | backend  | ui  | test     |
|-------|----------|-----|----------|
| AC1.1 | TB1–TB4  | TU2 | TT1, TT3 |
| AC1.2 | TB2, TB4 | TU2 | TT1      |
| AC1.3 | TB2, TB4 | TU2 | TT1      |
| AC1.4 | TB2, TB4 | TU2 | TT1, TT3 |
| AC1.5 | TB2, TB4 | TU2 | TT1      |
| AC1.6 | TB3, TB4 | TU1 | TT2      |
| AC1.7 | TB3, TB4 | TU1 | TT2, TT3 |
| AC1.8 | TB3, TB4 | TU3 | TT2, TT3 |
| AC1.9 | TB3, TB4 | TU3 | TT2, TT3 |
