"""Acceptance tests for spec 002 — Seat reservation. Written from spec.md + design.md."""

from datetime import timedelta

import pytest

from app.services.clock import utcnow


def make_event(client, capacity=100, name="Synthwave Night"):
    res = client.post(
        "/api/events",
        json={
            "name": name,
            "venue": "Hall A",
            "starts_at": (utcnow() + timedelta(days=7)).replace(microsecond=0).isoformat(),
            "capacity": capacity,
            "price_cents": 2500,
        },
    )
    assert res.status_code == 201
    return res.json()["id"]


def body(**overrides):
    return {"name": "Ada Lovelace", "email": "ada@example.com", "seats": 2} | overrides


def reserve(client, event_id, **overrides):
    return client.post(f"/api/events/{event_id}/reservations", json=body(**overrides))


def available(client, event_id):
    return client.get(f"/api/events/{event_id}").json()["seats_available"]


# --- API ---------------------------------------------------------------------
def test_AC2_1_reserve_confirms_and_drops_seats(client):
    """Given an event with at least N seats available When an attendee reserves N seats (1–10) with their
    name and email Then the reservation is confirmed with a booking reference and the event's seats
    available drop by N."""
    eid = make_event(client, capacity=100)
    res = reserve(client, eid)
    assert res.status_code == 201
    data = res.json()
    assert len(data["code"]) == 8
    assert data["code"].isalnum() and data["code"] == data["code"].upper()
    assert data == {
        "code": data["code"],
        "event_id": eid,
        "event_name": "Synthwave Night",
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "seats": 2,
        "status": "confirmed",
    }
    assert available(client, eid) == 98


def test_AC2_1_codes_are_unique(client):
    """Given an event with at least N seats available When an attendee reserves N seats (1–10) with their
    name and email Then the reservation is confirmed with a booking reference and the event's seats
    available drop by N."""
    eid = make_event(client)
    codes = {reserve(client, eid, seats=1).json()["code"] for _ in range(5)}
    assert len(codes) == 5
    assert available(client, eid) == 95


def test_AC2_1_can_reserve_exactly_ten_and_exactly_remaining(client):
    """Given an event with at least N seats available When an attendee reserves N seats (1–10) with their
    name and email Then the reservation is confirmed with a booking reference and the event's seats
    available drop by N."""
    eid = make_event(client, capacity=10)
    assert reserve(client, eid, seats=10).status_code == 201
    assert available(client, eid) == 0


def test_rule_reserve_unknown_event_404(client):
    """Business rule: reserving for a non-existent event returns 404 "Event not found"."""
    res = reserve(client, 9999)
    assert res.status_code == 404
    assert res.json() == {"detail": "Event not found"}


@pytest.mark.parametrize("seats", [0, -1, 11])
def test_AC2_2_seats_out_of_range_rejected(client, seats):
    """Given a request for fewer than 1 or more than 10 seats When the attendee reserves Then it is
    rejected with "You can reserve between 1 and 10 seats"."""
    eid = make_event(client, capacity=100)
    res = reserve(client, eid, seats=seats)
    assert res.status_code == 422
    assert res.json() == {"detail": "You can reserve between 1 and 10 seats"}
    assert available(client, eid) == 100


def test_AC2_3_not_enough_seats_left(client):
    """Given an event with fewer seats available than requested (but not zero) When the attendee reserves
    Then it is rejected with "Only X seats left" (X = seats available)."""
    eid = make_event(client, capacity=5)
    assert reserve(client, eid, seats=2).status_code == 201
    res = reserve(client, eid, seats=4)
    assert res.status_code == 409
    assert res.json() == {"detail": "Only 3 seats left"}
    assert available(client, eid) == 3


def test_AC2_4_sold_out_reserve_rejected(client):
    """Given an event with no seats available When an attendee views or reserves it Then it is shown as
    sold out and reserving is rejected with "This event is sold out"."""
    eid = make_event(client, capacity=3)
    assert reserve(client, eid, seats=3).status_code == 201
    assert available(client, eid) == 0
    res = reserve(client, eid, seats=1)
    assert res.status_code == 409
    assert res.json() == {"detail": "This event is sold out"}


def test_AC2_5_blank_name_rejected(client):
    """Given a blank name or an invalid email When the attendee reserves Then it is rejected with "Name is
    required" / "A valid email is required"."""
    eid = make_event(client)
    for name in ["", "   "]:
        res = reserve(client, eid, name=name)
        assert res.status_code == 422
        assert res.json() == {"detail": "Name is required"}


@pytest.mark.parametrize("email", ["", "ada", "ada@", "@example.com", "ada@example", "a b@x.com"])
def test_AC2_5_invalid_email_rejected(client, email):
    """Given a blank name or an invalid email When the attendee reserves Then it is rejected with "Name is
    required" / "A valid email is required"."""
    eid = make_event(client)
    res = reserve(client, eid, email=email)
    assert res.status_code == 422
    assert res.json() == {"detail": "A valid email is required"}
    assert available(client, eid) == 100


def test_AC2_6_lookup_by_code(client):
    """Given a reservation When the attendee looks it up by booking reference Then they see the event
    name, number of seats and status."""
    eid = make_event(client)
    created = reserve(client, eid, seats=3).json()
    res = client.get(f"/api/reservations/{created['code']}")
    assert res.status_code == 200
    assert res.json() == created
    assert res.json()["event_name"] == "Synthwave Night"
    assert res.json()["seats"] == 3
    assert res.json()["status"] == "confirmed"


def test_AC2_6_lookup_is_case_insensitive(client):
    """Given a reservation When the attendee looks it up by booking reference Then they see the event
    name, number of seats and status."""
    eid = make_event(client)
    created = reserve(client, eid).json()
    res = client.get(f"/api/reservations/{created['code'].lower()}")
    assert res.status_code == 200
    assert res.json()["code"] == created["code"]


def test_AC2_7_lookup_unknown_code_404(client):
    """Given a booking reference that does not exist When the attendee looks it up or cancels it Then they
    get "Reservation not found"."""
    res = client.get("/api/reservations/ZZZZZZZZ")
    assert res.status_code == 404
    assert res.json() == {"detail": "Reservation not found"}


def test_AC2_7_cancel_unknown_code_404(client):
    """Given a booking reference that does not exist When the attendee looks it up or cancels it Then they
    get "Reservation not found"."""
    res = client.post("/api/reservations/ZZZZZZZZ/cancel")
    assert res.status_code == 404
    assert res.json() == {"detail": "Reservation not found"}


def test_AC2_8_cancel_restores_seats(client):
    """Given a confirmed reservation When the attendee cancels it Then its status becomes cancelled and its
    seats become available again."""
    eid = make_event(client, capacity=10)
    created = reserve(client, eid, seats=4).json()
    assert available(client, eid) == 6
    res = client.post(f"/api/reservations/{created['code']}/cancel")
    assert res.status_code == 200
    assert res.json() == created | {"status": "cancelled"}
    assert available(client, eid) == 10
    assert client.get(f"/api/reservations/{created['code']}").json()["status"] == "cancelled"


def test_AC2_8_cancel_sold_out_event_reopens_it(client):
    """Given a confirmed reservation When the attendee cancels it Then its status becomes cancelled and its
    seats become available again."""
    eid = make_event(client, capacity=2)
    created = reserve(client, eid, seats=2).json()
    client.post(f"/api/reservations/{created['code']}/cancel")
    assert reserve(client, eid, seats=2).status_code == 201


def test_AC2_9_double_cancel_rejected(client):
    """Given an already cancelled reservation When the attendee cancels it again Then it is rejected with
    "Reservation is already cancelled"."""
    eid = make_event(client, capacity=10)
    code = reserve(client, eid, seats=4).json()["code"]
    assert client.post(f"/api/reservations/{code}/cancel").status_code == 200
    res = client.post(f"/api/reservations/{code}/cancel")
    assert res.status_code == 409
    assert res.json() == {"detail": "Reservation is already cancelled"}
    assert available(client, eid) == 10


# --- Pages -------------------------------------------------------------------
def test_AC2_1_page_form_shown_and_reserve_redirects(client):
    """Given an event with at least N seats available When an attendee reserves N seats (1–10) with their
    name and email Then the reservation is confirmed with a booking reference and the event's seats
    available drop by N."""
    eid = make_event(client, capacity=100)
    page = client.get(f"/events/{eid}")
    assert page.status_code == 200
    assert "Reserve seats" in page.text
    res = client.post(
        f"/events/{eid}/reserve",
        data={"name": "Ada Lovelace", "email": "ada@example.com", "seats": "2"},
        follow_redirects=False,
    )
    assert res.status_code == 303
    location = res.headers["location"]
    assert location.startswith("/reservations/")
    code = location.rsplit("/", 1)[1]
    assert len(code) == 8
    assert available(client, eid) == 98
    conf = client.get(location)
    assert conf.status_code == 200
    assert f"Reservation {code}" in conf.text


def test_AC2_3_page_reserve_error_shown_in_alert(client):
    """Given an event with fewer seats available than requested (but not zero) When the attendee reserves
    Then it is rejected with "Only X seats left" (X = seats available)."""
    eid = make_event(client, capacity=5)
    reserve(client, eid, seats=2)
    res = client.post(
        f"/events/{eid}/reserve",
        data={"name": "Bob", "email": "bob@example.com", "seats": "4"},
        follow_redirects=False,
    )
    assert res.status_code == 409
    assert "alert" in res.text and "error" in res.text
    assert "Only 3 seats left" in res.text
    assert available(client, eid) == 3


def test_AC2_4_page_sold_out_state(client):
    """Given an event with no seats available When an attendee views or reserves it Then it is shown as
    sold out and reserving is rejected with "This event is sold out"."""
    eid = make_event(client, capacity=3)
    reserve(client, eid, seats=3)
    page = client.get(f"/events/{eid}")
    assert page.status_code == 200
    assert "This event is sold out" in page.text
    assert "Reserve seats" not in page.text


def test_AC2_4_page_reserve_when_sold_out_rejected(client):
    """Given an event with no seats available When an attendee views or reserves it Then it is shown as
    sold out and reserving is rejected with "This event is sold out"."""
    eid = make_event(client, capacity=3)
    reserve(client, eid, seats=3)
    res = client.post(
        f"/events/{eid}/reserve",
        data={"name": "Bob", "email": "bob@example.com", "seats": "1"},
        follow_redirects=False,
    )
    assert res.status_code == 409
    assert "This event is sold out" in res.text


def test_AC2_6_page_confirmation_shows_details(client):
    """Given a reservation When the attendee looks it up by booking reference Then they see the event
    name, number of seats and status."""
    eid = make_event(client)
    code = reserve(client, eid, seats=2).json()["code"]
    page = client.get(f"/reservations/{code}")
    assert page.status_code == 200
    for text in [
        f"Reservation {code}",
        "Synthwave Night",
        "2 seats",
        "Confirmed",
        "Cancel reservation",
    ]:
        assert text in page.text


def test_AC2_6_page_confirmation_singular_seat(client):
    """Given a reservation When the attendee looks it up by booking reference Then they see the event
    name, number of seats and status."""
    eid = make_event(client)
    code = reserve(client, eid, seats=1).json()["code"]
    page = client.get(f"/reservations/{code}")
    assert "1 seat" in page.text
    assert "1 seats" not in page.text


def test_AC2_7_page_unknown_code_404(client):
    """Given a booking reference that does not exist When the attendee looks it up or cancels it Then they
    get "Reservation not found"."""
    page = client.get("/reservations/ZZZZZZZZ")
    assert page.status_code == 404
    assert "Reservation not found" in page.text


def test_AC2_7_page_cancel_unknown_code(client):
    """Given a booking reference that does not exist When the attendee looks it up or cancels it Then they
    get "Reservation not found"."""
    res = client.post("/reservations/ZZZZZZZZ/cancel", headers={"HX-Request": "true"})
    assert res.status_code == 404
    assert "Reservation not found" in res.text
    assert "<html" not in res.text.lower()


def test_AC2_8_page_cancel_partial(client):
    """Given a confirmed reservation When the attendee cancels it Then its status becomes cancelled and its
    seats become available again."""
    eid = make_event(client, capacity=10)
    code = reserve(client, eid, seats=4).json()["code"]
    res = client.post(f"/reservations/{code}/cancel", headers={"HX-Request": "true"})
    assert res.status_code == 200
    assert "Reservation cancelled" in res.text
    assert "Cancel reservation" not in res.text
    assert available(client, eid) == 10
    page = client.get(f"/reservations/{code}")
    assert "Cancelled" in page.text
    assert "Cancel reservation" not in page.text


def test_AC2_9_page_double_cancel_shows_error_in_partial(client):
    """Given an already cancelled reservation When the attendee cancels it again Then it is rejected with
    "Reservation is already cancelled"."""
    eid = make_event(client)
    code = reserve(client, eid).json()["code"]
    client.post(f"/reservations/{code}/cancel", headers={"HX-Request": "true"})
    res = client.post(f"/reservations/{code}/cancel", headers={"HX-Request": "true"})
    assert res.status_code == 409
    assert "Reservation is already cancelled" in res.text
    assert "<html" not in res.text.lower()


def test_AC2_9_pages_declare_htmx_config_swapping_409(client):
    """Given an already cancelled reservation When the attendee cancels it again Then it is rejected with
    "Reservation is already cancelled" (the 409 partial must be swappable by htmx in the browser)."""
    import json
    import re

    page = client.get("/")
    assert page.status_code == 200
    tag = re.search(r"<meta\b[^>]*name=[\"']htmx-config[\"'][^>]*>", page.text)
    assert tag, "htmx-config meta missing"
    content = re.search(r"content=(?:\"([^\"]*)\"|'([^']*)')", tag.group(0))
    import html

    cfg = json.loads(html.unescape(content.group(1) or content.group(2)))
    rules = cfg["responseHandling"]
    assert any(re.search(r.get("code", ""), "409") and r.get("swap") is True for r in rules)
