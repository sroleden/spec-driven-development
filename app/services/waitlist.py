import secrets
from datetime import datetime

from sqlmodel import Session, func, select

from app.models import (
    Event,
    Reservation,
    WaitlistEntry,
    WaitlistEntryRead,
    WaitlistJoin,
    WaitlistStatus,
)
from app.services import events, reservations
from app.services.clock import utcnow
from app.services.errors import Conflict, NotFound, ValidationFailed
from app.services.reservations import CODE_ALPHABET, EMAIL_RE, MAX_SEATS, MIN_SEATS


def _new_code(session: Session) -> str:
    while True:
        code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))
        if session.exec(select(WaitlistEntry).where(WaitlistEntry.code == code)).first() is None:
            return code


def join(
    session: Session, event_id: int, data: WaitlistJoin, now: datetime | None = None
) -> WaitlistEntry:
    now = now or utcnow()
    event = session.get(Event, event_id)
    if event is None:
        raise NotFound("Event not found")
    name, email = data.name.strip(), data.email.strip()
    if not name:
        raise ValidationFailed("Name is required")
    if not EMAIL_RE.match(email):
        raise ValidationFailed("A valid email is required")
    if not MIN_SEATS <= data.seats <= MAX_SEATS:
        raise ValidationFailed("You can wait for between 1 and 10 seats")
    if event.starts_at <= now:
        raise Conflict("This event has already started")
    if events.seats_available(session, event) > 0:
        raise Conflict("Seats are still available — reserve instead")
    duplicate = session.exec(
        select(WaitlistEntry).where(
            WaitlistEntry.event_id == event_id,
            WaitlistEntry.status == WaitlistStatus.waiting,
            func.lower(WaitlistEntry.email) == email.lower(),
        )
    ).first()
    if duplicate is not None:
        raise Conflict("You are already on the waitlist for this event")

    entry = WaitlistEntry(
        event_id=event_id, code=_new_code(session), name=name, email=email, seats=data.seats
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def get_by_code(session: Session, code: str) -> WaitlistEntry:
    entry = session.exec(select(WaitlistEntry).where(WaitlistEntry.code == code.upper())).first()
    if entry is None:
        raise NotFound("Waitlist entry not found")
    return entry


def leave(session: Session, code: str) -> WaitlistEntry:
    entry = get_by_code(session, code)
    if entry.status != WaitlistStatus.waiting:
        raise Conflict("Only waiting entries can be left")
    entry.status = WaitlistStatus.left
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def position(session: Session, entry: WaitlistEntry) -> int | None:
    if entry.status != WaitlistStatus.waiting:
        return None
    ahead = session.exec(
        select(func.count()).where(
            WaitlistEntry.event_id == entry.event_id,
            WaitlistEntry.status == WaitlistStatus.waiting,
            WaitlistEntry.id < entry.id,
        )
    ).one()
    return 1 + int(ahead)


def promote(session: Session, event_id: int) -> list[WaitlistEntry]:
    """Promote waiting entries into reservations in join order. Does not commit."""
    event = session.get(Event, event_id)
    available = events.seats_available(session, event)
    promoted: list[WaitlistEntry] = []
    waiting = session.exec(
        select(WaitlistEntry)
        .where(WaitlistEntry.event_id == event_id, WaitlistEntry.status == WaitlistStatus.waiting)
        .order_by(WaitlistEntry.id)
    ).all()
    for entry in waiting:
        if available <= 0:
            break
        if entry.seats > available:
            continue
        r = Reservation(
            event_id=event_id,
            code=reservations._new_code(session),
            name=entry.name,
            email=entry.email,
            seats=entry.seats,
        )
        session.add(r)
        session.flush()
        entry.status = WaitlistStatus.promoted
        entry.reservation_id = r.id
        session.add(entry)
        available -= entry.seats
        promoted.append(entry)
    return promoted


def to_read(session: Session, entry: WaitlistEntry) -> WaitlistEntryRead:
    event = session.get(Event, entry.event_id)
    booking_code = None
    if entry.reservation_id is not None:
        r = session.get(Reservation, entry.reservation_id)
        booking_code = r.code if r else None
    return WaitlistEntryRead(
        **entry.model_dump(exclude={"id", "reservation_id", "created_at"}),
        event_name=event.name if event else "",
        position=position(session, entry),
        booking_code=booking_code,
    )
