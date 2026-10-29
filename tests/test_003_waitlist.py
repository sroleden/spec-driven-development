"""Acceptance tests for spec 003 — Waitlist. Written from spec.md + design.md."""

from datetime import timedelta

import pytest

from app.models import Event, Reservation
from app.services.clock import utcnow

SOLD_OUT_MSG = "Seats are still available — reserve instead"


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


def reserve(client, event_id, seats=1, email="holder@example.com", name="Holder"):
    res = client.post(
        f"/api/events/{event_id}/reservations",
        json={"name": name, "email": email, "seats": seats},
    )
    assert res.status_code == 201
    return res.json()["code"]


def sold_out_event(client, capacity=4, name="Synthwave Night"):
    """Create an event and fill it with a single reservation. Returns (event_id, booking_code)."""
    eid = make_event(client, capacity=capacity, name=name)
    return eid, reserve(client, eid, seats=capacity)


def join_body(**overrides):
    return {"name": "Grace Hopper", "email": "grace@example.com", "seats": 2} | overrides


def join(client, event_id, **overrides):
    return client.post(f"/api/events/{event_id}/waitlist", json=join_body(**overrides))


def join_ok(client, event_id, **overrides):
    res = join(client, event_id, **overrides)
    assert res.status_code == 201, res.text
    return res.json()


def lookup(client, code):
    return client.get(f"/api/waitlist/{code}")


def available(client, event_id):
    return client.get(f"/api/events/{event_id}").json()["seats_available"]


def cancel(client, booking_code):
    res = client.post(f"/api/reservations/{booking_code}/cancel")
    assert res.status_code == 200, res.text
    return res


def started_sold_out_event(session, capacity=3):
    """Insert an already-started, sold-out event directly (the API rejects past start times)."""
    event = Event(
        name="Past Gig",
        venue="Hall B",
        starts_at=utcnow() - timedelta(hours=1),
        capacity=capacity,
        price_cents=1000,
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    session.add(
        Reservation(
            event_id=event.id, code="FULLFULL", name="Z", email="z@example.com", seats=capacity
        )
    )
    session.commit()
    return event.id


def started_open_event(session):
    event = Event(
        name="Past Gig",
        venue="Hall B",
        starts_at=utcnow() - timedelta(hours=1),
        capacity=50,
        price_cents=1000,
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event.id


# --- AC3.1 -------------------------------------------------------------------
def test_AC3_1_join_creates_waiting_entry_last_in_line(client):
    """Given a sold-out event When an attendee joins the waitlist with their name, email and N seats
    (1–10) Then a waitlist entry is created with a waitlist reference, status "Waiting" and their
    position in line (last)."""
    eid, _ = sold_out_event(client)
    res = join(client, eid)
    assert res.status_code == 201
    data = res.json()
    assert len(data["code"]) == 8
    assert data["code"].isalnum() and data["code"] == data["code"].upper()
    assert data == {
        "code": data["code"],
        "event_id": eid,
        "event_name": "Synthwave Night",
        "name": "Grace Hopper",
        "email": "grace@example.com",
        "seats": 2,
        "status": "waiting",
        "position": 1,
        "booking_code": None,
    }


def test_AC3_1_second_and_third_joiners_get_next_positions(client):
    """Given a sold-out event When an attendee joins the waitlist with their name, email and N seats
    (1–10) Then a waitlist entry is created with a waitlist reference, status "Waiting" and their
    position in line (last)."""
    eid, _ = sold_out_event(client)
    positions = [
        join_ok(client, eid, email=f"p{i}@example.com", seats=1)["position"] for i in range(3)
    ]
    assert positions == [1, 2, 3]


def test_AC3_1_codes_are_unique(client):
    """Given a sold-out event When an attendee joins the waitlist with their name, email and N seats
    (1–10) Then a waitlist entry is created with a waitlist reference, status "Waiting" and their
    position in line (last)."""
    eid, _ = sold_out_event(client)
    codes = {join_ok(client, eid, email=f"u{i}@example.com")["code"] for i in range(5)}
    assert len(codes) == 5


@pytest.mark.parametrize("seats", [1, 10])
def test_AC3_1_boundary_seat_counts_accepted(client, seats):
    """Given a sold-out event When an attendee joins the waitlist with their name, email and N seats
    (1–10) Then a waitlist entry is created with a waitlist reference, status "Waiting" and their
    position in line (last)."""
    eid, _ = sold_out_event(client)
    assert join_ok(client, eid, seats=seats)["seats"] == seats


def test_rule_join_unknown_event_404(client):
    """Business rule: joining the waitlist of an unknown event fails with "Event not found"."""
    res = join(client, 9999)
    assert res.status_code == 404
    assert res.json() == {"detail": "Event not found"}


def test_rule_email_with_confirmed_reservation_may_join(client):
    """Decision: an email that already holds a confirmed reservation may still join the waitlist."""
    eid = make_event(client, capacity=2)
    reserve(client, eid, seats=2, email="grace@example.com")
    assert join(client, eid, email="grace@example.com").status_code == 201


# --- AC3.2 -------------------------------------------------------------------
def test_AC3_2_join_rejected_while_seats_available(client):
    """Given an event that still has seats available When an attendee tries to join the waitlist Then
    it is rejected with "Seats are still available — reserve instead"."""
    eid = make_event(client, capacity=10)
    res = join(client, eid)
    assert res.status_code == 409
    assert res.json() == {"detail": SOLD_OUT_MSG}


def test_AC3_2_rejected_when_one_seat_left(client):
    """Given an event that still has seats available When an attendee tries to join the waitlist Then
    it is rejected with "Seats are still available — reserve instead"."""
    eid = make_event(client, capacity=3)
    reserve(client, eid, seats=2)
    res = join(client, eid)
    assert res.status_code == 409
    assert res.json() == {"detail": SOLD_OUT_MSG}


# --- AC3.3 -------------------------------------------------------------------
@pytest.mark.parametrize("seats", [0, -1, 11])
def test_AC3_3_seats_out_of_range_rejected(client, seats):
    """Given a request for fewer than 1 or more than 10 seats When the attendee joins the waitlist Then
    it is rejected with "You can wait for between 1 and 10 seats"."""
    eid, _ = sold_out_event(client)
    res = join(client, eid, seats=seats)
    assert res.status_code == 422
    assert res.json() == {"detail": "You can wait for between 1 and 10 seats"}


# --- AC3.4 -------------------------------------------------------------------
@pytest.mark.parametrize("name", ["", "   "])
def test_AC3_4_blank_name_rejected(client, name):
    """Given a blank name or an invalid email When the attendee joins the waitlist Then it is rejected
    with "Name is required" / "A valid email is required"."""
    eid, _ = sold_out_event(client)
    res = join(client, eid, name=name)
    assert res.status_code == 422
    assert res.json() == {"detail": "Name is required"}


@pytest.mark.parametrize("email", ["", "not-an-email", "a@b", "a b@example.com"])
def test_AC3_4_invalid_email_rejected(client, email):
    """Given a blank name or an invalid email When the attendee joins the waitlist Then it is rejected
    with "Name is required" / "A valid email is required"."""
    eid, _ = sold_out_event(client)
    res = join(client, eid, email=email)
    assert res.status_code == 422
    assert res.json() == {"detail": "A valid email is required"}


def test_AC3_4_name_checked_before_email_before_seats(client):
    """Given a blank name or an invalid email When the attendee joins the waitlist Then it is rejected
    with "Name is required" / "A valid email is required"."""
    eid, _ = sold_out_event(client)
    res = join(client, eid, name="", email="bad", seats=0)
    assert res.json() == {"detail": "Name is required"}
    res = join(client, eid, email="bad", seats=0)
    assert res.json() == {"detail": "A valid email is required"}


# --- AC3.5 -------------------------------------------------------------------
def test_AC3_5_duplicate_waiting_email_rejected(client):
    """Given an email that already has a waiting entry for the event When that email joins the waitlist
    of the same event again Then it is rejected with "You are already on the waitlist for this event"."""
    eid, _ = sold_out_event(client)
    join_ok(client, eid)
    res = join(client, eid)
    assert res.status_code == 409
    assert res.json() == {"detail": "You are already on the waitlist for this event"}


def test_AC3_5_duplicate_email_case_insensitive(client):
    """Given an email that already has a waiting entry for the event When that email joins the waitlist
    of the same event again Then it is rejected with "You are already on the waitlist for this event"."""
    eid, _ = sold_out_event(client)
    join_ok(client, eid, email="Grace@Example.com")
    res = join(client, eid, email="grace@example.com")
    assert res.status_code == 409
    assert res.json() == {"detail": "You are already on the waitlist for this event"}


def test_AC3_5_same_email_other_event_allowed(client):
    """Given an email that already has a waiting entry for the event When that email joins the waitlist
    of the same event again Then it is rejected with "You are already on the waitlist for this event"."""
    e1, _ = sold_out_event(client, name="One")
    e2, _ = sold_out_event(client, name="Two")
    join_ok(client, e1)
    assert join(client, e2).status_code == 201


def test_AC3_5_same_email_can_rejoin_after_leaving(client):
    """Given an email that already has a waiting entry for the event When that email joins the waitlist
    of the same event again Then it is rejected with "You are already on the waitlist for this event"."""
    eid, _ = sold_out_event(client)
    first = join_ok(client, eid)
    assert client.post(f"/api/waitlist/{first['code']}/leave").status_code == 200
    again = join(client, eid)
    assert again.status_code == 201
    assert again.json()["code"] != first["code"]


# --- AC3.12 ------------------------------------------------------------------
def test_AC3_12_started_sold_out_event_rejected(client, session):
    """Given a sold-out event whose start time is not in the future When an attendee tries to join the
    waitlist Then it is rejected with "This event has already started"."""
    eid = started_sold_out_event(session)
    res = join(client, eid)
    assert res.status_code == 409
    assert res.json() == {"detail": "This event has already started"}


def test_AC3_12_started_event_with_seats_reports_started_first(client, session):
    """Given a sold-out event whose start time is not in the future When an attendee tries to join the
    waitlist Then it is rejected with "This event has already started"."""
    eid = started_open_event(session)
    res = join(client, eid)
    assert res.status_code == 409
    assert res.json() == {"detail": "This event has already started"}


# --- AC3.6 -------------------------------------------------------------------
def test_AC3_6_lookup_waiting_entry(client):
    """Given a waiting entry When the attendee looks it up by waitlist reference Then they see the event
    name, seats wanted, status "Waiting" and their position in line (1 = next)."""
    eid, _ = sold_out_event(client)
    entry = join_ok(client, eid)
    res = lookup(client, entry["code"])
    assert res.status_code == 200
    assert res.json() == {
        "code": entry["code"],
        "event_id": eid,
        "event_name": "Synthwave Night",
        "name": "Grace Hopper",
        "email": "grace@example.com",
        "seats": 2,
        "status": "waiting",
        "position": 1,
        "booking_code": None,
    }


def test_AC3_6_position_reflects_place_in_line(client):
    """Given a waiting entry When the attendee looks it up by waitlist reference Then they see the event
    name, seats wanted, status "Waiting" and their position in line (1 = next)."""
    eid, _ = sold_out_event(client)
    a = join_ok(client, eid, email="a@example.com")
    b = join_ok(client, eid, email="b@example.com")
    assert lookup(client, a["code"]).json()["position"] == 1
    assert lookup(client, b["code"]).json()["position"] == 2


def test_AC3_6_lookup_is_case_insensitive(client):
    """Given a waiting entry When the attendee looks it up by waitlist reference Then they see the event
    name, seats wanted, status "Waiting" and their position in line (1 = next)."""
    eid, _ = sold_out_event(client)
    entry = join_ok(client, eid)
    res = lookup(client, entry["code"].lower())
    assert res.status_code == 200
    assert res.json()["code"] == entry["code"]


# --- AC3.7 -------------------------------------------------------------------
def test_AC3_7_lookup_promoted_entry_shows_booking_reference(client):
    """Given a promoted entry When the attendee looks it up by waitlist reference Then they see status
    "Promoted" and the booking reference of their confirmed reservation."""
    eid, booking = sold_out_event(client, capacity=4)
    entry = join_ok(client, eid, seats=2)
    cancel(client, booking)
    res = lookup(client, entry["code"])
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "promoted"
    assert data["position"] is None
    assert len(data["booking_code"]) == 8
    resv = client.get(f"/api/reservations/{data['booking_code']}")
    assert resv.status_code == 200
    assert resv.json()["status"] == "confirmed"
    assert resv.json()["seats"] == 2
    assert resv.json()["email"] == "grace@example.com"
    assert resv.json()["event_id"] == eid


# --- AC3.8 -------------------------------------------------------------------
def test_AC3_8_lookup_unknown_code_404(client):
    """Given a waitlist reference that does not exist When the attendee looks it up or leaves with it
    Then they get "Waitlist entry not found"."""
    res = lookup(client, "ZZZZZZZZ")
    assert res.status_code == 404
    assert res.json() == {"detail": "Waitlist entry not found"}


def test_AC3_8_leave_unknown_code_404(client):
    """Given a waitlist reference that does not exist When the attendee looks it up or leaves with it
    Then they get "Waitlist entry not found"."""
    res = client.post("/api/waitlist/ZZZZZZZZ/leave")
    assert res.status_code == 404
    assert res.json() == {"detail": "Waitlist entry not found"}


# --- AC3.9 -------------------------------------------------------------------
def test_AC3_9_cancel_promotes_first_waiting_entry(client):
    """Given a waitlist with entries and a reservation that is cancelled When the freed seats cover the
    seats wanted by the first waiting entry in join order Then that entry is promoted to a confirmed
    reservation with a booking reference and the event's seats available drop by its seats wanted."""
    eid, booking = sold_out_event(client, capacity=4)
    first = join_ok(client, eid, email="a@example.com", seats=3)
    second = join_ok(client, eid, email="b@example.com", seats=1)
    assert available(client, eid) == 0
    cancel(client, booking)
    promoted = lookup(client, first["code"]).json()
    assert promoted["status"] == "promoted"
    assert promoted["booking_code"]
    assert available(client, eid) == 4 - 3 - 1  # both fit: 3 then 1
    assert lookup(client, second["code"]).json()["status"] == "promoted"


def test_AC3_9_only_first_in_line_promoted_when_only_it_fits(client):
    """Given a waitlist with entries and a reservation that is cancelled When the freed seats cover the
    seats wanted by the first waiting entry in join order Then that entry is promoted to a confirmed
    reservation with a booking reference and the event's seats available drop by its seats wanted."""
    eid, booking = sold_out_event(client, capacity=4)
    first = join_ok(client, eid, email="a@example.com", seats=3)
    second = join_ok(client, eid, email="b@example.com", seats=3)
    cancel(client, booking)
    assert lookup(client, first["code"]).json()["status"] == "promoted"
    assert lookup(client, second["code"]).json()["status"] == "waiting"
    assert available(client, eid) == 1


def test_AC3_9_promoted_reservation_is_confirmed_with_entry_details(client):
    """Given a waitlist with entries and a reservation that is cancelled When the freed seats cover the
    seats wanted by the first waiting entry in join order Then that entry is promoted to a confirmed
    reservation with a booking reference and the event's seats available drop by its seats wanted."""
    eid, booking = sold_out_event(client, capacity=4)
    entry = join_ok(client, eid, seats=2)
    cancel(client, booking)
    code = lookup(client, entry["code"]).json()["booking_code"]
    resv = client.get(f"/api/reservations/{code}").json()
    assert resv["status"] == "confirmed"
    assert resv["name"] == "Grace Hopper"
    assert code.isalnum() and code == code.upper()
    assert available(client, eid) == 2


def test_AC3_9_cancel_response_unchanged(client):
    """Given a waitlist with entries and a reservation that is cancelled When the freed seats cover the
    seats wanted by the first waiting entry in join order Then that entry is promoted to a confirmed
    reservation with a booking reference and the event's seats available drop by its seats wanted."""
    eid, booking = sold_out_event(client, capacity=4)
    join_ok(client, eid, seats=2)
    res = cancel(client, booking)
    assert res.json()["code"] == booking
    assert res.json()["status"] == "cancelled"


def test_AC3_9_cancel_without_waitlist_just_frees_seats(client):
    """Given a waitlist with entries and a reservation that is cancelled When the freed seats cover the
    seats wanted by the first waiting entry in join order Then that entry is promoted to a confirmed
    reservation with a booking reference and the event's seats available drop by its seats wanted."""
    eid, booking = sold_out_event(client, capacity=4)
    cancel(client, booking)
    assert available(client, eid) == 4


def test_AC3_9_cancelling_promoted_reservation_promotes_next(client):
    """Given a waitlist with entries and a reservation that is cancelled When the freed seats cover the
    seats wanted by the first waiting entry in join order Then that entry is promoted to a confirmed
    reservation with a booking reference and the event's seats available drop by its seats wanted."""
    eid, booking = sold_out_event(client, capacity=2)
    first = join_ok(client, eid, email="a@example.com", seats=2)
    second = join_ok(client, eid, email="b@example.com", seats=2)
    cancel(client, booking)
    first_booking = lookup(client, first["code"]).json()["booking_code"]
    assert lookup(client, second["code"]).json()["status"] == "waiting"
    cancel(client, first_booking)
    assert lookup(client, second["code"]).json()["status"] == "promoted"
    assert available(client, eid) == 0


def test_AC3_9_seats_never_exceed_capacity(client):
    """Given a waitlist with entries and a reservation that is cancelled When the freed seats cover the
    seats wanted by the first waiting entry in join order Then that entry is promoted to a confirmed
    reservation with a booking reference and the event's seats available drop by its seats wanted."""
    eid = make_event(client, capacity=5)
    b1 = reserve(client, eid, seats=2, email="r1@example.com")
    reserve(client, eid, seats=3, email="r2@example.com")
    for i in range(4):
        join_ok(client, eid, email=f"w{i}@example.com", seats=2)
    cancel(client, b1)
    assert available(client, eid) >= 0
    assert available(client, eid) == 0


# --- AC3.10 ------------------------------------------------------------------
def test_AC3_10_non_fitting_first_entry_is_skipped_and_keeps_place(client):
    """Given several waiting entries and seats freed by a cancellation When the first entry wants more
    seats than are available Then it stays waiting in its place and the next entry in join order whose
    seats fit is promoted, repeating until no remaining waiting entry fits."""
    eid, booking = sold_out_event(client, capacity=2)
    big = join_ok(client, eid, email="big@example.com", seats=5)
    small = join_ok(client, eid, email="small@example.com", seats=2)
    cancel(client, booking)
    big_now = lookup(client, big["code"]).json()
    assert big_now["status"] == "waiting"
    assert big_now["position"] == 1
    small_now = lookup(client, small["code"]).json()
    assert small_now["status"] == "promoted"
    assert small_now["booking_code"]
    assert available(client, eid) == 0


def test_AC3_10_repeats_until_nothing_fits(client):
    """Given several waiting entries and seats freed by a cancellation When the first entry wants more
    seats than are available Then it stays waiting in its place and the next entry in join order whose
    seats fit is promoted, repeating until no remaining waiting entry fits."""
    eid, booking = sold_out_event(client, capacity=5)
    w1 = join_ok(client, eid, email="w1@example.com", seats=3)
    w2 = join_ok(client, eid, email="w2@example.com", seats=3)
    w3 = join_ok(client, eid, email="w3@example.com", seats=1)
    w4 = join_ok(client, eid, email="w4@example.com", seats=2)
    cancel(client, booking)
    # freed 5: w1 (3) promoted -> 2 left; w2 (3) skipped; w3 (1) promoted -> 1 left; w4 (2) skipped
    statuses = [lookup(client, w["code"]).json() for w in (w1, w2, w3, w4)]
    assert [s["status"] for s in statuses] == ["promoted", "waiting", "promoted", "waiting"]
    assert statuses[1]["position"] == 1
    assert statuses[3]["position"] == 2
    assert available(client, eid) == 1


def test_AC3_10_skipped_entry_promoted_by_later_cancellation(client):
    """Given several waiting entries and seats freed by a cancellation When the first entry wants more
    seats than are available Then it stays waiting in its place and the next entry in join order whose
    seats fit is promoted, repeating until no remaining waiting entry fits."""
    eid = make_event(client, capacity=4)
    b1 = reserve(client, eid, seats=1, email="r1@example.com")
    b2 = reserve(client, eid, seats=3, email="r2@example.com")
    big = join_ok(client, eid, email="big@example.com", seats=4)
    cancel(client, b1)
    assert lookup(client, big["code"]).json()["status"] == "waiting"
    cancel(client, b2)
    assert lookup(client, big["code"]).json()["status"] == "promoted"
    assert available(client, eid) == 0


# --- AC3.11 ------------------------------------------------------------------
def test_AC3_11_leave_removes_from_line_and_moves_others_up(client):
    """Given a waiting entry When the attendee leaves the waitlist Then the entry is removed from the
    line and the positions of those behind it each move up by one."""
    eid, _ = sold_out_event(client)
    a = join_ok(client, eid, email="a@example.com")
    b = join_ok(client, eid, email="b@example.com")
    c = join_ok(client, eid, email="c@example.com")
    res = client.post(f"/api/waitlist/{a['code']}/leave")
    assert res.status_code == 200
    assert res.json() == {
        "code": a["code"],
        "event_id": eid,
        "event_name": "Synthwave Night",
        "name": "Grace Hopper",
        "email": "a@example.com",
        "seats": 2,
        "status": "left",
        "position": None,
        "booking_code": None,
    }
    assert lookup(client, b["code"]).json()["position"] == 1
    assert lookup(client, c["code"]).json()["position"] == 2


def test_AC3_11_leaving_middle_entry_only_moves_those_behind(client):
    """Given a waiting entry When the attendee leaves the waitlist Then the entry is removed from the
    line and the positions of those behind it each move up by one."""
    eid, _ = sold_out_event(client)
    a = join_ok(client, eid, email="a@example.com")
    b = join_ok(client, eid, email="b@example.com")
    c = join_ok(client, eid, email="c@example.com")
    client.post(f"/api/waitlist/{b['code']}/leave")
    assert lookup(client, a["code"]).json()["position"] == 1
    assert lookup(client, c["code"]).json()["position"] == 2


def test_AC3_11_left_entry_is_not_promoted(client):
    """Given a waiting entry When the attendee leaves the waitlist Then the entry is removed from the
    line and the positions of those behind it each move up by one."""
    eid, booking = sold_out_event(client, capacity=2)
    a = join_ok(client, eid, email="a@example.com", seats=2)
    b = join_ok(client, eid, email="b@example.com", seats=2)
    client.post(f"/api/waitlist/{a['code']}/leave")
    cancel(client, booking)
    assert lookup(client, a["code"]).json()["status"] == "left"
    assert lookup(client, b["code"]).json()["status"] == "promoted"


def test_rule_leave_promoted_entry_rejected(client):
    """Business rule: a promoted entry can no longer be left; attempting to is rejected with "Only
    waiting entries can be left"."""
    eid, booking = sold_out_event(client, capacity=2)
    entry = join_ok(client, eid, seats=2)
    cancel(client, booking)
    res = client.post(f"/api/waitlist/{entry['code']}/leave")
    assert res.status_code == 409
    assert res.json() == {"detail": "Only waiting entries can be left"}
    assert lookup(client, entry["code"]).json()["status"] == "promoted"


def test_rule_leave_twice_rejected(client):
    """Business rule: leaving an entry that has already been left is rejected with "Only waiting
    entries can be left"."""
    eid, _ = sold_out_event(client)
    entry = join_ok(client, eid)
    assert client.post(f"/api/waitlist/{entry['code']}/leave").status_code == 200
    res = client.post(f"/api/waitlist/{entry['code']}/leave")
    assert res.status_code == 409
    assert res.json() == {"detail": "Only waiting entries can be left"}


# --- Pages -------------------------------------------------------------------
def page_join(client, event_id, **overrides):
    data = {"name": "Grace Hopper", "email": "grace@example.com", "seats": "2"} | overrides
    return client.post(f"/events/{event_id}/waitlist", data=data, follow_redirects=False)


def test_AC3_1_page_join_form_only_when_sold_out(client):
    """Given a sold-out event When an attendee joins the waitlist with their name, email and N seats
    (1–10) Then a waitlist entry is created with a waitlist reference, status "Waiting" and their
    position in line (last)."""
    open_id = make_event(client, capacity=10)
    html = client.get(f"/events/{open_id}").text
    assert "Reserve seats" in html
    assert "Join waitlist" not in html

    full_id, _ = sold_out_event(client)
    html = client.get(f"/events/{full_id}").text
    assert "This event is sold out" in html
    assert "Join the waitlist" in html
    assert "Join waitlist" in html
    assert "Reserve seats" not in html


def test_AC3_2_page_no_join_form_when_seats_available(client):
    """Given an event that still has seats available When an attendee tries to join the waitlist Then
    it is rejected with "Seats are still available — reserve instead"."""
    eid = make_event(client, capacity=10)
    assert "Join the waitlist" not in client.get(f"/events/{eid}").text
    res = page_join(client, eid)
    assert res.status_code == 409
    assert SOLD_OUT_MSG in res.text


def test_AC3_1_page_join_redirects_to_waiting_card(client):
    """Given a sold-out event When an attendee joins the waitlist with their name, email and N seats
    (1–10) Then a waitlist entry is created with a waitlist reference, status "Waiting" and their
    position in line (last)."""
    eid, _ = sold_out_event(client)
    res = page_join(client, eid)
    assert res.status_code == 303
    location = res.headers["location"]
    assert location.startswith("/waitlist/")
    code = location.rsplit("/", 1)[1]
    page = client.get(location)
    assert page.status_code == 200
    assert f"Waitlist entry {code}" in page.text
    assert "Synthwave Night" in page.text
    assert "2 seats wanted" in page.text
    assert "Status: Waiting" in page.text
    assert "Position in line: 1" in page.text
    assert "Leave waitlist" in page.text
    # the same entry is visible through the API
    assert lookup(client, code).json()["status"] == "waiting"


def test_AC3_3_page_seats_out_of_range_error(client):
    """Given a request for fewer than 1 or more than 10 seats When the attendee joins the waitlist Then
    it is rejected with "You can wait for between 1 and 10 seats"."""
    eid, _ = sold_out_event(client)
    res = page_join(client, eid, seats="0")
    assert res.status_code == 422
    assert "You can wait for between 1 and 10 seats" in res.text
    res = page_join(client, eid, seats="abc")
    assert res.status_code == 422
    assert "You can wait for between 1 and 10 seats" in res.text


def test_AC3_4_page_blank_name_and_bad_email_errors(client):
    """Given a blank name or an invalid email When the attendee joins the waitlist Then it is rejected
    with "Name is required" / "A valid email is required"."""
    eid, _ = sold_out_event(client)
    res = page_join(client, eid, name="  ")
    assert res.status_code == 422
    assert "Name is required" in res.text
    res = page_join(client, eid, email="nope")
    assert res.status_code == 422
    assert "A valid email is required" in res.text


def test_AC3_5_page_duplicate_email_error(client):
    """Given an email that already has a waiting entry for the event When that email joins the waitlist
    of the same event again Then it is rejected with "You are already on the waitlist for this event"."""
    eid, _ = sold_out_event(client)
    assert page_join(client, eid).status_code == 303
    res = page_join(client, eid)
    assert res.status_code == 409
    assert "You are already on the waitlist for this event" in res.text
    assert 'class="alert error"' in res.text


def test_AC3_12_page_started_event_error(client, session):
    """Given a sold-out event whose start time is not in the future When an attendee tries to join the
    waitlist Then it is rejected with "This event has already started"."""
    eid = started_sold_out_event(session)
    res = page_join(client, eid)
    assert res.status_code == 409
    assert "This event has already started" in res.text


def test_rule_page_join_unknown_event_404(client):
    """Business rule: joining the waitlist of an unknown event shows "Event not found"."""
    res = page_join(client, 9999)
    assert res.status_code == 404
    assert "Event not found" in res.text


def test_AC3_7_page_promoted_card_shows_booking_reference(client):
    """Given a promoted entry When the attendee looks it up by waitlist reference Then they see status
    "Promoted" and the booking reference of their confirmed reservation."""
    eid, booking = sold_out_event(client, capacity=2)
    entry = join_ok(client, eid, seats=2)
    cancel(client, booking)
    code = lookup(client, entry["code"]).json()["booking_code"]
    page = client.get(f"/waitlist/{entry['code']}")
    assert page.status_code == 200
    assert "Status: Promoted" in page.text
    assert "Booking reference: " in page.text
    assert f'href="/reservations/{code}"' in page.text
    assert "Leave waitlist" not in page.text
    assert "Position in line" not in page.text


def test_AC3_6_page_waiting_card_one_seat_wording_and_position(client):
    """Given a waiting entry When the attendee looks it up by waitlist reference Then they see the event
    name, seats wanted, status "Waiting" and their position in line (1 = next)."""
    eid, _ = sold_out_event(client)
    join_ok(client, eid, email="a@example.com")
    b = join_ok(client, eid, email="b@example.com", seats=1)
    page = client.get(f"/waitlist/{b['code']}")
    assert "1 seat wanted" in page.text
    assert "Position in line: 2" in page.text


def test_AC3_8_page_unknown_code_404_full_page(client):
    """Given a waitlist reference that does not exist When the attendee looks it up or leaves with it
    Then they get "Waitlist entry not found"."""
    res = client.get("/waitlist/ZZZZZZZZ")
    assert res.status_code == 404
    assert "Waitlist entry not found" in res.text
    assert "<html" in res.text


def test_AC3_11_page_htmx_leave_returns_left_card(client):
    """Given a waiting entry When the attendee leaves the waitlist Then the entry is removed from the
    line and the positions of those behind it each move up by one."""
    eid, _ = sold_out_event(client)
    a = join_ok(client, eid, email="a@example.com")
    b = join_ok(client, eid, email="b@example.com")
    res = client.post(f"/waitlist/{a['code']}/leave", headers={"HX-Request": "true"})
    assert res.status_code == 200
    assert "<html" not in res.text
    assert 'id="waitlist-entry"' in res.text
    assert "Status: Left" in res.text
    assert "You have left the waitlist" in res.text
    assert "Leave waitlist" not in res.text
    assert "Position in line" not in res.text
    assert "Position in line: 1" in client.get(f"/waitlist/{b['code']}").text
    # a later lookup of the left entry still shows Left
    assert "Status: Left" in client.get(f"/waitlist/{a['code']}").text


def test_AC3_11_page_htmx_leave_promoted_409_card(client):
    """Given a waiting entry When the attendee leaves the waitlist Then the entry is removed from the
    line and the positions of those behind it each move up by one."""
    eid, booking = sold_out_event(client, capacity=2)
    entry = join_ok(client, eid, seats=2)
    cancel(client, booking)
    res = client.post(f"/waitlist/{entry['code']}/leave", headers={"HX-Request": "true"})
    assert res.status_code == 409
    assert "<html" not in res.text
    assert 'id="waitlist-entry"' in res.text
    assert "Only waiting entries can be left" in res.text


def test_AC3_8_page_htmx_leave_unknown_404_partial(client):
    """Given a waitlist reference that does not exist When the attendee looks it up or leaves with it
    Then they get "Waitlist entry not found"."""
    res = client.post("/waitlist/ZZZZZZZZ/leave", headers={"HX-Request": "true"})
    assert res.status_code == 404
    assert "Waitlist entry not found" in res.text
    assert "<html" not in res.text
