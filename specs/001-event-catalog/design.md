# Design 001 — Event catalog

**Spec:** [spec.md](spec.md)

## Data model — `app/models.py`
```python
class EventBase(SQLModel):
    name: str
    venue: str
    starts_at: datetime  # naive UTC
    capacity: int
    price_cents: int


class Event(EventBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class EventCreate(EventBase):  # request body; rules are enforced in the service, not by pydantic
    pass


class EventRead(EventBase):  # response body
    id: int
    seats_available: int
```

## Service layer — `app/services/events.py`
| Function | Behaviour | Errors |
|----------|-----------|--------|
| `create_event(session, data: EventCreate, now: datetime \| None = None) -> Event` | Strips name/venue, validates in the order name → venue → capacity → start → price, saves. | `ValidationFailed("Name is required")`, `("Venue is required")`, `("Capacity must be between 1 and 10000")`, `("Event must start in the future")`, `("Price cannot be negative")` |
| `list_upcoming(session, now: datetime \| None = None) -> list[Event]` | Events with `starts_at > now`, ordered by `starts_at` ascending. | — |
| `get_event(session, event_id: int) -> Event` | Fetch by id. | `NotFound("Event not found")` |
| `seats_available(session, event: Event) -> int` | In 001: `event.capacity`. Later features subtract held seats. | — |
| `to_read(session, event: Event) -> EventRead` | Builds the response model including `seats_available`. | — |

`now` defaults to `datetime.utcnow()` equivalent (`datetime.now(UTC).replace(tzinfo=None)`).

## API contract — `app/routes/api.py`
### `POST /api/events`
Request:
```json
{"name": "Synthwave Night", "venue": "Hall A", "starts_at": "2026-12-01T20:00:00", "capacity": 100, "price_cents": 2500}
```
`201` →
```json
{"id": 1, "name": "Synthwave Night", "venue": "Hall A", "starts_at": "2026-12-01T20:00:00", "capacity": 100, "price_cents": 2500, "seats_available": 100}
```
Errors: `422 {"detail": "Capacity must be between 1 and 10000"}` (and the other messages above, verbatim).

### `GET /api/events`
`200` → `[EventRead, ...]` upcoming only, soonest first; `[]` when none.

### `GET /api/events/{event_id}`
`200` → `EventRead`. Errors: `404 {"detail": "Event not found"}`.

## UI — `app/routes/pages.py`, `app/templates/`
| Route | Template | Purpose |
|-------|----------|---------|
| `GET /` | `events/list.html` | Upcoming events as cards |
| `GET /events/new` | `events/new.html` | Create form |
| `POST /events/new` (form) | `events/new.html` on error, else `303` → `/events/{id}` | Create |
| `GET /events/{id}` | `events/detail.html` (`404` + `not_found.html` if missing) | Details |

```
/                                   /events/{id}
+--------------------------------+  +--------------------------------+
| Upcoming events  [+ New event] |  | Synthwave Night                |
| +-----------+ +-----------+    |  | Hall A · 1 Dec 2026 20:00      |
| | Synthwave | | Jazz Brunch|   |  | €25.00                         |
| | Hall A    | | Café Blue  |   |  | [100 seats available]          |
| | 100 left  | | SOLD OUT   |   |  +--------------------------------+
| +-----------+ +-----------+    |
+--------------------------------+
```
Form fields (`name`, `venue`, `starts_at` as `datetime-local`, `capacity`, `price` in euros → converted to
cents by the page route).

| State | When | Visible text (assertable) |
|-------|------|---------------------------|
| Empty list | no upcoming events | "No upcoming events yet" |
| Card | per event | name, venue, "`N` seats left" |
| Detail | event exists | name, venue, start, price formatted "€25.00", "`N` seats available" |
| Form error | service raised `ValidationFailed` | the error message in `.alert.error` |
| Not found | unknown id | "Event not found" (HTTP 404) |

## AC mapping
| AC    | Satisfied by |
|-------|--------------|
| AC1.1 | `POST /api/events` 201, `seats_available == capacity`; form → redirect |
| AC1.2 | 422 "Capacity must be between 1 and 10000"; form error |
| AC1.3 | 422 "Event must start in the future"; form error |
| AC1.4 | 422 "Name is required" / "Venue is required"; form error |
| AC1.5 | 422 "Price cannot be negative"; form error |
| AC1.6 | `GET /api/events` ordering/filter; `/` list |
| AC1.7 | `GET /api/events` → `[]`; `/` "No upcoming events yet" |
| AC1.8 | `GET /api/events/{id}`; `/events/{id}` detail |
| AC1.9 | 404 "Event not found" (API and page) |

## Risks / notes
- SQLModel rejects plain naive `datetime` fields; use pydantic `NaiveDatetime` (found during build).
- `seats_available` is a function, not a column, so feature 002 can change it without a migration.
