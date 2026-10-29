from fastapi import APIRouter

from app.db import SessionDep
from app.models import (
    EventCreate,
    EventRead,
    ReservationCreate,
    ReservationRead,
    WaitlistEntryRead,
    WaitlistJoin,
)
from app.services import events, reservations, waitlist

router = APIRouter(prefix="/api", tags=["api"])


# --- 001 event catalog -------------------------------------------------------
@router.post("/events", status_code=201, response_model=EventRead)
def create_event(data: EventCreate, session: SessionDep):
    return events.to_read(session, events.create_event(session, data))


@router.get("/events", response_model=list[EventRead])
def list_events(session: SessionDep):
    return [events.to_read(session, e) for e in events.list_upcoming(session)]


@router.get("/events/{event_id}", response_model=EventRead)
def get_event(event_id: int, session: SessionDep):
    return events.to_read(session, events.get_event(session, event_id))


# --- 002 seat reservation ----------------------------------------------------
@router.post("/events/{event_id}/reservations", status_code=201, response_model=ReservationRead)
def reserve(event_id: int, data: ReservationCreate, session: SessionDep):
    return reservations.to_read(session, reservations.reserve(session, event_id, data))


@router.get("/reservations/{code}", response_model=ReservationRead)
def get_reservation(code: str, session: SessionDep):
    return reservations.to_read(session, reservations.get_by_code(session, code))


@router.post("/reservations/{code}/cancel", response_model=ReservationRead)
def cancel_reservation(code: str, session: SessionDep):
    return reservations.to_read(session, reservations.cancel(session, code))


# --- 003 waitlist ------------------------------------------------------------
@router.post("/events/{event_id}/waitlist", status_code=201, response_model=WaitlistEntryRead)
def join_waitlist(event_id: int, data: WaitlistJoin, session: SessionDep):
    return waitlist.to_read(session, waitlist.join(session, event_id, data))


@router.get("/waitlist/{code}", response_model=WaitlistEntryRead)
def get_waitlist_entry(code: str, session: SessionDep):
    return waitlist.to_read(session, waitlist.get_by_code(session, code))


@router.post("/waitlist/{code}/leave", response_model=WaitlistEntryRead)
def leave_waitlist(code: str, session: SessionDep):
    return waitlist.to_read(session, waitlist.leave(session, code))
