"""SQLModel tables. Each feature's design.md defines what lives here."""

from enum import StrEnum

from pydantic import NaiveDatetime
from sqlmodel import Field, SQLModel

from app.services.clock import utcnow


# --- 001 event catalog -------------------------------------------------------
class EventBase(SQLModel):
    name: str
    venue: str
    starts_at: NaiveDatetime  # UTC
    capacity: int
    price_cents: int


class Event(EventBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class EventCreate(EventBase):
    pass


class EventRead(EventBase):
    id: int
    seats_available: int


# --- 002 seat reservation ----------------------------------------------------
class ReservationStatus(StrEnum):
    confirmed = "confirmed"
    cancelled = "cancelled"


class Reservation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id", index=True)
    code: str = Field(index=True, unique=True)  # 8 chars, A-Z0-9
    name: str
    email: str
    seats: int
    status: ReservationStatus = ReservationStatus.confirmed
    created_at: NaiveDatetime = Field(default_factory=utcnow)


class ReservationCreate(SQLModel):  # request body; rules enforced in the service
    name: str
    email: str
    seats: int


class ReservationRead(SQLModel):  # response body
    code: str
    event_id: int
    event_name: str
    name: str
    email: str
    seats: int
    status: ReservationStatus


# --- 003 waitlist ------------------------------------------------------------
class WaitlistStatus(StrEnum):
    waiting = "waiting"
    promoted = "promoted"
    left = "left"  # soft-deleted: no longer in the line


class WaitlistEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)  # ascending id == join order
    event_id: int = Field(foreign_key="event.id", index=True)
    code: str = Field(index=True, unique=True)  # waitlist reference, 8 chars, A-Z0-9
    name: str
    email: str
    seats: int  # seats wanted, 1-10
    status: WaitlistStatus = WaitlistStatus.waiting
    reservation_id: int | None = Field(default=None, foreign_key="reservation.id")
    created_at: NaiveDatetime = Field(default_factory=utcnow)


class WaitlistJoin(SQLModel):  # request body; rules enforced in the service
    name: str
    email: str
    seats: int


class WaitlistEntryRead(SQLModel):  # response body
    code: str
    event_id: int
    event_name: str
    name: str
    email: str
    seats: int
    status: WaitlistStatus
    position: int | None  # 1 = next in line; null unless status == "waiting"
    booking_code: str | None  # Reservation.code; null unless status == "promoted"
