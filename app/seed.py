"""Reset the local database and load demo data: `uv run python -m app.seed`."""

from datetime import timedelta

from sqlmodel import Session, SQLModel

from app.db import engine, init_db
from app.models import EventCreate, ReservationCreate
from app.services import events, reservations
from app.services.clock import utcnow

EVENTS = [
    # name, venue, days from now, hour, capacity, price_cents
    ("Neon Dreams: Synthwave Live", "The Foundry", 5, 21, 4, 3500),
    ("Jazz Brunch Quartet", "Café Blue", 9, 11, 40, 1800),
    ("Spec-Driven Dev Meetup", "Tech Hub · Room 2", 14, 18, 60, 0),
    ("Midnight Planetarium", "City Observatory", 21, 23, 25, 1200),
]

# Fixed booking codes so the demo script can cancel them by name.
SOLD_OUT_BOOKINGS = [
    ("ADALOVE1", "Ada Lovelace", "ada@example.com", 2),
    ("TURING42", "Alan Turing", "alan@example.com", 2),
]


def seed() -> None:
    SQLModel.metadata.drop_all(engine)
    init_db()
    now = utcnow().replace(minute=0, second=0, microsecond=0)
    with Session(engine) as session:
        created = [
            events.create_event(
                session,
                EventCreate(
                    name=name,
                    venue=venue,
                    starts_at=(now + timedelta(days=days)).replace(hour=hour),
                    capacity=capacity,
                    price_cents=price,
                ),
            )
            for name, venue, days, hour, capacity, price in EVENTS
        ]
        sold_out = created[0]
        for code, name, email, seats in SOLD_OUT_BOOKINGS:
            r = reservations.reserve(
                session, sold_out.id, ReservationCreate(name=name, email=email, seats=seats)
            )
            r.code = code
            session.add(r)
            session.commit()
            print(f"  reservation {r.code}  {name:<14} {seats} seats  → {sold_out.name}")
        reservations.reserve(
            session,
            created[1].id,
            ReservationCreate(name="Grace Hopper", email="grace@example.com", seats=3),
        )
        print(f"Seeded {len(created)} events; '{sold_out.name}' is sold out.")


if __name__ == "__main__":
    seed()
