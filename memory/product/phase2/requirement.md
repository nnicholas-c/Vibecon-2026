# Phase 2 requirements: the pricing engine

**Version:** phase-2

**Goal:** A deterministic plain-Python engine can price any job on every van in under half a second. It finds the cheapest feasible slot, explains the price in one line, cites pass-by evidence, finds a working window when the asked one fails, and can book a job and undo it. A Settings "Engine test" view proves it on the 10 seeded requests.

Read first:
- `/app/memory/product/overview.md`, especially D-2 (demo clock) and **D-14 to D-17**, which change or interpret the spec's engine rules
- `/app/memory/product/spec_part_a.md`, section 6
- Phase 1's `backend/engine/timing.py`, which is reused, not rewritten

**What Phase 1 delivered (build on it):** 6 vans with 20 stops each (spare minutes 45/50/42/43/55/62), Van 2's Shattuck Avenue Imaging (5100 Shattuck) at 1:50pm and Ashby Pediatrics (3000 Telegraph) at 2:15pm, Van 4's Lakeshore Eye Care at 3:50pm and Piedmont Avenue Pediatrics at 4:05pm (returns 4:17pm), route plans with the previous version kept, and Settings on the business document.

**Out of scope:** reading request text (Phase 4; Phase 2 uses hand-made structured versions of the seeded requests), maps, AI, quotes, phones, prospecting UI.

## Functional requirements

### Engine input
- REQ-92 [always] The engine shall take a structured job made of an ordered list of new stops (kind, name, address, latitude, longitude, window start, window end, service minutes, items, opening hours if known), pickup-to-dropoff pairs, and a frequency (one-off on a date, every weekday, or specific weekdays). Phase 4's request reader will produce exactly this shape.
- REQ-93 [always] New stops without their own service minutes shall use "Minutes per new stop" from Settings (default 4).
- REQ-94 [always] The system shall store a structured job for each of the 10 seeded requests, built by hand from spec section 5 with directory coordinates (interpreted).
- REQ-95 [always] Seeded requests that can't be structured honestly (request 6, missing addresses; request 7, city unclear) shall be stored as "Can't price yet" with a plain-words reason, not given made-up locations (interpreted).
- REQ-96 [unwanted] If a job has no stops, a stop without coordinates, or a window that ends before it starts, then the engine shall return a plain-words error and no price.

### Travel matrix
- REQ-97 [event] When the seed is created, the system shall precompute and cache the travel time and distance between every pair of seeded stops and start/end locations in travel_matrix.
- REQ-98 [event] When the owner saves a change to a speed, the bridge minutes or the road factor, the system shall rebuild the travel matrix.
- REQ-99 [always] Legs involving a new, unseeded point shall be computed on the fly with the same travel model.

### Insertion
- REQ-100 [always] For a single new stop, the engine shall try every unit and every position in that unit's order, including first and last.
- REQ-101 [always] For a pickup-and-dropoff pair, the engine shall try every pickup position and every dropoff position after it.
- REQ-102 [always] For a job with several stops, the engine shall insert them one at a time in the given order, each at its cheapest position, and report the total.
- REQ-103 [always] The engine shall keep only options where the whole route stays feasible (every arrival inside its window, return at or before shift end, items within capacity).
- REQ-104 [always] Every-weekday jobs shall be priced against the unit's standard weekday route.
- REQ-105 [always] One-off jobs shall be priced against that date's route (the weekday route plus that date's one-off stops).
- REQ-106 [always] Specific-weekday jobs shall be priced against the weekday route and charged for those days only, at 4.3 visits a month per weekday.
- REQ-107 [always] For a one-off job on the demo date, new stops shall only go after the van's position at the demo clock time (D-17).
- REQ-108 [always] A unit shall only take a job that needs a skill if it has that skill.
- REQ-109 [always] After choosing an insertion, the engine shall try swapping each pair of neighboring stops once and keep any swap that shortens the route without breaking a window.
- REQ-110 [always] Added minutes shall equal the extra driving minutes plus the new stops' service minutes (D-14).
- REQ-111 [always] Added miles shall equal new route miles minus old route miles.
- REQ-112 [always] Added minutes and added miles shall never be shown below zero (interpreted).
- REQ-113 [always] Added cost shall equal added minutes (whole) x wage per minute plus added miles (0.1 mi) x cost per mile, rounded to the cent.
- REQ-114 [always] For every unit, the engine shall return feasible yes or no, the best position or positions, the new arrival times of the new stops, added minutes, added miles and added cost.
- REQ-115 [always] The winner shall be the feasible unit with the lowest added cost, with ties going to fewer added minutes (interpreted).

### When a unit can't take it
- REQ-116 [unwanted] If a unit can't take the job, then the engine shall return one plain-words reason: "the window has already passed", "can't reach it in time", "past shift end", "no room" or "missing skill".
- REQ-117 [always] Each infeasible result shall include where the van is around the requested time and until when (for example area "San Francisco" until "3:10pm"), for the Phase 5 comparison card template.
- REQ-118 [unwanted] If no unit can take the job as asked, then the engine shall try windows moved earlier and later in 15-minute steps up to 2 hours each way, and report the first window that works with its unit and added cost.
- REQ-119 [always] The window search shall respect known opening hours (D-15).
- REQ-120 [always] For pickup-and-dropoff jobs, the window search shall move the dropoff deadline later (and the pickup earlier) before moving both together (D-16).
- REQ-121 [unwanted] If no shifted window within 2 hours works, then the engine shall say "No time within 2 hours works" with each unit's reason.

### Price
- REQ-122 [always] The suggested price shall be the higher of (added cost plus markup) and the floor for that job type, rounded up to the next 50 cents.
- REQ-123 [always] Every-weekday and specific-weekday jobs shall use "floor per recurring visit". One-off jobs shall use "floor per one-off run".
- REQ-124 [always] The engine shall never return a price below the applicable floor.
- REQ-125 [always] Margin shall equal price minus added cost.
- REQ-126 [always] Every-weekday jobs shall show a monthly total of price x weekdays per month (21).
- REQ-127 [always] Specific-weekday jobs shall show a monthly total of price x 4.3 x the number of weekdays.
- REQ-128 [always] The explanation line shall follow the form: "Adds 9 min and 0.1 mi to Van 2, which costs $2.97. Your floor is $11, so the quote is $11 a visit, or $231 a month."
- REQ-129 [always] When markup sets the price, the line shall read like: "Adds 40 min and 6.2 mi to Van 3, which costs $17.56. With your 100% markup, the quote is $35.50 a visit, or $745.50 a month."
- REQ-130 [always] One-off results shall add the market reference line "A typical on-demand run in the Bay Area is $45 to $65." using the Settings values.
- REQ-131 [always] The winner shall carry a pass-by line naming the existing stop nearest the new stop, like "Van 2 stops at 5100 Shattuck at 1:50pm, 0.1 miles from you." (straight-line distance, interpreted).
- REQ-132 [always] Every price shall be recomputed from current Settings each time; changing a floor, the markup, the wage or the cost per mile changes the next result.

### Engine actions (API, documented in /api/openapi.json)
- REQ-133 [always] The API shall price a job across all units and return every unit's result plus the winner.
- REQ-134 [always] The API shall price a job for one named unit.
- REQ-135 [always] The API shall run a what-if that moves an existing stop to another unit and shows both units' change in minutes, miles and cost, without saving anything.
- REQ-136 [unwanted] If the what-if move is infeasible on the target unit, then the API shall return the plain-words reason.
- REQ-137 [event] When an option is accepted, the system shall insert the new stops on that unit with source "quote", recompute the affected route plan, and save the previous plan.
- REQ-138 [always] Every-weekday stops created from a job shall carry an optional start date (for example next Monday for "starting next week").
- REQ-139 [unwanted] If an accepted option is no longer feasible because the route changed, then the system shall refuse it with "This slot is no longer free. Price it again."
- REQ-140 [event] When undo is called, the system shall restore the most recent change's previous route plan and remove the stops it added.
- REQ-141 [unwanted] If there is nothing to undo, then the system shall return "Nothing to undo".
- REQ-142 [always] The fleet stats action shall return per unit: stops, spare minutes today, spare minutes for each weekday Monday to Friday of the demo week and their total, revenue per day, cost per stop, on-time rate over 4 weeks, morning and afternoon on-time rates, late-run count and average minutes late.
- REQ-143 [always] The unit stats action shall return the same fields for one unit.
- REQ-144 [always] The unit page and Dispatch table shall show today's route (the weekday route plus the demo date's one-off stops), so an accepted job shows up there.

### Engine test view (in Settings)
- REQ-145 [always] Settings shall contain an "Engine test" view listing the 10 seeded requests, each with a one-line summary of its structured job.
- REQ-146 [event] When the owner presses "Run all", the system shall price every priceable seeded request across all six vans and show the results.
- REQ-147 [always] Each request's result shall show, per van: feasible or not, added minutes, added miles, added cost, the new stops' arrival times, or the plain-words reason.
- REQ-148 [always] Each request's result shall highlight the winner and show its price, explanation line, pass-by line, monthly total or market reference, and any working shifted window.
- REQ-149 [always] Each request's result shall show the engine time in milliseconds.
- REQ-150 [always] The view shall show the hand-check formula for the winner, for example "9 min x $0.3212 + 0.1 mi x $0.76 = $2.97".
- REQ-151 [always] The view shall offer a what-if control: pick a stop and a target van, and see both vans' change.
- REQ-152 [unwanted] If running the engine fails, then the view shall show "The engine hit a problem on this request. Try again." without raw errors.
- REQ-153 [always] The Engine test view shall not change any route.

## Quality requirements

```
Q-13 Tag: Perf.PriceAllUnits
     Scale: ms server-side to price one normal request (requests 1, 2, 3, 4, 8) across all 6 vans, including window search
     Meter: engine timing shown in Engine test, 5 runs each, max
     Must: 500
     Plan: 150
```
```
Q-14 Tag: Perf.MultiStop
     Scale: ms server-side to price request 5 (4 pickups + 1 dropoff) across all 6 vans
     Meter: Engine test timing, 5 runs, max
     Must: 1000 (estimate)
     Plan: 400
```
```
Q-15 Tag: Money.HandCheck
     Scale: cents of difference between shown added cost and (shown minutes x wage/60 + shown miles x cost per mile)
     Meter: API, all feasible winners of the 10 seeded requests
     Must: 1
     Plan: 0
```
```
Q-16 Tag: Money.Floor
     Scale: count of prices below the applicable floor
     Meter: API, all 10 seeded requests x 6 vans, plus floor set to $15
     Must: 0
     Plan: 0
```
```
Q-17 Tag: Trust.Request1
     Scale: request 1 winner and added cost
     Meter: API after fresh reset
     Must: Van 2 wins with added cost under $4
     Plan: Van 2 wins at $2.50 to $3.50, +7 to +11 min (estimate)
```
```
Q-18 Tag: Trust.Deterministic
     Scale: count of differing fields between two runs of the same job on the same data
     Meter: API, request 1 and 5, twice
     Must: 0
     Plan: 0
```
```
Q-19 Tag: Data.Undo (it lost my stuff)
     Scale: count of differences in Van 2's stops and arrival times between before accept and after undo
     Meter: API, accept request 1 then undo
     Must: 0
     Plan: 0
```
```
Q-20 Tag: Usability.Reasons (I can't figure it out)
     Scale: count of infeasible results showing codes, blank reasons or jargon instead of the plain-words list
     Meter: Engine test, all 10 requests
     Must: 0
     Plan: 0
```
```
Q-21 Tag: Domain.DemoClock
     Scale: count of same-day results that use server real time instead of the demo clock
     Meter: API, request 2 with demo clock at 10:00am and at 4:00pm
     Must: 0
     Plan: 0
```
