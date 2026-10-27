# Step 3a requirements: sensible routes, an optimizer, and street-following lines

**Version:** step-3a

**Goal:** Each van drives a sensible loop instead of zig-zagging, routes can be optimized without breaking any time slot, and the map lines follow real streets. Read overview V-16.

## Functional requirements
- REQ-329 [always] The seed shall order each van's stops in a sensible geographic loop (area by area, no back-and-forth between areas) and give them time windows consistent with that order.
- REQ-330 [always] The re-seed shall keep the hard targets:
  - Van 2 with a Shattuck Ave stop near 51st at about 1:50pm and a Telegraph Ave stop near Ashby at about 2:15pm, with about 50 spare minutes
  - Van 4's last stops near Lakeshore Ave and Piedmont Ave around 4pm
  - every van with 30 to 70 spare minutes
  - Van 6 the least on time in the afternoon
  - request 1 won by Van 2 under $4, quoting $11
  - request 4 offered at 4:15pm on Van 4
  - request 8 with a later delivery that works
- REQ-331 [always] The system shall have a plain-Python route optimizer (2-opt and or-opt moves) that only accepts orders where every arrival stays in its window, the return stays by shift end and capacity holds.
- REQ-332 [event] When the owner presses "Optimize route" on a van page, the system shall show "Saves X mi and Y min" with Apply and Cancel, or "This is already the shortest order we found".
- REQ-333 [event] When the owner applies an optimized order, the system shall save the previous plan so Undo restores it.
- REQ-334 [event] When a booking is accepted, the system shall run the optimizer on that van and keep the new order only if it's shorter and feasible.
- REQ-335 [always] A booked stop's window shall be its quoted time plus or minus 15 minutes, so optimizing never moves it away from what the customer was told (interpreted).
- REQ-336 [always] Quoted prices and added costs shall stay as computed before any optimization.
- REQ-337 [always] Map route lines shall follow real streets using the OSRM demo server: one request per van route with all stops in order, a custom User-Agent, at most 1 request per second, cached by stop order, refetched only when that route changes, and fetched on first map view rather than at startup.
- REQ-338 [unwanted] If street routing fails, then the map shall draw straight lines and show a small note "Street lines unavailable, showing straight lines."
- REQ-339 [always] The map shall show routing attribution alongside "© OpenStreetMap contributors".
- REQ-340 [always] Pricing shall keep using the built-in travel model. Map geometry never changes a price.
- REQ-341 [always] Reset demo data shall keep the cached street geometry.

## Quality requirements
```
Q-51 Tag: Trust.RouteLooksReal (it looks broken)
     Scale: count of vans whose map route visibly backtracks between areas or crosses itself more than twice
     Meter: human, Fleet map and each van map
     Must: 0
     Plan: 0
```
```
Q-52 Tag: Perf.StreetLines
     Scale: seconds to draw a van's street-following route on a second visit (cached)
     Meter: browser, Van 1 and Van 2, 3 loads each, max
     Must: 2
     Plan: 1
```
```
Q-53 Tag: Money.OptimizerHonest
     Scale: count of time-window breaks or quoted-time moves beyond 15 min after optimizing
     Meter: API, optimize all 6 vans plus a van with request 1 booked
     Must: 0
     Plan: 0
```
