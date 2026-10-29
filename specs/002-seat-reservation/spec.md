# Spec 002 — Seat reservation

**Status:** Approved
**Idea:** [idea.md](idea.md)

## Problem
Attendees can browse events (spec 001) but cannot claim seats, so organisers cannot tell how full an event
is. Reservations must respect capacity and be cancellable so seats go back on sale.

## User stories
- **US1** — As an attendee, I want to reserve one or more seats for an event so that I'm guaranteed entry.
- **US2** — As an attendee, I want a booking reference so that I can look up my reservation later.
- **US3** — As an attendee, I want to cancel my reservation so that my seats go to someone else.

## Acceptance criteria
| ID    | Story | Given / When / Then |
|-------|-------|---------------------|
| AC2.1 | US1   | **Given** an event with at least N seats available **When** an attendee reserves N seats (1–10) with their name and email **Then** the reservation is confirmed with a booking reference and the event's seats available drop by N. |
| AC2.2 | US1   | **Given** a request for fewer than 1 or more than 10 seats **When** the attendee reserves **Then** it is rejected with "You can reserve between 1 and 10 seats". |
| AC2.3 | US1   | **Given** an event with fewer seats available than requested (but not zero) **When** the attendee reserves **Then** it is rejected with "Only X seats left" (X = seats available). |
| AC2.4 | US1   | **Given** an event with no seats available **When** an attendee views or reserves it **Then** it is shown as sold out and reserving is rejected with "This event is sold out". |
| AC2.5 | US1   | **Given** a blank name or an invalid email **When** the attendee reserves **Then** it is rejected with "Name is required" / "A valid email is required". |
| AC2.6 | US2   | **Given** a reservation **When** the attendee looks it up by booking reference **Then** they see the event name, number of seats and status. |
| AC2.7 | US2   | **Given** a booking reference that does not exist **When** the attendee looks it up or cancels it **Then** they get "Reservation not found". |
| AC2.8 | US3   | **Given** a confirmed reservation **When** the attendee cancels it **Then** its status becomes cancelled and its seats become available again. |
| AC2.9 | US3   | **Given** an already cancelled reservation **When** the attendee cancels it again **Then** it is rejected with "Reservation is already cancelled". |

## Business rules
- A reservation holds 1–10 seats. Seats available = capacity − seats in confirmed reservations.
- An event can never have more seats reserved than its capacity.
- Booking references are 8 characters, upper-case letters and digits, unique.
- Reserving for an unknown event fails with "Event not found" (as in spec 001).

## Out of scope
- Payments, tickets/QR codes, emails.
- Changing the number of seats on an existing reservation.
- Seat maps / assigned seating.
- Waitlists (future feature).

## Open questions
- None.
