# Review 002 — Seat reservation
**Result:** PASS   ·   **Tests:** 53 passed, 0 failed (whole suite, 001 + 002)   ·   **Lint:** clean (`ruff check`, `ruff format --check`)

| AC    | Test | Code | Verdict | Owner / fix |
|-------|------|------|---------|-------------|
| AC2.1 | `test_AC2_1_reserve_confirms_and_drops_seats` (full body + 8-char A–Z0–9 code + seats 100→98), `test_AC2_1_codes_are_unique`, `test_AC2_1_can_reserve_exactly_ten_and_exactly_remaining`, `test_AC2_1_page_form_shown_and_reserve_redirects` (303 → confirmation page, seats drop) | `app/services/reservations.py:22-47`, `:15` (code gen), `app/services/events.py:47`, `app/routes/api.py:27`, `app/routes/pages.py:93-118`, `app/templates/events/detail.html:21-26` | PASS | — |
| AC2.2 | `test_AC2_2_seats_out_of_range_rejected` (0, −1, 11; exact detail; seats unchanged) | `app/services/reservations.py:33-34`, `app/routes/pages.py:108-111` (non-numeric form value → 0 → same message) | PASS | — |
| AC2.3 | `test_AC2_3_not_enough_seats_left` ("Only 3 seats left", 409), `test_AC2_3_page_reserve_error_shown_in_alert` | `app/services/reservations.py:38-39`, `app/routes/pages.py:115-117`, `app/templates/events/detail.html:17` | PASS | — |
| AC2.4 | `test_AC2_4_sold_out_reserve_rejected`, `test_AC2_4_page_sold_out_state` (message shown, no "Reserve seats"), `test_AC2_4_page_reserve_when_sold_out_rejected` | `app/services/reservations.py:36-37`, `app/templates/events/detail.html:10-11,18-19` | PASS | — |
| AC2.5 | `test_AC2_5_blank_name_rejected` ("" and whitespace), `test_AC2_5_invalid_email_rejected` (6 invalid forms) | `app/services/reservations.py:10,28-32` | PASS | — |
| AC2.6 | `test_AC2_6_lookup_by_code` (event name, seats, status), `test_AC2_6_lookup_is_case_insensitive`, `test_AC2_6_page_confirmation_shows_details`, `test_AC2_6_page_confirmation_singular_seat` | `app/services/reservations.py:50-54,75-77`, `app/routes/api.py:32`, `app/routes/pages.py:130-140`, `app/templates/partials/reservation_card.html:2-5` | PASS | — |
| AC2.7 | `test_AC2_7_lookup_unknown_code_404`, `test_AC2_7_cancel_unknown_code_404`, `test_AC2_7_page_unknown_code_404`, `test_AC2_7_page_cancel_unknown_code` | `app/services/reservations.py:52-53`, `app/routes/pages.py:133-135,146-148` | PASS | — (see finding 1: page-cancel status not asserted) |
| AC2.8 | `test_AC2_8_cancel_restores_seats` (status cancelled, 6→10, persisted), `test_AC2_8_cancel_sold_out_event_reopens_it`, `test_AC2_8_page_cancel_partial` ("Reservation cancelled", no cancel button) | `app/services/reservations.py:57-65,68-72`, `app/services/events.py:47`, `app/routes/api.py:37`, `app/routes/pages.py:143-152`, `app/templates/partials/reservation_card.html:7-11` | PASS | — |
| AC2.9 | `test_AC2_9_double_cancel_rejected` (409, exact detail, seats not double-restored), `test_AC2_9_page_double_cancel_shows_error_in_partial` | `app/services/reservations.py:59-60`, `app/routes/pages.py:149-151`, `app/templates/partials/reservation_card.html:6` | PASS | — (see finding 1: UI path does not render in a real browser) |

All code matches the design contract: model fields/`StrEnum` (`app/models.py`), service functions and
error order (NotFound → name → email → seats → sold out → only X), API status codes and bodies, page
routes (303 on success, 422/409 re-render with `.alert.error`, 404 `not_found.html`), and the UI states table.

## Other findings
1. **Design gap — HTMX cancel error status codes (designer).** design.md says cancel errors are
   "rendered inside the same partial" but gives no status code. ui-coder chose 409 for already-cancelled
   (`app/routes/pages.py:151`) and a full-page 404 `not_found.html` for unknown codes (`:148`). The page
   loads htmx 2.0.4, whose default `responseHandling` does **not swap 4xx responses** — so in a real
   browser the "Reservation is already cancelled" partial is never shown (click does nothing), and the 404
   would be a whole page, not a partial, if it were swapped. Tests pass because `TestClient` just reads the
   body; `test_AC2_7_page_cancel_unknown_code` and `test_AC2_9_page_double_cancel_shows_error_in_partial`
   do not assert a status code at all. Only reachable via a stale tab, so non-blocking. Fix: designer
   decides between returning the partial with 200, or configuring `htmx.config.responseHandling` for 409,
   and pins the status codes in design.md; tester then asserts them.
2. **Pluralisation — "Only 1 seats left" (designer / spec-writer).** spec.md and design.md mandate the literal
   "Only X seats left", and `app/services/reservations.py:39` follows it, so X=1 yields "Only 1 seats left".
   This is inconsistent with the confirmation page, where the design explicitly asks for "1 seat"
   (`reservation_card.html:4`). Correct per contract; a spec amendment ("Only 1 seat left") is
   needed before anyone changes code.
3. **Ownership / packaging.** The `feat(002)` commit touches only backend + ui files plus `tasks.md`, and the
   `test(002)` commit touches only `tests/test_002_seat_reservation.py`. All 12 tasks are ticked. But the
   tester's TT1–TT3 ticks were committed in `feat(002)`, not `test(002)`. This comes from the parallel lanes
   sharing one working tree. Cosmetic.
4. Minor UI: when a POST to a sold-out event is rejected, "This event is sold out" appears twice, once in the
   error alert and once in the sold-out block (`events/detail.html:17,19`). The sold-out block also reuses
   `.alert.error`, although nothing has gone wrong. No AC impact.
5. Minor tests: `test_AC2_1_unknown_event_404` tests the "Event not found" business rule, not AC2.1. Form-level
   errors for AC2.2/AC2.5 are untested, which is consistent with TT3's scope. They share the AC2.3 code path
   (`pages.py:115-117`).
6. No scope creep found. Case-insensitive lookup and `created_at` are both in design.md. Untracked
   `specs/003-waitlist/` and `presentation/` are outside this review.

---

## Re-review — round 1 (after design rev. 2)
**Result:** PASS   ·   **Tests:** 54 passed, 0 failed   ·   **Lint:** clean

| Finding | Routed to | Resolution | Evidence |
|---------|-----------|------------|----------|
| 1 — HTMX cancel errors not visible in a browser | designer → ui-coder ∥ tester | Contract pins 200/409/404 for the cancel partial; `base.html` declares `htmx-config` swapping 404/409/422 | `app/routes/pages.py` cancel route, `app/templates/base.html`, `test_AC2_7_page_cancel_unknown_code`, `test_AC2_9_page_double_cancel_shows_error_in_partial`, `test_AC2_9_pages_declare_htmx_config_swapping_409` |
| Misfiled test `test_AC2_1_unknown_event_404` | tester | Renamed `test_rule_reserve_unknown_event_404` | `tests/test_002_seat_reservation.py` |
| 2 — "Only 1 seats left" | spec-writer | **Open** — needs a spec change first; left as-is to match the approved spec | — |
