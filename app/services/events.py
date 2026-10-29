from datetime import datetime

from sqlmodel import Session, select

from app.models import Event, EventCreate, EventRead
from app.services import reservations
from app.services.clock import utcnow
from app.services.errors import NotFound, ValidationFailed

MAX_CAPACITY = 10_000


def create_event(session: Session, data: EventCreate, now: datetime | None = None) -> Event:
    now = now or utcnow()
    name, venue = data.name.strip(), data.venue.strip()
    if not name:
        raise ValidationFailed("Name is required")
    if not venue:
        raise ValidationFailed("Venue is required")
    if not 1 <= data.capacity <= MAX_CAPACITY:
        raise ValidationFailed(f"Capacity must be between 1 and {MAX_CAPACITY}")
    if data.starts_at <= now:
        raise ValidationFailed("Event must start in the future")
    if data.price_cents < 0:
        raise ValidationFailed("Price cannot be negative")

    event = Event(**data.model_dump(exclude={"name", "venue"}), name=name, venue=venue)
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def list_upcoming(session: Session, now: datetime | None = None) -> list[Event]:
    now = now or utcnow()
    query = select(Event).where(Event.starts_at > now).order_by(Event.starts_at)
    return list(session.exec(query))


def get_event(session: Session, event_id: int) -> Event:
    event = session.get(Event, event_id)
    if event is None:
        raise NotFound("Event not found")
    return event


def seats_available(session: Session, event: Event) -> int:
    return event.capacity - reservations.held_seats(session, event.id)


def to_read(session: Session, event: Event) -> EventRead:
    return EventRead(**event.model_dump(), seats_available=seats_available(session, event))
