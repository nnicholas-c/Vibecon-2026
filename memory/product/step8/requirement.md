# Phase: step8 — Task 2 routing fixes (user's task text is the source of truth)

Version: step8-1. The insertion and pricing engine is correct: don't rewrite it, only make the five fixes. No full tester run unless the user asks; run the CHECK below.

## Functional requirements
- REQ-700 [always] The system shall not show the "Optimize route" button or its sentence on the van page, and /api/units/{id} shall have no optimize-button field.
- REQ-701 [event] When a request is accepted, a stop is marked done, a stop is moved, or a van is added or removed, the system shall run the existing optimize/preview logic for the affected van(s) and apply it automatically.
- REQ-702 [event] When an auto-reoptimise changes a van's order, the system shall write an event {ts, van_id, text: "Van 2 reordered, saves N min"}.
- REQ-703 [always] The system shall expose GET /api/events?since=<ts> returning reorder events after ts.
- REQ-704 [state] While any app page is open, the system shall poll /api/events?since=... every 10 s (no websockets) and show each new reorder event as a toast.
- REQ-705 [always] The system shall compute spare_minutes = shift_minutes - driving_minutes - service_minutes, counting waiting between windows as spare.
- REQ-706 [always] The system shall show that spare value everywhere it appears (fleet strip, van table, van page).
- REQ-707 [always] The system shall label the van page's "Day used" tile "Driving and stops: X of Y min".
- REQ-708 [always] The system shall price a request at demo clock T with the first new stop's arrival including travel from the van's current location at T (the stop it's at, or its position on the current leg), not from the previous scheduled stop.
- REQ-709 [event] When two option cards have the same van and the same price, the system shall merge them into one card labelled "Cheapest and soonest".
- REQ-710 [state] While the parsed request has no explicit requested time (asked_minutes is null), the system shall not show a "Preferred window" card.
- REQ-711 [always] The system shall show at most two option cards.
- REQ-712 [always] The system shall seed each van's stop windows spread across its shift, with no idle gap over 30 minutes between consecutive stops, keeping stop counts and addresses (only window_start/window_end change).
- REQ-713 [event] When Reset demo data runs, the system shall rebuild the new seed windows.

## Quality requirements
Q-700 Tag: Check.Van3
      Scale: GET /api/units/van-3 after accepting any request: optimize field present? spare == shift - driving - service? max gap between consecutive arrivals
      Meter: script, report the three numbers
      Must: no field; equal; < 35 min
      Plan: no field; equal; <= 30 min
Q-701 Tag: Pricing.Unchanged
      Scale: change in seeded request prices beyond what REQ-708 and REQ-712 cause
      Meter: before/after run-all diff, explained line by line
      Must: every change explained
      Plan: every change explained
