# Phase 1 requirements: the fleet is alive

**Version:** phase-1

**Goal:** Bayline Courier exists in the app. It is seeded, saved and resettable. The owner can see it in a calm three-pane layout with real route timing (stops, arrival times, spare minutes) and stats. A Settings page holds every default. The pricing of new jobs is NOT in this phase.

Read first: `/app/memory/product/overview.md` (kickoff decisions D-1 to D-11 win over the spec) and `/app/memory/product/spec_part_a.md` (sections 4, 5, 6 "Travel model" and "Route timing", and 10).

**Out of scope for Phase 1** (later phases):
- inserting or pricing new jobs, and the travel matrix
- maps
- Claude and any AI
- Inbox screens
- Demo phones
- quotes
- prospecting
- the bar chart, inbox summary and top prospects on Dispatch
- the rail activity dot
- "Refresh from OpenStreetMap", "Send request 1 from the customer phone" and "Customer taps Accept"

## Functional requirements

### Data and seed
- REQ-1 [always] The system shall store its data in the collections named in spec section 4 (businesses, units, stops, route_plans, directory, requests, quotes, prospects, messages, agent_threads, run_history, geo_cache, place_cache, travel_matrix).
- REQ-2 [always] The system shall model units with a kind of van or truck and stops with a kind of pickup, dropoff or job.
- REQ-3 [event] When the backend starts with no Bayline Courier data in the database, the system shall create the full seed from spec section 5.
- REQ-4 [unwanted] If Bayline Courier data already exists at startup, then the system shall leave every existing record unchanged.
- REQ-5 [always] The seed shall contain 6 vans with the names, nicknames, fictional drivers, areas, 8:00am to 5:00pm shifts and start and end locations from spec section 5.
- REQ-6 [always] Each van shall have its own distinct map color.
- REQ-7 [always] Each van shall have about 20 recurring weekday stops (about 120 in total), placed within about 0.6 miles of that van's area centers, in a sensible driving order.
- REQ-8 [always] Each seeded stop shall have a fictional customer name and type that fits its area (labs in Emeryville and Mission Bay, law offices downtown, dental and medical offices in Rockridge and on Piedmont Ave, plus print shops, pharmacies and florists).
- REQ-9 [always] Each seeded stop shall have 3 to 6 service minutes, a time window mostly 1 to 2 hours wide, and a price of $9 to $14 per visit.
- REQ-10 [always] Each van's weekday route shall leave between 30 and 70 spare minutes.
- REQ-11 [always] Van 2's weekday route shall leave about 50 spare minutes.
- REQ-12 [always] Van 2's weekday route shall include a stop on Shattuck Ave near 51st St with a planned arrival of about 1:50pm.
- REQ-13 [always] Van 2's weekday route shall include a stop on Telegraph Ave near Ashby Ave with a planned arrival of about 2:15pm.
- REQ-14 [always] Van 4's last stops of the day shall be near Lakeshore Ave and Piedmont Ave with planned arrivals around 4:00pm.
- REQ-15 [always] Every seeded weekday route shall be feasible: every arrival falls inside its window and the return is at or before 5:00pm.
- REQ-16 [always] The seed shall contain run history for every stop covering the 20 weekdays of the 4 weeks before the demo date.
- REQ-17 [always] Seeded actual arrivals shall mostly fall between 5 minutes early and 10 minutes late against the planned arrival, with a few later runs.
- REQ-18 [always] Seeded actual service minutes shall vary around each stop's planned service minutes.
- REQ-19 [always] A seeded run shall count as on time only when its actual arrival is inside the stop's window.
- REQ-20 [always] Van 6's afternoon runs (window starting at or after 12:00pm) shall have the lowest on-time rate of the six vans (interpreted).
- REQ-21 [always] The directory shall contain the 11 fictional businesses from spec section 5, each with address, coordinates, category, opening hours and a fake 555 phone.
- REQ-22 [always] The seed shall contain about 40 fictional fallback prospects, each within 300 meters of a van's route, in the spec section 9 categories, with opening hours and a fake 555 phone.
- REQ-23 [always] The seed shall contain the 10 requests from spec section 5 with their source, sender, raw text and status "new".
- REQ-24 [always] Every seeded phone number shall be a fake 555 number.
- REQ-25 [event] When the seed is created, the system shall set the demo date to today's date in America/Los_Angeles.
- REQ-26 [always] The system shall treat the demo date as a weekday.
- REQ-27 [event] When the seed is created, the system shall set the demo clock to 10:00am.

### Route timing (plain Python, reusable by the Phase 2 engine)
- REQ-28 [always] The system shall compute the distance between two points as the straight-line distance times the road factor (default 1.3).
- REQ-29 [always] The system shall use 18 mph for legs with both points in San Francisco.
- REQ-30 [always] The system shall use 22 mph for legs with both points in the East Bay.
- REQ-31 [always] The system shall use 30 mph plus a fixed 8 minutes for legs between San Francisco and the East Bay.
- REQ-32 [always] A unit shall leave its start location at shift start.
- REQ-33 [always] Each arrival shall equal the departure from the previous point plus the travel time.
- REQ-34 [always] When a unit arrives before a stop's window opens, the system shall hold the arrival until the window opens.
- REQ-35 [always] A unit shall leave each stop after that stop's service minutes.
- REQ-36 [always] Where a stop has run history, the system shall use its average actual service minutes instead of the planned value.
- REQ-37 [always] The system shall mark a route feasible only when every arrival is inside its window, the return is at or before shift end, and items never exceed capacity.
- REQ-38 [always] The system shall compute route duration as the time from leaving the start location to returning to the end location.
- REQ-39 [always] The system shall compute spare minutes as shift length minus route duration.
- REQ-40 [always] The system shall save one weekday route_plan per unit with the ordered stops, planned arrival and departure times, total minutes, total miles and spare minutes.
- REQ-41 [event] When the owner saves a change to a speed, the bridge minutes or the road factor in Settings, the system shall recompute every route_plan.
- REQ-42 [always] The system shall keep the previous version of a route_plan whenever it recomputes one.

### Layout
- REQ-43 [always] On screens 768px and wider, the system shall show three panes: left rail (about 260px), center chat, right page.
- REQ-44 [always] The left rail top shall show "Bayline Courier" with a business switcher that lists Bayline Courier only.
- REQ-45 [always] The left rail shall pin "Dispatch" first with a fleet icon.
- REQ-46 [always] The left rail shall show one row per unit with its color dot, name, nickname and the status line "N stops, M spare min".
- REQ-47 [always] The left rail bottom shall show Inbox with a count of requests with status "new", plus Phones and Settings.
- REQ-48 [event] When the owner opens Inbox, the system shall show a friendly placeholder that states the request count and "The inbox opens in a later step" (interpreted).
- REQ-49 [event] When the owner opens Phones, the system shall show a friendly "Demo phones arrive in a later step" placeholder (interpreted).
- REQ-50 [always] The header or an empty state shall show "Every van gets an agent that sells its own empty minutes."
- REQ-51 [always] A corner of the app shall show a fictional owner's name (interpreted).
- REQ-52 [always] On screens narrower than 768px, the system shall show the three panes as tabs labeled "List", "Chat" and "Page".
- REQ-53 [event] When the owner selects Dispatch or a unit, the system shall show that agent's chat in the center and its page on the right.
- REQ-54 [always] The app shall open with Dispatch selected (interpreted).

### Placeholder chat
- REQ-55 [event] When the owner sends a message to an agent, the system shall show the owner's bubble followed by an echo reply bubble that repeats the text (interpreted copy: "Echo from <agent name>: <text>").
- REQ-56 [unwanted] If the message box is empty or only spaces, then the system shall keep the send button disabled.
- REQ-57 [always] The system shall save every chat turn in that agent's agent_threads record.
- REQ-58 [always] The chat input shall show 3 suggested prompts for the selected agent type (unit prompts like "Can you take a daily 2pm pickup at 5200 Shattuck?", "Where are your empty minutes today?", "Who should we sell to near your route?"; Dispatch prompts about the whole fleet).
- REQ-59 [event] When the owner taps a suggested prompt, the system shall send that prompt as a message.
- REQ-60 [unwanted] If a chat send fails, then the system shall show "Couldn't send that. Try again." and keep the typed text.

### Unit page
- REQ-61 [always] The unit page header shall show the unit name, nickname, driver name, stops today and spare minutes.
- REQ-62 [always] The unit page shall show today's timeline of stops in route order with the arrival time, customer name, address and window of each stop.
- REQ-63 [always] The unit page shall show a stats row with cost per stop, revenue per day and on-time rate over 4 weeks.
- REQ-64 [always] Cost per stop shall equal (route minutes x wage per minute + route miles x cost per mile) divided by the number of stops (interpreted).
- REQ-65 [always] Revenue per day shall equal the sum of the price per visit of the unit's stops that day (interpreted).
- REQ-66 [always] The on-time rate shall equal on-time runs divided by all runs in the 4 weeks of run history, shown as a percentage.

### Dispatch page
- REQ-67 [always] The Dispatch page shall show a table with one row per unit and the columns stops, spare minutes, revenue per day and cost per stop.
- REQ-68 [always] Stops and spare minutes shall be the same numbers in the left rail, the unit page header and the Dispatch table.

### Settings
- REQ-69 [always] Settings shall show costs and pricing with these defaults: driver wage $19.27 per hour, vehicle cost $0.76 per mile, markup 100%, floor per recurring visit $11, floor per one-off run $35, market reference $45 to $65, weekdays per month 21.
- REQ-70 [always] Settings shall show travel with these defaults: San Francisco 18 mph, East Bay 22 mph, between SF and the East Bay 30 mph, bridge 8 minutes, road factor 1.3.
- REQ-71 [always] Settings shall show "Minutes per new stop" with default 4.
- REQ-72 [always] Settings shall show the "Auto-send quotes within my rules" toggle, on by default.
- REQ-73 [always] Settings shall show the demo date (read-only) and the demo clock (editable, default 10:00am).
- REQ-74 [always] Settings shall show real texting status "Off", the channel (SMS or WhatsApp sandbox), and an editable list of team numbers, empty by default.
- REQ-75 [always] Settings shall show the business type "Courier".
- REQ-76 [always] Settings shall show connection status rows for "Our model", "Backup AI (Emergent universal key)", "OpenStreetMap data" and "Real texting", each labeled either green "connected" or grey "using fallback".
- REQ-77 [always] In Phase 1 the "Our model" row shall read "Not set up yet" with grey "using fallback", because the model address fields arrive in Phase 4 (interpreted).
- REQ-78 [event] When the owner saves Settings, the system shall store the values and show "Saved".
- REQ-79 [unwanted] If a Settings value is blank, negative or not a number, then the system shall show an inline message next to that field and not save.
- REQ-80 [event] When the owner changes the wage or cost per mile, the system shall update cost per stop everywhere it shows.
- REQ-81 [always] Settings shall show demo controls "Reset demo data", "Refresh from OpenStreetMap", "Send request 1 from the customer phone" and "Customer taps Accept".
- REQ-82 [always] Until their phase is built, "Refresh from OpenStreetMap", "Send request 1 from the customer phone" and "Customer taps Accept" shall be disabled with the hint "Available in a later step" (interpreted).
- REQ-83 [event] When the owner presses "Reset demo data", the system shall ask for confirmation with "Reset all demo data? This can't be undone."
- REQ-84 [event] When the owner confirms the reset, the system shall replace all Bayline Courier data with a fresh seed, restore every Settings default except the team numbers, and show "Demo data reset".
- REQ-85 [unwanted] If the reset fails partway, then the system shall leave a complete dataset (the old one or the new one) and show "Reset didn't finish. Try again."
- REQ-86 [always] A reset shall keep geo_cache and place_cache.

### Platform
- REQ-87 [always] All data shall persist across page refreshes and backend restarts.
- REQ-88 [unwanted] If the backend can't be reached, then the system shall show a friendly "Can't reach Drivepast right now. Try again in a moment." message, never raw errors or JSON.
- REQ-89 [always] The backend shall serve its API contract at /api/openapi.json.
- REQ-90 [always] The backend shall use only plain Python math (no pandas, numpy, OR-Tools, ML or plotting libraries, Playwright, Selenium, Celery, Redis, websockets or background workers).
- REQ-91 [always] Times shall show in Pacific time in the form "1:50pm".

## Quality requirements

```
Q-1  Tag: Perf.FirstLoad
     Scale: seconds from opening the preview URL to the left rail showing 6 vans with status lines
     Meter: headless browser, 3 cold loads, median
     Must: 3
     Plan: 1.5
```
```
Q-2  Tag: Perf.RouteTiming
     Scale: ms to recompute weekday route plans for all 6 vans on the backend
     Meter: timed backend call after a speed change, 5 trials, max
     Must: 500
     Plan: 100
```
```
Q-3  Tag: Perf.Reset
     Scale: seconds from confirming Reset demo data to "Demo data reset"
     Meter: headless browser, 3 trials, max
     Must: 10
     Plan: 4
```
```
Q-4  Tag: Trust.SeedTiming (breaks demo trust if wrong)
     Scale: minutes off target for Van 2's Shattuck/51st arrival (1:50pm) and Telegraph/Ashby arrival (2:15pm)
     Meter: read Van 2 route plan via API, 1 trial after fresh reset
     Must: 10
     Plan: 5
```
```
Q-5  Tag: Trust.SeedSpare
     Scale: count of vans whose spare minutes fall outside 30 to 70 (Van 2 outside 40 to 60)
     Meter: route plans via API after fresh reset
     Must: 0
     Plan: 0
```
```
Q-6  Tag: Trust.NumberConsistency
     Scale: count of mismatches in stops or spare minutes between left rail, unit header and Dispatch table across 6 vans
     Meter: headless browser read of all three, 1 trial
     Must: 0
     Plan: 0
```
```
Q-7  Tag: Data.Persistence (it lost my stuff)
     Scale: % of saved Settings changes and chat turns still present after page refresh
     Meter: headless browser, change 3 settings + send 2 chat messages, refresh, compare
     Must: 100
     Plan: 100
```
```
Q-8  Tag: Usability.FindSpare (I can't figure it out)
     Scale: seconds for a first-time non-technical user to say which van has the most spare minutes
     Meter: human
     Must: 30 (estimate)
     Plan: 10 (estimate)
```
```
Q-9  Tag: Device.Mobile (it broke on my device)
     Scale: count of horizontal-scroll or clipped-content issues at 390x844 across List, Chat and Page tabs
     Meter: headless browser at 390x844, each tab, Dispatch and Van 2
     Must: 0
     Plan: 0
```
```
Q-10 Tag: Trust.NoRawErrors
     Scale: count of raw JSON, stack traces or "undefined"/"NaN" strings visible on any Phase 1 screen
     Meter: headless browser walk of every Phase 1 screen, plus backend stopped once
     Must: 0
     Plan: 0
```
```
Q-11 Tag: Domain.Timezone
     Scale: count of times not shown in Pacific "h:mmam/pm" format, or a demo date not equal to today in America/Los_Angeles after reset
     Meter: headless browser + API, 1 trial after reset
     Must: 0
     Plan: 0
```
```
Q-12 Tag: Cosmetic.Calm (design direction D-1)
     Scale: reviewer judgment that the layout matches D-1 (light, near-black text, deep green accent, rounded soft-shadow cards, tabular numbers, distinct van colors)
     Meter: human, screenshots at 1440x900 and 390x844
     Must: matches on all six points
     Plan: looks like polished dispatch software
```
