import re
import secrets
import string

from sqlmodel import Session, func, select

from app.models import Event, Reservation, ReservationCreate, ReservationRead, ReservationStatus
from app.services.errors import Conflict, NotFound, ValidationFailed

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CODE_ALPHABET = string.ascii_uppercase + string.digits
MIN_SEATS, MAX_SEATS = 1, 10


def _new_code(session: Session) -> str:
    while True:
        code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))
        if session.exec(select(Reservation).where(Reservation.code == code)).first() is None:
            return code


def reserve(session: Session, event_id: int, data: ReservationCreate) -> Reservation:
    from app.services import events  # local import: events imports this module

    event = session.get(Event, event_id)
    if event is None:
        raise NotFound("Event not found")
    name, email = data.name.strip(), data.email.strip()
    if not name:
        raise ValidationFailed("Name is required")
    if not EMAIL_RE.match(email):
        raise ValidationFailed("A valid email is required")
    if not MIN_SEATS <= data.seats <= MAX_SEATS:
        raise ValidationFailed("You can reserve between 1 and 10 seats")
    available = events.seats_available(session, event)
    if available <= 0:
        raise Conflict("This event is sold out")
    if data.seats > available:
        raise Conflict(f"Only {available} seats left")

    reservation = Reservation(
        event_id=event_id, code=_new_code(session), name=name, email=email, seats=data.seats
    )
    session.add(reservation)
    session.commit()
    session.refresh(reservation)
    return reservation


def get_by_code(session: Session, code: str) -> Reservation:
    reservation = session.exec(select(Reservation).where(Reservation.code == code.upper())).first()
    if reservation is None:
        raise NotFound("Reservation not found")
    return reservation


def cancel(session: Session, code: str) -> Reservation:
    from app.services import waitlist  # local import: waitlist imports this module

    reservation = get_by_code(session, code)
    if reservation.status == ReservationStatus.cancelled:
        raise Conflict("Reservation is already cancelled")
    reservation.status = ReservationStatus.cancelled
    session.add(reservation)
    waitlist.promote(session, reservation.event_id)  # same transaction
    session.commit()
    session.refresh(reservation)
    return reservation


def held_seats(session: Session, event_id: int) -> int:
    query = select(func.coalesce(func.sum(Reservation.seats), 0)).where(
        Reservation.event_id == event_id, Reservation.status == ReservationStatus.confirmed
    )
    return int(session.exec(query).one())


def to_read(session: Session, r: Reservation) -> ReservationRead:
    event = session.get(Event, r.event_id)
    return ReservationRead(**r.model_dump(), event_name=event.name if event else "")
