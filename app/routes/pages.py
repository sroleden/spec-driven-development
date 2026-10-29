from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import SessionDep
from app.models import EventCreate, ReservationCreate, WaitlistJoin
from app.services import events, reservations, waitlist
from app.services.errors import Conflict, NotFound, ServiceError, ValidationFailed

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")
templates.env.filters["money"] = lambda cents: "Free" if cents == 0 else f"€{cents / 100:,.2f}"
templates.env.filters["when"] = lambda dt: dt.strftime("%a %d %b %Y · %H:%M")


def not_found(request: Request, message: str) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "not_found.html", {"message": message}, status_code=404
    )


# --- 001 event catalog -------------------------------------------------------
@router.get("/", response_class=HTMLResponse)
def event_list(request: Request, session: SessionDep):
    items = [events.to_read(session, e) for e in events.list_upcoming(session)]
    return templates.TemplateResponse(request, "events/list.html", {"events": items})


@router.get("/events/new", response_class=HTMLResponse)
def new_event_form(request: Request):
    return templates.TemplateResponse(request, "events/new.html", {"form": {}, "error": None})


@router.post("/events/new", response_class=HTMLResponse)
def create_event(
    request: Request,
    session: SessionDep,
    name: Annotated[str, Form()] = "",
    venue: Annotated[str, Form()] = "",
    starts_at: Annotated[str, Form()] = "",
    capacity: Annotated[str, Form()] = "",
    price: Annotated[str, Form()] = "0",
):
    form = {
        "name": name,
        "venue": venue,
        "starts_at": starts_at,
        "capacity": capacity,
        "price": price,
    }
    try:
        try:
            data = EventCreate(
                name=name,
                venue=venue,
                starts_at=datetime.fromisoformat(starts_at),
                capacity=int(capacity),
                price_cents=int(Decimal(price or "0") * 100),
            )
        except (ValueError, InvalidOperation):
            raise ValidationFailed("Please fill in every field with a valid value") from None
        event = events.create_event(session, data)
    except ValidationFailed as exc:
        return templates.TemplateResponse(
            request, "events/new.html", {"form": form, "error": exc.detail}, status_code=422
        )
    return RedirectResponse(f"/events/{event.id}", status_code=303)


def render_event(request, session, event, form, error=None, status_code=200):
    return templates.TemplateResponse(
        request,
        "events/detail.html",
        {"event": events.to_read(session, event), "form": form, "error": error},
        status_code=status_code,
    )


@router.get("/events/{event_id}", response_class=HTMLResponse)
def event_detail(request: Request, event_id: int, session: SessionDep):
    try:
        event = events.get_event(session, event_id)
    except NotFound as exc:
        return not_found(request, exc.detail)
    return render_event(request, session, event, {"seats": 1})


# --- 002 seat reservation ----------------------------------------------------
@router.post("/events/{event_id}/reserve", response_class=HTMLResponse)
def reserve_seats(
    request: Request,
    event_id: int,
    session: SessionDep,
    name: Annotated[str, Form()] = "",
    email: Annotated[str, Form()] = "",
    seats: Annotated[str, Form()] = "",
):
    try:
        event = events.get_event(session, event_id)
    except NotFound as exc:
        return not_found(request, exc.detail)
    form = {"name": name, "email": email, "seats": seats}
    try:
        try:
            count = int(seats)
        except ValueError:
            count = 0  # service rejects it with the "between 1 and 10 seats" message
        reservation = reservations.reserve(
            session, event_id, ReservationCreate(name=name, email=email, seats=count)
        )
    except ServiceError as exc:
        code = 409 if isinstance(exc, Conflict) else 422
        return render_event(request, session, event, form, exc.detail, code)
    return RedirectResponse(f"/reservations/{reservation.code}", status_code=303)


def render_card(request, session, reservation, error=None, status_code=200):
    return templates.TemplateResponse(
        request,
        "partials/reservation_card.html",
        {"r": reservations.to_read(session, reservation), "error": error},
        status_code=status_code,
    )


@router.get("/reservations/{code}", response_class=HTMLResponse)
def reservation_detail(request: Request, code: str, session: SessionDep):
    try:
        reservation = reservations.get_by_code(session, code)
    except NotFound as exc:
        return not_found(request, exc.detail)
    return templates.TemplateResponse(
        request,
        "reservations/detail.html",
        {"r": reservations.to_read(session, reservation), "error": None},
    )


@router.post("/reservations/{code}/cancel", response_class=HTMLResponse)
def cancel_reservation(request: Request, code: str, session: SessionDep):
    try:
        reservation = reservations.cancel(session, code)
    except NotFound as exc:
        return templates.TemplateResponse(
            request,
            "partials/reservation_card.html",
            {"r": None, "error": exc.detail},
            status_code=404,
        )
    except Conflict as exc:
        reservation = reservations.get_by_code(session, code)
        return render_card(request, session, reservation, exc.detail, 409)
    return render_card(request, session, reservation)


# --- 003 waitlist ------------------------------------------------------------
@router.post("/events/{event_id}/waitlist", response_class=HTMLResponse)
def join_waitlist(
    request: Request,
    event_id: int,
    session: SessionDep,
    name: Annotated[str, Form()] = "",
    email: Annotated[str, Form()] = "",
    seats: Annotated[str, Form()] = "",
):
    try:
        event = events.get_event(session, event_id)
    except NotFound as exc:
        return not_found(request, exc.detail)
    form = {"name": name, "email": email, "seats": seats}
    try:
        try:
            count = int(seats)
        except ValueError:
            count = 0  # service rejects it with the "between 1 and 10 seats" message
        entry = waitlist.join(session, event_id, WaitlistJoin(name=name, email=email, seats=count))
    except ServiceError as exc:
        code = 409 if isinstance(exc, Conflict) else 422
        return render_event(request, session, event, form, exc.detail, code)
    return RedirectResponse(f"/waitlist/{entry.code}", status_code=303)


def render_waitlist_card(request, session, entry, error=None, status_code=200):
    return templates.TemplateResponse(
        request,
        "partials/waitlist_card.html",
        {"w": waitlist.to_read(session, entry), "error": error},
        status_code=status_code,
    )


@router.get("/waitlist/{code}", response_class=HTMLResponse)
def waitlist_detail(request: Request, code: str, session: SessionDep):
    try:
        entry = waitlist.get_by_code(session, code)
    except NotFound as exc:
        return not_found(request, exc.detail)
    return templates.TemplateResponse(
        request,
        "waitlist/detail.html",
        {"w": waitlist.to_read(session, entry), "error": None},
    )


@router.post("/waitlist/{code}/leave", response_class=HTMLResponse)
def leave_waitlist(request: Request, code: str, session: SessionDep):
    try:
        entry = waitlist.leave(session, code)
    except NotFound as exc:
        return templates.TemplateResponse(
            request,
            "partials/waitlist_card.html",
            {"w": None, "error": exc.detail},
            status_code=404,
        )
    except Conflict as exc:
        entry = waitlist.get_by_code(session, code)
        return render_waitlist_card(request, session, entry, exc.detail, 409)
    return render_waitlist_card(request, session, entry)
