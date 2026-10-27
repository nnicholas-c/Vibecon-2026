# Phase: step11 — Task 3: Email to route without clicks (user's task text is authoritative)

Version: step11-1. Overrides the Oct 25 decision "book only after customer taps Accept": with auto-send on, the accept step is simulated and the request is booked automatically. No full tester unless asked; the CHECK is run by E3.

## Functional requirements
- REQ-850 [state] While Google is connected, the system shall run one backend job that polls Gmail every 10 s with messages.list q="newer_than:1d", using the stored last history id to skip unchanged mailboxes, without any frontend trigger.
- REQ-851 [always] The frontend shall not call /api/gmail/check anywhere.
- REQ-852 [state] While the tab is visible, the frontend shall poll /api/inbox every 5 s from a single effect with cleanup.
- REQ-853 [always] The system shall store the Gmail message id as request.source_key with a unique index, and never create two requests from one message.
- REQ-854 [event] When a request is created (Gmail, Add a request, seed/reset), the system shall run the existing read-and-price pipeline in the background, setting status "reading" then "priced".
- REQ-855 [always] The system shall not show "Read it" or "Read all requests", and shall keep one "Re-read" action on the request detail.
- REQ-856 [always] The request reader shall use the Task 1 env config (AGENT_MODEL, AGENT_API_BASE, AGENT_API_KEY) with reasoning "low", and keep the no-AI fallback.
- REQ-857 [always] The system shall never show a BACKUP badge, storing ai.tag in the record only.
- REQ-858 [event] When auto-send is on and the cheapest option is at or above the floor and doesn't lose money, the system shall mark the request Quoted, then immediately commit it via the existing "Customer taps Accept" path, and mark it Booked.
- REQ-859 [event] When an auto-booking happens, the system shall write an event "Booked {customer}, ${price} instead of ${usual}, {van} already passes {miles} mi away." and show it as a toast.
- REQ-860 [always] The system shall return booked events from GET /api/events?since= along with reorder events.
- REQ-861 [always] The system shall show on each inbox row the source (Gmail, text, photo, manual), sender, received time and status (Reading, Priced, Quoted, Booked, Declined).
- REQ-862 [always] The system shall show the raw email body beside the parsed fields on the request detail.
- REQ-863 [state] While status is "reading", the system shall show a skeleton on the detail pane with "Reading the request", then "Pricing against N vans".
- REQ-864 [unwanted] If the reader model fails or times out, then the system shall price from the no-AI fallback and still auto-book when the rules allow. (interpreted)
- REQ-865 [always] The system shall keep presenter mode and Rehearse working with auto-booking, showing one booking toast (with the price ruler and savings bump) per booking, not two. (interpreted)

## Quality requirements
Q-850 Tag: Check.EmailToBooked
      Scale: seconds from sending "pickup 2 boxes at 1300 Clay St Oakland, deliver to 1261 Fallon St by 3pm today" to status Booked in /api/inbox, one van +2 stops in /api/fleet, Booked line in /api/events
      Meter: E3 script with real Gmail, no clicks
      Must: 30
      Plan: 15
Q-851 Tag: Dedupe
      Scale: duplicate requests from one Gmail message over 10 polls
      Meter: script
      Must: 0
      Plan: 0
Q-852 Tag: ModelBudget
      Scale: model calls per Reset (seed re-read)
      Meter: model_calls_today before/after
      Must: report it
      Plan: at most one per request
