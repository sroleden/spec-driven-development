# Design 003 — Waitlist

**Spec:** [spec.md](spec.md)

## Data model — `app/models.py`
New section `# --- 003 waitlist ---` after the 002 models. No changes to `Event` or `Reservation`.

```python
class WaitlistStatus(StrEnum):
    waiting = "waiting"
    promoted = "promoted"
    left = "left"          # soft-deleted: no longer in the line (see Risks / notes)

class WaitlistEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)   # ascending id == join order
    event_id: int = Field(foreign_key="event.id", index=True)
    code: str = Field(index=True, unique=True)               # waitlist reference, 8 chars, A–Z0–9
    name: str
    email: str
    seats: int                                               # seats wanted, 1–10
    status: WaitlistStatus = WaitlistStatus.waiting
    reservation_id: int | None = Field(default=None, foreign_key="reservation.id")  # set on promotion
    created_at: NaiveDatetime = Field(default_factory=utcnow)

class WaitlistJoin(SQLModel):            # request body; rules enforced in the service
    name: str
    email: str
    seats: int

class WaitlistEntryRead(SQLModel):       # response body
    code: str
    event_id: int
    event_name: str
    name: str
    email: str
    seats: int
    status: WaitlistStatus
    position: int | None                 # 1 = next in line; null unless status == "waiting"
    booking_code: str | None             # Reservation.code; null unless status == "promoted"
```

Tables are created by the existing `init_db()` / `SQLModel.metadata.create_all` (no migrations).

## Service layer — `app/services/waitlist.py` (new)
Module constants reuse 002's: `from app.services.reservations import EMAIL_RE, CODE_ALPHABET`.
Top-level imports `from app.services import events, reservations` are safe (neither imports `waitlist` at
module level).

| Function | Behaviour | Errors (checked in this order) |
|----------|-----------|--------------------------------|
| `join(session, event_id: int, data: WaitlistJoin, now: datetime \| None = None) -> WaitlistEntry` | `now = now or utcnow()`. Strips name/email, generates a unique waitlist code (8 chars from `CODE_ALPHABET`, unique within `WaitlistEntry.code`), saves with status `waiting`, commits, refreshes. | `NotFound("Event not found")` → `ValidationFailed("Name is required")` → `ValidationFailed("A valid email is required")` (same `EMAIL_RE` as 002, applied to the stripped email) → `ValidationFailed("You can wait for between 1 and 10 seats")` → `Conflict("This event has already started")` if `event.starts_at <= now` → `Conflict("Seats are still available — reserve instead")` if `events.seats_available(session, event) > 0` → `Conflict("You are already on the waitlist for this event")` if a `waiting` entry exists for this `event_id` whose email equals the stripped email **case-insensitively** |
| `get_by_code(session, code: str) -> WaitlistEntry` | Case-insensitive lookup (`code.upper()`). Returns entries of any status, including `left`. | `NotFound("Waitlist entry not found")` |
| `leave(session, code: str) -> WaitlistEntry` | Sets status `left`, commits, refreshes. Positions of later entries move up automatically because `position` counts only `waiting` entries. | `NotFound("Waitlist entry not found")` → `Conflict("Only waiting entries can be left")` if status is `promoted` **or** `left` |
| `position(session, entry: WaitlistEntry) -> int \| None` | `None` unless `entry.status == waiting`; otherwise `1 +` count of `waiting` entries with the same `event_id` and `id < entry.id`. | — |
| `promote(session, event_id: int) -> list[WaitlistEntry]` | See *Promotion* below. Does **not** commit (caller commits). Returns the entries promoted, in join order (possibly empty). | — |
| `to_read(session, entry: WaitlistEntry) -> WaitlistEntryRead` | Adds `event_name`, `position` (via `position()`), and `booking_code` (the code of `Reservation` `entry.reservation_id`, or `None`). | — |

The em dash in "Seats are still available — reserve instead" is U+2014, with one space either side, exactly
as in spec.md.

### Promotion
```
promote(session, event_id):
    event     = session.get(Event, event_id)
    available = events.seats_available(session, event)       # sees the pending cancellation via autoflush
    promoted  = []
    for entry in waiting entries of event_id ORDER BY id ASC:
        if available <= 0: break
        if entry.seats > available: continue                  # skipped, keeps its place (AC3.10)
        r = Reservation(event_id=event_id, code=reservations._new_code(session),
                        name=entry.name, email=entry.email, seats=entry.seats)   # status confirmed
        session.add(r); session.flush()                       # r.id assigned
        entry.status = promoted; entry.reservation_id = r.id; session.add(entry)
        available -= entry.seats
        promoted.append(entry)
    return promoted
```
A single pass is equivalent to "repeat until no remaining waiting entry fits": `available` only decreases,
so an entry skipped earlier can never fit later in the same pass. Seats reserved never exceed capacity
because each promotion is checked against the remaining `available`.

### Hook into 002 — change to `app/services/reservations.py::cancel`
```python
def cancel(session: Session, code: str) -> Reservation:
    from app.services import waitlist  # local import: waitlist imports this module

    reservation = get_by_code(session, code)
    if reservation.status == ReservationStatus.cancelled:
        raise Conflict("Reservation is already cancelled")
    reservation.status = ReservationStatus.cancelled
    session.add(reservation)
    waitlist.promote(session, reservation.event_id)   # NEW — same transaction
    session.commit()
    session.refresh(reservation)
    return reservation
```
Signature, return value, errors and the API/page responses of cancel are **unchanged**. Because a promoted
entry's reservation is an ordinary `Reservation`, cancelling it goes through the same `cancel` and triggers
promotion again. No other 002 function changes.

## API contract — `app/routes/api.py`
All errors use the existing `ServiceError` handler in `app/main.py` (`{"detail": "..."}`). Request bodies that
fail Pydantic parsing (missing field, non-integer `seats`) get FastAPI's default 422, as in 002.

### `POST /api/events/{event_id}/waitlist`
Request:
```json
{"name": "Grace Hopper", "email": "grace@example.com", "seats": 2}
```
`201` →
```json
{"code": "W8X3KP2Q", "event_id": 1, "event_name": "Synthwave Night", "name": "Grace Hopper", "email": "grace@example.com", "seats": 2, "status": "waiting", "position": 3, "booking_code": null}
```
Errors:
- `404 {"detail": "Event not found"}`
- `422 {"detail": "Name is required"}`
- `422 {"detail": "A valid email is required"}`
- `422 {"detail": "You can wait for between 1 and 10 seats"}`
- `409 {"detail": "This event has already started"}`
- `409 {"detail": "Seats are still available — reserve instead"}`
- `409 {"detail": "You are already on the waitlist for this event"}`

### `GET /api/waitlist/{code}`
`200` → `WaitlistEntryRead`. Waiting:
```json
{"code": "W8X3KP2Q", "event_id": 1, "event_name": "Synthwave Night", "name": "Grace Hopper", "email": "grace@example.com", "seats": 2, "status": "waiting", "position": 1, "booking_code": null}
```
Promoted:
```json
{"code": "W8X3KP2Q", "event_id": 1, "event_name": "Synthwave Night", "name": "Grace Hopper", "email": "grace@example.com", "seats": 2, "status": "promoted", "position": null, "booking_code": "K7Q2M9XA"}
```
Errors: `404 {"detail": "Waitlist entry not found"}`.

### `POST /api/waitlist/{code}/leave`
No request body. `200` →
```json
{"code": "W8X3KP2Q", "event_id": 1, "event_name": "Synthwave Night", "name": "Grace Hopper", "email": "grace@example.com", "seats": 2, "status": "left", "position": null, "booking_code": null}
```
Errors: `404 {"detail": "Waitlist entry not found"}`, `409 {"detail": "Only waiting entries can be left"}`.

### Unchanged, but with new side effects
- `POST /api/reservations/{code}/cancel` — same request/response/errors as 002; now also runs promotion.
- `GET /api/events/{id}` — `seats_available` already counts confirmed reservations, so promoted
  reservations reduce it with no change.

## UI — `app/routes/pages.py`, `app/templates/`
| Route | Template | Behaviour |
|-------|----------|-----------|
| `GET /events/{id}` | `events/detail.html` (`event_actions` block) | When `seats_available == 0`: keep the existing `<p class="alert error">This event is sold out</p>` and add the waitlist form below it. When seats are available: unchanged reservation form, **no** waitlist form. |
| `POST /events/{id}/waitlist` (form: `name`, `email`, `seats`) | success → `303` to `/waitlist/{code}`; error → re-render `events/detail.html` with the message in `.alert.error`, status `409` for `Conflict`, `422` for `ValidationFailed`; unknown event → `404` `not_found.html` "Event not found" | Join. Non-integer `seats` is treated as `0` (service then returns the "between 1 and 10 seats" message), as in 002. Form values are passed back in `form` (same dict the reserve route uses). |
| `GET /waitlist/{code}` | `waitlist/detail.html` (new; extends `base.html`, link "← All events", includes the card partial); unknown → `404` `not_found.html` "Waitlist entry not found" | Lookup |
| `POST /waitlist/{code}/leave` (HTMX, `hx-target="#waitlist-entry"`, `hx-swap="outerHTML"`) | **always** returns partial `partials/waitlist_card.html` (never a full page): `200` left card · `409` card + "Only waiting entries can be left" · `404` card containing only "Waitlist entry not found" | Leave |

The 404/409/422 swapping is already configured by the `htmx-config` meta in `base.html` (002 rev. 2) — no
change needed.

Waitlist form markup (inside the sold-out branch of `events/detail.html`): `<h2>Join the waitlist</h2>` then
`<form class="stack" id="waitlist-form" method="post" action="/events/{{ event.id }}/waitlist">` with inputs
`name`, `email` (type email), `seats` (type number, default `form.seats or 1`) and
`<button type="submit">Join waitlist</button>`.

`partials/waitlist_card.html` — root element `<div class="card" id="waitlist-entry">`, context
`{"w": WaitlistEntryRead | None, "error": str | None}`.

```
/events/1 (sold out)                     /waitlist/W8X3KP2Q (waiting)
+------------------------------------+  +------------------------------------+
| Synthwave Night                    |  | Waitlist entry W8X3KP2Q            |
| Hall A · Tue 01 Dec 2026 · 20:00   |  | Synthwave Night                    |
| €25.00   [Sold out]                |  | 2 seats wanted · Grace Hopper      |
| This event is sold out             |  | Status: Waiting                    |
| Join the waitlist                  |  | Position in line: 3                |
| Name  [__________]                 |  | [Leave waitlist]                   |
| Email [__________]                 |  +------------------------------------+
| Seats [1]   [Join waitlist]        |
+------------------------------------+  /waitlist/W8X3KP2Q (promoted)
                                        +------------------------------------+
                                        | Waitlist entry W8X3KP2Q            |
                                        | Synthwave Night                    |
                                        | 2 seats wanted · Grace Hopper      |
                                        | Status: Promoted                   |
                                        | Booking reference: K7Q2M9XA        |
                                        +------------------------------------+
```

| State | When | Visible text (assertable) |
|-------|------|---------------------------|
| Join form | event `seats_available == 0` | "This event is sold out", heading "Join the waitlist", button "Join waitlist"; **no** "Reserve seats" button |
| No join form | event `seats_available > 0` | "Reserve seats" button; **no** "Join waitlist" text |
| Join error | service error on `POST /events/{id}/waitlist` | the message in `.alert.error` (e.g. "You are already on the waitlist for this event"), HTTP 409/422 |
| Waiting | entry status `waiting` | "Waitlist entry {code}", event name, "{n} seats wanted" (or "1 seat wanted"), "Status: Waiting", "Position in line: {p}", button "Leave waitlist" |
| Promoted | entry status `promoted` | "Status: Promoted", "Booking reference: {booking_code}" where `{booking_code}` is a link `<a href="/reservations/{booking_code}">`; **no** "Leave waitlist" button and **no** "Position in line" |
| Left | after leaving (or lookup of a left entry) | "Status: Left", "You have left the waitlist" (in `.alert.success`); **no** "Leave waitlist" button and **no** "Position in line" |
| Leave error | leave on a promoted/left entry | card + "Only waiting entries can be left" in `.alert.error`, HTTP 409 |
| Not found | unknown code | "Waitlist entry not found" — `GET` page: HTTP 404 full page; leave: HTTP 404 partial (no `<html>`) |

## AC mapping
| AC     | Satisfied by |
|--------|--------------|
| AC3.1  | `POST /api/events/{id}/waitlist` 201 (`status` "waiting", `position` = count of waiting entries, 8-char code); form → 303 to `/waitlist/{code}` "Waiting" state |
| AC3.2  | 409 "Seats are still available — reserve instead"; form error; join form hidden when seats are available |
| AC3.3  | 422 "You can wait for between 1 and 10 seats"; form error |
| AC3.4  | 422 "Name is required" / "A valid email is required"; form error |
| AC3.5  | 409 "You are already on the waitlist for this event" (waiting entries only, case-insensitive email); form error |
| AC3.6  | `GET /api/waitlist/{code}` 200 waiting body; `/waitlist/{code}` "Waiting" state |
| AC3.7  | `GET /api/waitlist/{code}` 200 promoted body with `booking_code`; `GET /api/reservations/{booking_code}` is `confirmed`; "Promoted" state |
| AC3.8  | 404 "Waitlist entry not found" on GET and leave (API and pages) |
| AC3.9  | `POST /api/reservations/{code}/cancel` → `waitlist.promote`; entry becomes promoted, reservation created, `GET /api/events/{id}` `seats_available` = freed − seats wanted |
| AC3.10 | `promote` skips non-fitting entries in join order; skipped entry keeps `position` |
| AC3.11 | `POST /api/waitlist/{code}/leave` 200 `status` "left"; later entries' `position` decreases by 1; HTMX leave → "Left" state |
| AC3.12 | 409 "This event has already started"; form error |

Business rules covered as well: unknown event → 404 "Event not found"; leaving a promoted entry →
409 "Only waiting entries can be left"; cancelling a promoted entry's reservation re-triggers promotion.

## Risks / notes
- **Leaving is a soft delete** (status `left`), not a row delete. The spec says a left entry is "no longer in
  the line" but does not say what a later lookup shows; keeping the row means lookup still works (shows
  "Status: Left"), references are never reused, leaving twice gives the spec's own message
  "Only waiting entries can be left", and the same email may join again (only `waiting` entries count for AC3.5).
- **Duplicate-email check is case-insensitive** (`Ada@Example.com` == `ada@example.com`). The spec does not
  say; this is the stricter, less surprising choice.
- **Error order when an event is both started and has seats:** "This event has already started" wins (checked
  first), since "reserve instead" would be misleading for a started event.
- **Join order = ascending `id`**, not `created_at` (timestamps can tie within a test). `created_at` is stored
  for information only.
- **Atomicity:** cancellation and promotion share one commit in `cancel`. SQLite serialises writes; good
  enough for a demo (same caveat as 002).
- **Testing started events:** `POST /api/events` rejects past start times, so tests for AC3.12 must insert an
  `Event` with a past `starts_at` through the `session` fixture (and fill it with `Reservation` rows, or use
  `POST /api/events/{id}/reservations`, which does not check start time).
- `waitlist.promote` reuses `reservations._new_code`, so booking references keep 002's format and uniqueness.
  Waitlist codes are unique within `WaitlistEntry` only; the two code spaces are looked up through separate
  URLs, so a collision across tables is harmless.
- Existing 002 behaviour (cancel response, "This event is sold out" text, no "Reserve seats" when sold out) is
  preserved, so 002 tests must keep passing.
