# Tasks 003 — Waitlist

**Spec:** [spec.md](spec.md) · **Design:** [design.md](design.md)

Lanes run **in parallel**; each agent only edits files it owns (see CLAUDE.md) and only ticks its own lane.

## backend — `backend-coder`
- [x] TB1 Add `WaitlistStatus`, `WaitlistEntry`, `WaitlistJoin`, `WaitlistEntryRead` to `app/models.py` (AC3.1, AC3.6, AC3.7)
- [x] TB2 Add `join` with the design's validation order and waitlist-code generation in `app/services/waitlist.py` (AC3.1–AC3.5, AC3.12)
- [x] TB3 Add `get_by_code`, `position`, `to_read` (AC3.1, AC3.6–AC3.8)
- [x] TB4 Add `leave` (soft delete to `left`; `Conflict` for promoted/left entries) (AC3.8, AC3.11)
- [x] TB5 Add `promote` (join order, skip non-fitting entries, create confirmed reservations, no commit) (AC3.9, AC3.10)
- [x] TB6 Call `waitlist.promote` from `reservations.cancel` before its commit, keeping cancel's contract unchanged (AC3.9, AC3.10)
- [x] TB7 Add `POST /api/events/{event_id}/waitlist`, `GET /api/waitlist/{code}`, `POST /api/waitlist/{code}/leave` to `app/routes/api.py` (AC3.1–AC3.8, AC3.11, AC3.12)

## ui — `ui-coder`
- [x] TU1 Waitlist form ("Join the waitlist" / "Join waitlist") in the sold-out branch of `events/detail.html`, absent when seats are available (AC3.1, AC3.2)
- [x] TU2 `POST /events/{id}/waitlist` page route: 303 to `/waitlist/{code}`, error re-render with 409/422, 404 for unknown event (AC3.1–AC3.5, AC3.12)
- [x] TU3 `partials/waitlist_card.html` with Waiting / Promoted / Left states and `waitlist/detail.html` page + 404 (AC3.6, AC3.7, AC3.8)
- [x] TU4 `POST /waitlist/{code}/leave` HTMX route always returning the card partial (200 / 409 / 404) (AC3.8, AC3.11)

## test — `tester`
- [x] TT1 API tests: join happy path (code format, status, position = last) + each validation/conflict error incl. started event and unknown event (AC3.1–AC3.5, AC3.12)
- [x] TT2 API tests: lookup waiting (position 1 = next) and promoted (booking_code resolves to a confirmed reservation), unknown code on GET and leave (AC3.6, AC3.7, AC3.8)
- [x] TT3 API tests: promotion on cancel — first fitting entry promoted, seats_available drops, skip-and-continue ordering, skipped entry keeps position, cancelling a promoted reservation promotes again, never over capacity (AC3.9, AC3.10)
- [x] TT4 API tests: leave — status left, positions behind move up by one, leaving promoted/left entry 409 "Only waiting entries can be left", same email can rejoin after leaving (AC3.5, AC3.11)
- [x] TT5 Page tests: join form only when sold out, join → 303 → Waiting card, form errors in `.alert.error`, Promoted card with booking reference, HTMX leave 200/409/404 (404 is a partial), GET 404 page (AC3.1–AC3.4, AC3.6–AC3.8, AC3.11, AC3.12)

## Traceability
| AC     | backend            | ui            | test          |
|--------|--------------------|---------------|---------------|
| AC3.1  | TB1, TB2, TB3, TB7 | TU1, TU2      | TT1, TT5      |
| AC3.2  | TB2, TB7           | TU1, TU2      | TT1, TT5      |
| AC3.3  | TB2, TB7           | TU2           | TT1, TT5      |
| AC3.4  | TB2, TB7           | TU2           | TT1, TT5      |
| AC3.5  | TB2, TB7           | TU2           | TT1, TT4      |
| AC3.6  | TB1, TB3, TB7      | TU3           | TT2, TT5      |
| AC3.7  | TB1, TB3, TB7      | TU3           | TT2, TT5      |
| AC3.8  | TB3, TB4, TB7      | TU3, TU4      | TT2, TT5      |
| AC3.9  | TB5, TB6           | —             | TT3           |
| AC3.10 | TB5, TB6           | —             | TT3           |
| AC3.11 | TB4, TB7           | TU4           | TT4, TT5      |
| AC3.12 | TB2, TB7           | TU2           | TT1, TT5      |

AC3.9 and AC3.10 are backend-only (promotion runs inside the existing cancel flow; its visible result is the
Promoted card from TU3, covered under AC3.7).
