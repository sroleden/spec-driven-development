# Review 003 — Waitlist
**Result:** PASS (with non-blocking findings)   ·   **Tests:** 114 passed, 0 failed (whole suite, 1.50s)   ·   **Lint:** clean (`ruff check .`: all checks passed; `ruff format --check .`: 20 files already formatted)

Reviewed the uncommitted working tree on branch `live-demo` against `spec.md` (Status: Approved, AC3.1–AC3.12),
`design.md` and `tasks.md`. All tasks TB1–TB7, TU1–TU4 and TT1–TT5 are ticked. Every changed file sits inside its
owner's lane (backend: `app/models.py`, `app/services/waitlist.py`, `app/services/reservations.py`,
`app/routes/api.py`; ui: `app/routes/pages.py`, `app/templates/**`; tester: `tests/test_003_waitlist.py`).

## Acceptance criteria

| AC | Test (`tests/test_003_waitlist.py`) | Code | Verdict | Owner / fix |
|----|------|------|---------|-------------|
| AC3.1 | `test_AC3_1_join_creates_waiting_entry_last_in_line` (full body: 8-char upper-case code, `status` waiting, `position` 1), `test_AC3_1_second_and_third_joiners_get_next_positions` (positions 1,2,3 = last), `test_AC3_1_codes_are_unique`, `test_AC3_1_boundary_seat_counts_accepted` (1, 10), `test_AC3_1_page_join_redirects_to_waiting_card` (303 → "Status: Waiting", "Position in line: 1"), `test_AC3_1_page_join_form_only_when_sold_out` | `app/services/waitlist.py:27-61` (`join`), `:20-24` (code), `:82-92` (`position`); `app/routes/api.py` `join_waitlist` (201); `app/routes/pages.py` `join_waitlist` (303); `app/templates/events/detail.html` waitlist form in sold-out branch | PASS | — |
| AC3.2 | `test_AC3_2_join_rejected_while_seats_available`, `test_AC3_2_rejected_when_one_seat_left` (409, exact message incl. U+2014), `test_AC3_2_page_no_join_form_when_seats_available` | `waitlist.py:43-44`; form only in `seats_available == 0` branch of `events/detail.html` | PASS | — |
| AC3.3 | `test_AC3_3_seats_out_of_range_rejected` (0, -1, 11 → 422 exact message), `test_AC3_3_page_seats_out_of_range_error` (incl. non-integer → 0) | `waitlist.py:39-40` (reuses `MIN_SEATS`/`MAX_SEATS` from 002); `pages.py` int fallback to 0 | PASS | — |
| AC3.4 | `test_AC3_4_blank_name_rejected` ("", whitespace), `test_AC3_4_invalid_email_rejected` (4 cases), `test_AC3_4_name_checked_before_email_before_seats`, `test_AC3_4_page_blank_name_and_bad_email_errors` | `waitlist.py:34-38` (strip, `EMAIL_RE` from 002) | PASS | — |
| AC3.5 | `test_AC3_5_duplicate_waiting_email_rejected`, `test_AC3_5_duplicate_email_case_insensitive`, `test_AC3_5_page_duplicate_email_error` (409, `.alert.error`) | `waitlist.py:45-53` (waiting entries only, `lower()` match) | PASS | — (see F4 on labelling) |
| AC3.6 | `test_AC3_6_lookup_waiting_entry` (full body: event name, seats, waiting, position 1), `test_AC3_6_position_reflects_place_in_line`, `test_AC3_6_lookup_is_case_insensitive`, `test_AC3_6_page_waiting_card_one_seat_wording_and_position` | `waitlist.py:64-68`, `:127-138` (`to_read`); `partials/waitlist_card.html:3-13`; `waitlist/detail.html` | PASS | — |
| AC3.7 | `test_AC3_7_lookup_promoted_entry_shows_booking_reference` (status promoted, `booking_code` resolves via `/api/reservations/{code}` to a confirmed reservation with the entry's seats/email/event), `test_AC3_7_page_promoted_card_shows_booking_reference` ("Status: Promoted", link, no leave button/position) | `waitlist.py:127-138`; `waitlist_card.html:14-15` | PASS | — |
| AC3.8 | `test_AC3_8_lookup_unknown_code_404`, `test_AC3_8_leave_unknown_code_404` (exact body), `test_AC3_8_page_unknown_code_404_full_page`, `test_AC3_8_page_htmx_leave_unknown_404_partial` | `waitlist.py:64-68` (`leave` reuses it, `:72`); `pages.py` `waitlist_detail` / `leave_waitlist` NotFound branches | PASS | — |
| AC3.9 | `test_AC3_9_only_first_in_line_promoted_when_only_it_fits` (4 freed, first wants 3 → promoted, second (3) waits, available = 1 = 4 − 3), `test_AC3_9_cancel_promotes_first_waiting_entry`, `test_AC3_9_promoted_reservation_is_confirmed_with_entry_details`, `test_AC3_9_cancelling_promoted_reservation_promotes_next`, `test_AC3_9_cancel_response_unchanged`, `test_AC3_9_cancel_without_waitlist_just_frees_seats`, `test_AC3_9_seats_never_exceed_capacity` | `waitlist.py:95-124` (`promote`); hook `app/services/reservations.py:58,65` (same transaction, commit at `:66`) | PASS | — (see F3) |
| AC3.10 | `test_AC3_10_non_fitting_first_entry_is_skipped_and_keeps_place` (skipped entry stays waiting, position 1), `test_AC3_10_repeats_until_nothing_fits` (3,3,1,2 with 5 freed → P,W,P,W; skipped keep positions 1 and 2; available 1), `test_AC3_10_skipped_entry_promoted_by_later_cancellation` | `waitlist.py:105-109` (`continue` on non-fit, `break` at 0, `ORDER BY id`) | PASS | — |
| AC3.11 | `test_AC3_11_leave_removes_from_line_and_moves_others_up` (first leaves → others 1,2), `test_AC3_11_leaving_middle_entry_only_moves_those_behind` (front entry unchanged), `test_AC3_11_left_entry_is_not_promoted`, `test_AC3_11_page_htmx_leave_returns_left_card`, `test_AC3_11_page_htmx_leave_promoted_409_card` | `waitlist.py:71-79` (status `left`), `:82-92` (position counts only waiting), `:100-104` (promotion only considers waiting); `pages.py` `leave_waitlist` | PASS | — (see F1) |
| AC3.12 | `test_AC3_12_started_sold_out_event_rejected` (event inserted with past `starts_at`, 409 exact message), `test_AC3_12_started_event_with_seats_reports_started_first`, `test_AC3_12_page_started_event_error` | `waitlist.py:41-42` (`starts_at <= now`, checked before "seats available") | PASS | — |

Spec business rules also have tests: unknown event → "Event not found" (`test_rule_join_unknown_event_404`,
`test_rule_page_join_unknown_event_404`); promoted entry cannot be left (`test_rule_leave_promoted_entry_rejected`);
confirmed-reservation holder may join (`test_rule_email_with_confirmed_reservation_may_join`, spec Decisions).

## Other findings

### F1 — Soft delete (`left` status) vs AC3.11: no conflict. The user-visible wording beyond the spec is untraced (owner: `designer`, non-blocking)
- **Not a conflict.** AC3.11 says the entry is "removed from the line". The spec's own business rules define the
  line: "position in line counts only Waiting entries", and an entry "has the status Waiting or Promoted (or is
  left, in which case it is no longer in the line)". So the spec already allows for a "left" state and does not
  ask for the row to be deleted. Keeping the row with status `left` takes it out of the line in every way the spec
  can observe: `position()` skips it, `promote()` skips it (`test_AC3_11_left_entry_is_not_promoted`), and the
  AC3.5 duplicate check skips it. The *Then* clause holds.
- **Not untraced:** "Only waiting entries can be left" is spec text (business rules, for promoted entries).
- **Untraced (no AC or rule backs it):** (a) looking up a left entry returns 200 / a "Status: Left" card rather
  than "Waitlist entry not found". A literal reading of "removed" could expect the AC3.8 message here, so this is
  the one real ambiguity; (b) the "You have left the waitlist" success banner; (c) leaving an already-left entry
  returns "Only waiting entries can be left", although the spec states that rule only for promoted entries;
  (d) the same email can rejoin after leaving. The designer recorded all of these under Risks / notes rather than
  silently diverging, and the coders and tester followed the contract. This is scope added at design time, and
  no code is wrong. **Fix:** `designer` should take (a)–(d) to the human/`spec-writer` to be added to spec.md
  §Decisions (or one AC), so every visible behaviour traces back to the spec. No code change is needed unless the
  human decides a left entry should look up as "not found".

### F2 — The approved spec was amended but not committed (owner: `spec-writer` / human, process)
`git diff specs/003-waitlist/spec.md` against commit `8fb09cd spec(003): waitlist` shows that AC3.12, the
"has not started" rule, the whole §Decisions section and two out-of-scope lines were added after the spec commit,
and are still uncommitted. `design.md` and `tasks.md` are untracked as well. The working tree is internally
consistent (status Approved, no open questions), but the committed history does not show that the human approved
AC3.12. **Fix:** confirm the human approved the amendment, then commit it as `spec(003): ...` and the design as
`design(003): ...` before the `feat`/`test`/`review` commits.

### F3 — Promotion edge cases: checked, no defect found (informational)
- **Over-capacity:** `promote` measures each candidate against the running total
  `available = capacity − confirmed seats` (`waitlist.py:98,108,122`), and `cancel` commits once
  (`reservations.py:65-66`). `seats_available` sees the pending cancellation through autoflush (default on).
  `test_AC3_9_only_first_in_line_promoted_when_only_it_fits` would fail if the fit check were missing (available
  would go to −2). Capacity cannot be edited and `reserve` checks availability, so `available` cannot start
  negative. If it ever did, the `break` at `:106` stops safely.
- **Order of skipped entries:** a single pass in ascending `id` with `continue` matches "repeating until no
  remaining waiting entry fits", because `available` only goes down during a pass. Skipped entries are not
  touched, so they keep their place (`test_AC3_10_repeats_until_nothing_fits` checks positions 1 and 2 after the
  pass).
- **Freed seats vs total seats available:** promotion uses all seats available, not only the seats this
  cancellation freed. That fits AC3.10 ("more seats than are available"), and
  `test_AC3_10_skipped_entry_promoted_by_later_cancellation` checks that seats add up across cancellations.
- **No stranded seats:** after every promotion, each remaining waiting entry wants more seats than are available.
  Joining requires 0 available, leaving frees no seats, and reserving only lowers availability. So no waiting
  entry can fit seats that are sitting idle.
- **Gap at spec level (owner: `spec-writer`, not a defect):** the leftover seats in that state (e.g. 1 seat free,
  the head of the line wants 2) can be booked straight through `POST /reservations` by someone not on the
  waitlist, and new attendees cannot join the waitlist meanwhile ("Seats are still available — reserve instead").
  The spec allows this. If "fair order" should cover it, it needs a new AC.
- Promotion still runs for events that have already started. The spec only says waiting entries do not lapse, so
  this is acceptable.

### F4 — The tests check the spec, with minor labelling and strength issues (owner: `tester`, non-blocking)
The tests were written after the code, so none was seen failing first. I judged them on whether they would catch
plausible wrong implementations. They use only the public API and pages. They assert the spec's messages
verbatim (including the em dash) and expected values worked out from the spec's rules, not from the code's output.
Each of these mutants would fail at least one test: `break` instead of `continue` on non-fit; no fit check;
wrong join order; position counting non-waiting entries; promotion not committed; duplicate check counting left
entries; "started" checked with `<` instead of `<=` (the fixture uses now − 1h, so this one is only partly
covered). Nits:
- `test_AC3_5_same_email_other_event_allowed`, `test_AC3_5_same_email_can_rejoin_after_leaving` and
  `test_AC3_12_started_event_with_seats_reports_started_first` carry AC IDs, but they test design decisions
  (the opposite case, or a Given clause the AC does not have: the AC3.12 one uses an event with seats left, not a
  sold-out one). Rename them to `test_rule_*` / `test_design_*` so AC reports do not count them as evidence.
- `test_AC3_9_seats_never_exceed_capacity` does not exercise an over-capacity risk: the freed 2 seats exactly fit
  the first 2-seat entry. Use a scenario where later entries would overflow if each were not checked against the
  running total (e.g. 3 freed, entries of 2, 2, 1 → expect P, W, P and available 0).
- No boundary test for `starts_at == now` (AC3.12 says "not in the future"). `join` accepts `now` but the test
  goes through the API. A service-level test with an injected `now` would pin it down.

### F5 — Minor UI note (owner: `ui-coder`, informational, not required by design)
The detail page of a sold-out event that has already started still shows the "Join the waitlist" form, and
submitting it returns the AC3.12 error. This matches design.md (the form depends only on `seats_available == 0`),
so it is not a defect. Hiding the form would need a design change first.
