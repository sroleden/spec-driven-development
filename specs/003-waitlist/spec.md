# Spec 003 — Waitlist

**Status:** Approved
**Idea:** [idea.md](idea.md)

## Problem
Popular events sell out (spec 002) and interested attendees simply leave, even though cancelled reservations
often put seats back on sale a few days later. Attendees need a way to queue for a sold-out event and get
seats automatically, in fair order, when other attendees cancel.

## User stories
- **US1** — As an attendee, I want to join the waitlist of a sold-out event so that I get a chance at seats if someone cancels.
- **US2** — As an attendee, I want to look up my waitlist entry so that I can see whether I am still waiting, my position in line, or my booking reference.
- **US3** — As an attendee, I want to be given seats automatically when they free up so that I don't have to keep checking the event.
- **US4** — As an attendee, I want to leave the waitlist so that I don't get seats I no longer want.

## Acceptance criteria
| ID     | Story | Given / When / Then |
|--------|-------|---------------------|
| AC3.1  | US1   | **Given** a sold-out event **When** an attendee joins the waitlist with their name, email and N seats (1–10) **Then** a waitlist entry is created with a waitlist reference, status "Waiting" and their position in line (last). |
| AC3.2  | US1   | **Given** an event that still has seats available **When** an attendee tries to join the waitlist **Then** it is rejected with "Seats are still available — reserve instead". |
| AC3.3  | US1   | **Given** a request for fewer than 1 or more than 10 seats **When** the attendee joins the waitlist **Then** it is rejected with "You can wait for between 1 and 10 seats". |
| AC3.4  | US1   | **Given** a blank name or an invalid email **When** the attendee joins the waitlist **Then** it is rejected with "Name is required" / "A valid email is required". |
| AC3.5  | US1   | **Given** an email that already has a waiting entry for the event **When** that email joins the waitlist of the same event again **Then** it is rejected with "You are already on the waitlist for this event". |
| AC3.6  | US2   | **Given** a waiting entry **When** the attendee looks it up by waitlist reference **Then** they see the event name, seats wanted, status "Waiting" and their position in line (1 = next). |
| AC3.7  | US2   | **Given** a promoted entry **When** the attendee looks it up by waitlist reference **Then** they see status "Promoted" and the booking reference of their confirmed reservation. |
| AC3.8  | US2   | **Given** a waitlist reference that does not exist **When** the attendee looks it up or leaves with it **Then** they get "Waitlist entry not found". |
| AC3.9  | US3   | **Given** a waitlist with entries and a reservation that is cancelled **When** the freed seats cover the seats wanted by the first waiting entry in join order **Then** that entry is promoted to a confirmed reservation with a booking reference and the event's seats available drop by its seats wanted. |
| AC3.10 | US3   | **Given** several waiting entries and seats freed by a cancellation **When** the first entry wants more seats than are available **Then** it stays waiting in its place and the next entry in join order whose seats fit is promoted, repeating until no remaining waiting entry fits. |
| AC3.11 | US4   | **Given** a waiting entry **When** the attendee leaves the waitlist **Then** the entry is removed from the line and the positions of those behind it each move up by one. |
| AC3.12 | US1   | **Given** a sold-out event whose start time is not in the future **When** an attendee tries to join the waitlist **Then** it is rejected with "This event has already started". |

## Business rules
- A waitlist entry holds a name, an email and 1–10 seats wanted, and has the status Waiting or Promoted (or
  is left, in which case it is no longer in the line).
- Joining is only allowed while the event is sold out (seats available = 0) and has not started ("started"
  means the start time is not later than now, UTC, consistent with "upcoming" in spec 001).
- An email may have at most one waiting entry per event.
- Join order is the order in which entries were created; position in line counts only Waiting entries.
- Promotion happens automatically when seats become available through a reservation cancellation (spec 002)
  and never leaves an event with more seats reserved than its capacity.
- Entries that do not fit the freed seats are skipped, not removed or demoted; they keep their place.
- A promoted entry becomes a confirmed reservation exactly as in spec 002 (8-character booking reference,
  cancellable); cancelling that reservation frees seats and triggers promotion again.
- A promoted entry can no longer be left; attempting to is rejected with "Only waiting entries can be left".
- There is no limit on waitlist length.
- Joining the waitlist of an unknown event fails with "Event not found" (as in spec 001).
- Waitlist references are 8 characters, upper-case letters and digits, unique.

## Decisions
- An email that already holds a confirmed reservation for the event may still join that event's waitlist; the
  one-waiting-entry-per-email rule (AC3.5) counts only waitlist entries, and no existing AC forbids this.
- A lost waitlist reference cannot be recovered. Lookup is by waitlist reference only; no email is sent and
  looking up by email is not offered.
- Joining is blocked once the event has started (AC3.12). No equivalent wording exists in specs 001/002 or the
  app for joining or reserving (only "Event must start in the future" for event creation, which does not fit),
  so the message is new.

## Out of scope
- Email or any other notification of promotion (attendees must look up their entry).
- Payments, tickets/QR codes.
- Changing the seats wanted on an existing entry.
- Priority, paid or organiser-controlled ordering.
- Limits on waitlist length, expiry of entries.
- Waitlist management by organisers.
- Automatic lapsing of Waiting entries when the event starts (they simply stay Waiting).
- Looking up or recovering a waitlist entry by email.

## Open questions
- None.
