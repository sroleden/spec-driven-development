# Review 001 — Event catalog
**Result:** PASS   ·   **Tests:** 20 passed, 0 failed   ·   **Lint:** clean

| AC    | Test | Code | Verdict | Owner / fix |
|-------|------|------|---------|-------------|
| AC1.1 | `test_AC1_1_create_event_with_all_seats_available`, `test_AC1_1_create_form_redirects_to_event_page` | `app/services/events.py:12`, `app/routes/api.py:11`, `app/routes/pages.py:38` | PASS | — |
| AC1.2 | `test_AC1_2_capacity_out_of_range_rejected` (0, −5, 10001), `test_AC1_2_capacity_boundaries_accepted` | `app/services/events.py:12` | PASS | — |
| AC1.3 | `test_AC1_3_past_start_rejected` | `app/services/events.py:12` | PASS | — |
| AC1.4 | `test_AC1_4_blank_name_or_venue_rejected`, `test_AC1_4_form_shows_validation_error` | `app/services/events.py:12`, `app/templates/events/new.html` | PASS | — |
| AC1.5 | `test_AC1_5_negative_price_rejected`, `test_AC1_5_free_event_allowed` | `app/services/events.py:12` | PASS | — |
| AC1.6 | `test_AC1_6_only_upcoming_events_soonest_first`, `test_AC1_6_list_page_shows_cards` | `app/services/events.py:33`, `app/templates/events/list.html` | PASS | — |
| AC1.7 | `test_AC1_7_no_upcoming_events_api_empty`, `test_AC1_7_list_page_empty_state` | `app/templates/events/list.html` | PASS | — |
| AC1.8 | `test_AC1_8_event_details` | `app/services/events.py:50`, `app/templates/events/detail.html` | PASS | — |
| AC1.9 | `test_AC1_9_unknown_event_not_found`, `test_AC1_9_unknown_event_page_404` | `app/services/events.py:39`, `app/routes/pages.py:74` | PASS | — |

## Other findings
- All 10 tasks ticked; no files edited outside lane ownership.
- Contract change during build: `starts_at` became pydantic `NaiveDatetime` — design.md updated to match
  (see *Risks / notes*). Good example of the contract being corrected rather than silently diverging.
- AC1.8 is checked through the API only; the detail page is covered indirectly by
  `test_AC1_1_create_form_redirects_to_event_page`. Acceptable.
