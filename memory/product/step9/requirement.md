# Phase: step9 — Smarter Done, Reorder on map, Price-cut ruler

Version: step9-1. Small polish on the demo moment. No full tester run unless the user asks. Don't change pricing, insertion or optimizer logic; don't touch agent.py model config/limits.

## Functional requirements
- REQ-750 [event] When the driver taps Done (driver phone or "done" message), the system shall mark the stop the van is at or heading to at the demo clock (its current or next open stop), not the earliest open stop.
- REQ-751 [unwanted] If the van has no open stop at the demo clock, then the system shall reply "No stop to mark done right now." and change nothing.
- REQ-752 [event] When a stop is marked done, the system shall re-time that van's later stops from the done time, so the driver phone, van page and map show the updated times within 10 s.
- REQ-753 [event] When a reorder event fires (step8 "Van N reordered, saves M min"), the system shall show the old and new stop order on that van's map for about 6 seconds: the old route as a faint dashed line, the new route in the van's color, and stop numbers updating, then settle to the new route.
- REQ-754 [state] While the reorder overlay is showing on a page without that van's map (e.g. Inbox), the system shall make the toast's "Show on map" link open the van page with the overlay. (interpreted)
- REQ-755 [state] While reduced motion is on, the system shall show the old and new orders side by side as a static overlay without animation. (interpreted)
- REQ-756 [event] When the "Booked …" toast shows, the system shall include a short horizontal ruler from $0 to the usual price with a marker sliding from the usual price (e.g. $55) down to the quoted price (e.g. $35), labelled with both, in Overpass Mono, ink on paper, accent marker, no gradients.
- REQ-757 [always] The system shall take the ruler's two prices from the same engine numbers as the toast text.
- REQ-758 [state] While reduced motion is on, the system shall show the ruler's marker at the quoted price without sliding.

## Quality requirements
Q-750 Tag: Done.Correctness
      Scale: wrong stop marked done when tapped at a set demo clock
      Meter: script at 3 demo clock times
      Must: 0
      Plan: 0
Q-751 Tag: Demo.Readability
      Scale: seconds the ruler and reorder overlay are clearly readable
      Meter: human on a laptop
      Must: 4
      Plan: 6
