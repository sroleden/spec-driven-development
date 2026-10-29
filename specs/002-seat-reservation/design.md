# Design 002 — Seat reservation

**Spec:** [spec.md](spec.md)

## Data model — `app/models.py`
```python
class ReservationStatus(StrEnum):
    confirmed = "confirmed"
    cancelled = "cancelled"

class Reservation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id", index=True)
    code: str = Field(index=True, unique=True)       # 8 chars, A–Z0–9
    name: str
    email: str
    seats: int
    status: ReservationStatus = ReservationStatus.confirmed
    created_at: NaiveDatetime = Field(default_factory=utcnow)   # app.services.clock.utcnow

class ReservationCreate(SQLModel):       # request body; rules enforced in the service
    name: str
    email: str
    seats: int

class ReservationRead(SQLModel):         # response body
    code: str
    event_id: int
    event_name: str
    name: str
    email: str
    seats: int
    status: ReservationStatus
```

## Service layer — `app/services/reservations.py`
| Function | Behaviour | Errors (checked in this order) |
|----------|-----------|--------------------------------|
| `reserve(session, event_id: int, data: ReservationCreate) -> Reservation` | Strips name/email, generates a unique code, saves as `confirmed`. | `NotFound("Event not found")` → `ValidationFailed("Name is required")` → `ValidationFailed("A valid email is required")` (regex `^[^@\s]+@[^@\s]+\.[^@\s]+$`) → `ValidationFailed("You can reserve between 1 and 10 seats")` → `Conflict("This event is sold out")` if 0 available → `Conflict("Only X seats left")` if fewer than requested |
| `get_by_code(session, code: str) -> Reservation` | Case-insensitive lookup (code upper-cased). | `NotFound("Reservation not found")` |
| `cancel(session, code: str) -> Reservation` | Sets status `cancelled`. | `NotFound("Reservation not found")`, `Conflict("Reservation is already cancelled")` |
| `held_seats(session, event_id: int) -> int` | Sum of `seats` over **confirmed** reservations for the event. | — |
| `to_read(session, r: Reservation) -> ReservationRead` | Adds `event_name`. | — |

**Change to `app/services/events.py`:** `seats_available(session, event)` returns
`event.capacity - reservations.held_seats(session, event.id)`.

## API contract — `app/routes/api.py`
### `POST /api/events/{event_id}/reservations`
Request:
```json
{"name": "Ada Lovelace", "email": "ada@example.com", "seats": 2}
```
`201` →
```json
{"code": "K7Q2M9XA", "event_id": 1, "event_name": "Synthwave Night", "name": "Ada Lovelace", "email": "ada@example.com", "seats": 2, "status": "confirmed"}
```
Errors: `404 {"detail": "Event not found"}`, `422 {"detail": "Name is required"}` /
`{"detail": "A valid email is required"}` / `{"detail": "You can reserve between 1 and 10 seats"}`,
`409 {"detail": "This event is sold out"}`, `409 {"detail": "Only 3 seats left"}`.

### `GET /api/reservations/{code}`
`200` → `ReservationRead`. Errors: `404 {"detail": "Reservation not found"}`.

### `POST /api/reservations/{code}/cancel`
`200` → `ReservationRead` with `"status": "cancelled"`.
Errors: `404 {"detail": "Reservation not found"}`, `409 {"detail": "Reservation is already cancelled"}`.

## UI — `app/routes/pages.py`, `app/templates/`
| Route | Template | Behaviour |
|-------|----------|-----------|
| `GET /events/{id}` | `events/detail.html` (fill the `event_actions` block) | Shows the reservation form, or the sold-out message |
| `POST /events/{id}/reserve` (form: `name`, `email`, `seats`) | success → `303` to `/reservations/{code}`; error → re-render `events/detail.html` with the message in `.alert.error`, status 422 or 409 (404 page if no event) | Reserve |
| `GET /reservations/{code}` | `reservations/detail.html` (404 `not_found.html` "Reservation not found") | Confirmation / lookup |
| `POST /reservations/{code}/cancel` (HTMX, `hx-target="#reservation"`, `hx-swap="outerHTML"`) | **always** returns partial `partials/reservation_card.html` (never a full page): `200` cancelled card · `409` card + "Reservation is already cancelled" · `404` card containing only "Reservation not found" | Cancel |

**HTMX error swapping (rev. 2):** htmx 2 does not swap 4xx responses by default. `base.html` declares
`<meta name="htmx-config">` whose `responseHandling` swaps `404`, `409` and `422` responses (as non-errors)
so error partials are visible in a real browser, while keeping honest HTTP status codes.

```
/events/1                                /reservations/K7Q2M9XA
+------------------------------------+  +------------------------------------+
| Synthwave Night                    |  | Reservation K7Q2M9XA               |
| Hall A · Tue 01 Dec 2026 · 20:00   |  | Synthwave Night                    |
| €25.00   [98 seats available]      |  | 2 seats · Ada Lovelace             |
| Name  [__________]                 |  | Status: Confirmed                  |
| Email [__________]                 |  | [Cancel reservation]               |
| Seats [2]   [Reserve seats]        |  +------------------------------------+
+------------------------------------+
```

| State | When | Visible text (assertable) |
|-------|------|---------------------------|
| Form | seats available > 0 | button "Reserve seats" |
| Sold out | seats available == 0 | "This event is sold out" and **no** "Reserve seats" button |
| Reserve error | service error | the message in `.alert.error` (e.g. "Only 3 seats left") |
| Confirmation | reservation exists | "Reservation {code}", event name, "{n} seats" (or "1 seat"), "Confirmed" or "Cancelled" |
| Cancelled | after cancel | "Reservation cancelled" and **no** "Cancel reservation" button |
| Not found | unknown code | "Reservation not found" (HTTP 404) |

## AC mapping
| AC    | Satisfied by |
|-------|--------------|
| AC2.1 | `POST /api/events/{id}/reservations` 201 + `GET /api/events/{id}` seats drop; form → 303 confirmation page |
| AC2.2 | 422 "You can reserve between 1 and 10 seats"; form error |
| AC2.3 | 409 "Only X seats left"; form error |
| AC2.4 | 409 "This event is sold out"; detail page sold-out state; list page "Sold out" badge (from 001) |
| AC2.5 | 422 "Name is required" / "A valid email is required"; form error |
| AC2.6 | `GET /api/reservations/{code}`; `/reservations/{code}` page |
| AC2.7 | 404 "Reservation not found" on GET and cancel (API and page) |
| AC2.8 | `POST /api/reservations/{code}/cancel` 200 + seats restored; HTMX cancel → "Reservation cancelled" |
| AC2.9 | 409 "Reservation is already cancelled" |

## Risks / notes
- Overbooking under concurrency: SQLite serialises writes, and the check + insert happen in one session
  commit. Good enough for a demo; a real system would lock the event row.
- **rev. 2 (from review.md finding 1):** pinned status codes for the HTMX cancel partial and added the
  `htmx-config` meta so 4xx partials swap. Affected lanes: ui (TU5), test (TT4).
- `ReservationStatus` uses `StrEnum` rather than `(str, Enum)` — ruff UP042; raised by backend-coder
  and ui-coder during build, contract updated.
- `seats_available` changes in `events.py` (backend lane) — the UI keeps calling `events.to_read`, unchanged.
