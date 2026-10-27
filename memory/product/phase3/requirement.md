# Phase 3 requirements: the new look, plus maps

**Version:** phase-3

**Goal:**
- Restyle the whole app once in the feel of phenomenonstudio.com (overview D-18). Every later screen is built in that style.
- Add light, fast Leaflet maps to the unit page and the Dispatch page.
- Nothing that worked before changes behavior.

Read first: `/app/memory/product/overview.md` (D-18 especially) and `/app/memory/product/spec_part_a.md` section 10 (map items).

**What Phases 1 and 2 delivered:**
- The three-pane layout and phone tabs
- The echo chat
- Unit page (header, timeline with New and Starts tags, stats)
- Dispatch table
- Settings, with the Engine test tab
- The engine API, including accept and undo

**Out of scope:** prospect pins (Phase 7), AI, Inbox screens, phones, any change to copy or behavior.

## Functional requirements

### Design pass
- REQ-154 [always] The app shall use one shared set of design tokens (color, type scale, spacing, radius, shadow, motion) modeled on Phenomenon Studio's Haulix logistics dashboard (reference image `/app/memory/product/design_refs/haulix_ref.png`, overview D-18).
- REQ-155 [always] The app shall not use Haulix's or Phenomenon Studio's logo, illustrations, compass, gauges or copy.
- REQ-155a [always] The Dispatch and unit pages shall show a row of pill stat chips whose values come only from the engine (Dispatch: vans, stops today, total spare minutes, on-time rate; unit page: stops, spare minutes, cost per stop, on-time rate) (interpreted).
- REQ-155b [always] Maps shall use standard OpenStreetMap tiles with a dark CSS treatment on the tile layer only, so route lines and markers keep their true colors (interpreted).
- REQ-156 [always] Every existing screen shall use the new tokens: left rail, chat, unit page, Dispatch page, Settings (including Engine test), Inbox and Phones placeholders, the phone tabs, and the friendly error message.
- REQ-157 [always] Each van shall keep a distinct route color, used the same way in the rail dot, timeline and map.
- REQ-158 [always] Amber shall mean a problem and red shall mean only "can't do it".
- REQ-159 [always] All prices, times and counts shall use tabular numbers.
- REQ-160 [always] Body text shall meet a 4.5:1 contrast ratio against its background.
- REQ-161 [always] UI motion shall follow phenomenonstudio.com's full character (reveals, transitions, hover states), but prices, times and counts shall be readable within 400 ms of a screen opening, and no animation shall block a click (user: "the entire feeling", interpreted).
- REQ-162 [always] Where the browser asks for reduced motion, the app shall turn decorative motion off.
- REQ-163 [always] The design pass shall not change any on-screen copy, control, data-testid or behavior that a Phase 1 or Phase 2 journey checks.

### Maps (Leaflet + OpenStreetMap tiles)
- REQ-164 [always] The unit page shall show a map above or beside the timeline with standard OpenStreetMap tiles and the attribution "© OpenStreetMap contributors".
- REQ-165 [always] The unit map shall draw today's route as straight lines in the unit's color, from its start location through every stop in order and back to its end location.
- REQ-166 [always] The unit map shall show a numbered marker for each stop matching its timeline position.
- REQ-167 [always] The unit map shall show the start/end location (the depot or the SoMa lot) with its own marker (interpreted).
- REQ-168 [event] When the owner clicks a stop marker, the map shall show the customer name, address, arrival time and window.
- REQ-169 [always] Stops booked from a job shall show as "New" on the map, styled to match the timeline tag.
- REQ-170 [event] When the unit page opens, the map shall fit to that unit's route.
- REQ-171 [always] The Dispatch page shall show a fleet map with every unit's route in its color plus a legend naming each van.
- REQ-172 [event] When the owner clicks a van in the fleet map legend, the system shall open that van's page (interpreted).
- REQ-173 [always] Each Engine test result shall have a "Show on map" link for its winning van (or its shifted-window van) (interpreted).
- REQ-174 [event] When the owner presses "Show on map", the system shall open that van's page with the job's new stops as distinct "new request" pins and the proposed insertion drawn as a dashed line (interpreted).
- REQ-175 [always] "Show on map" shall not change any route.
- REQ-176 [event] When a unit's route changes (accept, undo, speed change), its maps shall show the new route the next time they load or refresh.
- REQ-177 [unwanted] If map tiles fail to load, then the map shall still draw route lines and markers on a plain background and show "Map tiles couldn't load. Routes are still shown."
- REQ-178 [always] The desktop map shall not zoom on page scroll until the owner clicks into it (interpreted).
- REQ-179 [always] On phones, the map shall fill the Page tab width and support pinch zoom without trapping page scroll.
- REQ-180 [always] Maps shall use Leaflet (plain or react-leaflet) only, with no other mapping library, API key or Google service.

## Quality requirements

```
Q-22 Tag: Perf.MapLoad
     Scale: seconds from opening a unit page to route line and markers drawn
     Meter: headless browser, Van 2 and Dispatch, 3 loads each, max
     Must: 2
     Plan: 1
```
```
Q-23 Tag: Regression.Journeys (it's broken)
     Scale: count of Phase 1 and Phase 2 journeys failing after the design pass
     Meter: rerun existing suites
     Must: 0
     Plan: 0
```
```
Q-24 Tag: Cosmetic.Feel
     Scale: reviewer judgment that the app recognizably shares phenomenonstudio.com's typography, spacing and mood while staying readable dispatch software
     Meter: human, screenshots at 1440x900 and 390x844 next to the reference site
     Must: a clear family resemblance on type and spacing, with no element unreadable
     Plan: looks like a studio-built product
```
```
Q-25 Tag: Cosmetic.Contrast
     Scale: count of text elements under 4.5:1 contrast
     Meter: automated contrast check on rail, chat, unit page, Dispatch, Settings
     Must: 0
     Plan: 0
```
```
Q-26 Tag: Device.MobileMap
     Scale: count of horizontal-scroll, clipped or scroll-trap issues on Page tab with map at 390x844
     Meter: headless browser
     Must: 0
     Plan: 0
```
```
Q-27 Tag: Trust.MapMatchesTimeline
     Scale: count of markers whose number or position doesn't match the timeline order
     Meter: headless browser, all 6 vans
     Must: 0
     Plan: 0
```
