# Tasks 002 — Seat reservation

**Spec:** [spec.md](spec.md) · **Design:** [design.md](design.md)

Lanes run **in parallel**; each agent only edits files it owns (see CLAUDE.md) and only ticks its own lane.

## backend — `backend-coder`
- [x] TB1 Add `ReservationStatus`, `Reservation`, `ReservationCreate`, `ReservationRead` to `app/models.py` (AC2.1, AC2.6)
- [x] TB2 Add `reserve` with validation order and code generation in `app/services/reservations.py` (AC2.1–AC2.5)
- [x] TB3 Add `get_by_code`, `cancel`, `held_seats`, `to_read` (AC2.6–AC2.9)
- [x] TB4 Make `events.seats_available` subtract confirmed reservations (AC2.1, AC2.4, AC2.8)
- [x] TB5 Add the three reservation endpoints to `app/routes/api.py` (AC2.1–AC2.9)

## ui — `ui-coder`
- [x] TU1 Reservation form / sold-out state in `events/detail.html` (AC2.1, AC2.4)
- [x] TU2 `POST /events/{id}/reserve` page route with error re-render and redirect (AC2.1–AC2.5)
- [x] TU3 `reservations/detail.html` confirmation page + 404 (AC2.6, AC2.7)
- [x] TU4 HTMX cancel with `partials/reservation_card.html` (AC2.8, AC2.9)
- [x] TU5 *(rev. 2)* Cancel always returns the card partial (200/409/404); add `htmx-config` meta to `base.html` so 404/409/422 swap (AC2.7, AC2.9)

## test — `tester`
- [x] TT1 API tests: reserve happy path + each validation/conflict error (AC2.1–AC2.5)
- [x] TT2 API tests: lookup, not found, cancel, double cancel, seats restored (AC2.6–AC2.9)
- [x] TT3 Page tests: form, sold-out state, form error, confirmation, cancel partial, 404 (AC2.1, AC2.3, AC2.4, AC2.6–AC2.8)
- [x] TT4 *(rev. 2)* Assert HTMX cancel status codes 200/409/404, that the 404 response is a partial (no `<html>`), and that pages declare the htmx-config swapping 409 (AC2.7, AC2.8, AC2.9)

## Traceability
| AC    | backend       | ui       | test     |
|-------|---------------|----------|----------|
| AC2.1 | TB1, TB2, TB4, TB5 | TU1, TU2 | TT1, TT3 |
| AC2.2 | TB2, TB5      | TU2      | TT1      |
| AC2.3 | TB2, TB5      | TU2      | TT1, TT3 |
| AC2.4 | TB2, TB4, TB5 | TU1, TU2 | TT1, TT3 |
| AC2.5 | TB2, TB5      | TU2      | TT1      |
| AC2.6 | TB1, TB3, TB5 | TU3      | TT2, TT3 |
| AC2.7 | TB3, TB5      | TU3, TU4 | TT2, TT3 |
| AC2.8 | TB3, TB4, TB5 | TU4      | TT2, TT3 |
| AC2.9 | TB3, TB5      | TU4      | TT2      |
