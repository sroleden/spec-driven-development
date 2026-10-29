"""Acceptance tests for spec 001 — Event catalog. Written from spec.md + design.md."""

from datetime import timedelta

import pytest

from app.models import Event
from app.services.clock import utcnow


def future(days=7):
    return (utcnow() + timedelta(days=days)).replace(microsecond=0)


def payload(**overrides):
    body = {
        "name": "Synthwave Night",
        "venue": "Hall A",
        "starts_at": future().isoformat(),
        "capacity": 100,
        "price_cents": 2500,
    }
    return body | overrides


def add_event(session, days, name="E", capacity=10):
    event = Event(
        name=name,
        venue="V",
        starts_at=utcnow() + timedelta(days=days),
        capacity=capacity,
        price_cents=0,
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


# --- API ---------------------------------------------------------------------
def test_AC1_1_create_event_with_all_seats_available(client):
    """Given a name, venue, future start time, capacity of 1–10,000 and a price ≥ 0 When the organiser
    creates the event Then the event is saved and all of its seats are available."""
    res = client.post("/api/events", json=payload())
    assert res.status_code == 201
    body = res.json()
    assert body["id"] > 0
    assert body["seats_available"] == 100
    assert client.get(f"/api/events/{body['id']}").json()["name"] == "Synthwave Night"


@pytest.mark.parametrize("capacity", [0, -5, 10_001])
def test_AC1_2_capacity_out_of_range_rejected(client, capacity):
    """Given a capacity below 1 or above 10,000 When the organiser creates the event Then it is rejected
    with "Capacity must be between 1 and 10000"."""
    res = client.post("/api/events", json=payload(capacity=capacity))
    assert res.status_code == 422
    assert res.json() == {"detail": "Capacity must be between 1 and 10000"}


def test_AC1_2_capacity_boundaries_accepted(client):
    assert client.post("/api/events", json=payload(capacity=1)).status_code == 201
    assert client.post("/api/events", json=payload(capacity=10_000)).status_code == 201


def test_AC1_3_past_start_rejected(client):
    """Given a start time that is not in the future When the organiser creates the event Then it is
    rejected with "Event must start in the future"."""
    res = client.post("/api/events", json=payload(starts_at=future(days=-1).isoformat()))
    assert res.status_code == 422
    assert res.json() == {"detail": "Event must start in the future"}


@pytest.mark.parametrize(
    ("field", "message"), [("name", "Name is required"), ("venue", "Venue is required")]
)
def test_AC1_4_blank_name_or_venue_rejected(client, field, message):
    """Given a blank name or blank venue When the organiser creates the event Then it is rejected with
    "Name is required" / "Venue is required"."""
    res = client.post("/api/events", json=payload(**{field: "   "}))
    assert res.status_code == 422
    assert res.json() == {"detail": message}


def test_AC1_5_negative_price_rejected(client):
    """Given a negative price When the organiser creates the event Then it is rejected with "Price
    cannot be negative"."""
    res = client.post("/api/events", json=payload(price_cents=-1))
    assert res.status_code == 422
    assert res.json() == {"detail": "Price cannot be negative"}


def test_AC1_5_free_event_allowed(client):
    assert client.post("/api/events", json=payload(price_cents=0)).status_code == 201


def test_AC1_6_only_upcoming_events_soonest_first(client, session):
    """Given past and upcoming events When an attendee browses events Then only upcoming events are
    shown, soonest first."""
    add_event(session, days=-2, name="Past")
    add_event(session, days=10, name="Later")
    add_event(session, days=3, name="Sooner")
    names = [e["name"] for e in client.get("/api/events").json()]
    assert names == ["Sooner", "Later"]


def test_AC1_7_no_upcoming_events_api_empty(client, session):
    """Given no upcoming events When an attendee browses events Then they see "No upcoming events
    yet"."""
    add_event(session, days=-1)
    assert client.get("/api/events").json() == []


def test_AC1_8_event_details(client):
    """Given an existing event When an attendee opens it Then they see its name, venue, start time,
    price and seats available."""
    created = client.post("/api/events", json=payload()).json()
    body = client.get(f"/api/events/{created['id']}").json()
    assert body == created
    assert {"name", "venue", "starts_at", "price_cents", "seats_available"} <= body.keys()


def test_AC1_9_unknown_event_not_found(client):
    """Given an event that does not exist When an attendee opens it Then they get "Event not
    found"."""
    res = client.get("/api/events/999")
    assert res.status_code == 404
    assert res.json() == {"detail": "Event not found"}


# --- Pages -------------------------------------------------------------------
def test_AC1_1_create_form_redirects_to_event_page(client):
    form = {
        "name": "Jazz Brunch",
        "venue": "Café Blue",
        "starts_at": future().strftime("%Y-%m-%dT%H:%M"),
        "capacity": "40",
        "price": "12.50",
    }
    res = client.post("/events/new", data=form, follow_redirects=False)
    assert res.status_code == 303
    page = client.get(res.headers["location"])
    assert "Jazz Brunch" in page.text
    assert "€12.50" in page.text
    assert "40 seats available" in page.text


def test_AC1_4_form_shows_validation_error(client):
    form = {
        "name": "",
        "venue": "Café Blue",
        "starts_at": future().strftime("%Y-%m-%dT%H:%M"),
        "capacity": "40",
        "price": "0",
    }
    res = client.post("/events/new", data=form)
    assert res.status_code == 422
    assert "Name is required" in res.text


def test_AC1_6_list_page_shows_cards(client, session):
    add_event(session, days=2, name="Synthwave Night", capacity=100)
    page = client.get("/")
    assert "Synthwave Night" in page.text
    assert "100 seats left" in page.text


def test_AC1_7_list_page_empty_state(client):
    assert "No upcoming events yet" in client.get("/").text


def test_AC1_9_unknown_event_page_404(client):
    res = client.get("/events/999")
    assert res.status_code == 404
    assert "Event not found" in res.text
