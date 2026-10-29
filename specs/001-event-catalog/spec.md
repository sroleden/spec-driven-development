# Spec 001 — Event catalog

**Status:** Approved
**Idea:** [idea.md](idea.md)

## Problem
Organisers have no way to publish events, and attendees have no single place to see what is coming up and
whether seats are still available. Every later feature (reservations, waitlists) needs events to exist.

## User stories
- **US1** — As an organiser, I want to create an event with its venue, start time, capacity and price so that
  people can find it.
- **US2** — As an attendee, I want to browse upcoming events, soonest first, so that I can pick one.
- **US3** — As an attendee, I want to open an event's page so that I can see its details and seats left.

## Acceptance criteria
| ID    | Story | Given / When / Then |
|-------|-------|---------------------|
| AC1.1 | US1   | **Given** a name, venue, future start time, capacity of 1–10,000 and a price ≥ 0 **When** the organiser creates the event **Then** the event is saved and all of its seats are available. |
| AC1.2 | US1   | **Given** a capacity below 1 or above 10,000 **When** the organiser creates the event **Then** it is rejected with "Capacity must be between 1 and 10000". |
| AC1.3 | US1   | **Given** a start time that is not in the future **When** the organiser creates the event **Then** it is rejected with "Event must start in the future". |
| AC1.4 | US1   | **Given** a blank name or blank venue **When** the organiser creates the event **Then** it is rejected with "Name is required" / "Venue is required". |
| AC1.5 | US1   | **Given** a negative price **When** the organiser creates the event **Then** it is rejected with "Price cannot be negative". |
| AC1.6 | US2   | **Given** past and upcoming events **When** an attendee browses events **Then** only upcoming events are shown, soonest first. |
| AC1.7 | US2   | **Given** no upcoming events **When** an attendee browses events **Then** they see "No upcoming events yet". |
| AC1.8 | US3   | **Given** an existing event **When** an attendee opens it **Then** they see its name, venue, start time, price and seats available. |
| AC1.9 | US3   | **Given** an event that does not exist **When** an attendee opens it **Then** they get "Event not found". |

## Business rules
- Capacity is a whole number from 1 to 10,000.
- Prices are stored in minor units (cents); free events (price 0) are allowed.
- "Upcoming" means the start time is later than now. Times are UTC.

## Out of scope
- Editing or deleting events.
- Organiser accounts / authentication.
- Categories, search, images.

## Open questions
- None.
