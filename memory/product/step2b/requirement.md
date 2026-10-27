# Step 2b requirements: Haulix fidelity pass (user feedback after step 1)

**Version:** step-2b

**Goal:** The user says the UI and animation don't yet fully use the Haulix exemplar (`/app/memory/product/design_refs/haulix_ref.png`, Dribbble shot 27229691). Bring the look and motion much closer to it while keeping our three panes, our copy and the rule that every number comes from the engine. This runs before the first deploy so the deployed app shows it.

## Functional requirements
- REQ-291 [always] The builder shall study the full Dribbble shot, including every attachment and any video, using its browser tools, and extract still frames from any video to study the motion (interpreted).
- REQ-292 [unwanted] If Dribbble blocks access, then the builder shall work from the saved image and report that more frames would help.
- REQ-293 [always] The app shall sit in floating rounded panels with gaps on a near-black backdrop, like the exemplar's framed dashboard.
- REQ-294 [always] The van and Fleet pages shall make the map the hero: at least 60% of the viewport height, rounded, with stacked round map controls on the right (list, zoom in, zoom out, reset, fullscreen, layers).
- REQ-295 [always] The van page map shall carry a floating detail card in the top-left corner (interpreted). The card shows:
  - the van's name and a status pill
  - "Stop N of M" and its next stop with time
  - an amber-to-yellow striped progress bar of the day at the demo clock
  - the return time
- REQ-296 [always] The detail card shall show two gauge tiles built only from engine numbers: a "Day used" dial (route minutes against shift minutes) and a "Spare minutes" fill tile (interpreted).
- REQ-297 [always] The detail card shall end with an amber insight banner drawn from real stats, like "Late most often after 2pm: 80% on time", or no banner when there's nothing to flag (interpreted).
- REQ-298 [always] Each van shall show on the map as our own top-down van icon at its demo-clock position, interpolated along its route and pointed along its heading. The selected van gets a soft lime glow halo.
- REQ-299 [event] When a van is selected (rail, legend or map), the system shall draw its route in lime and dim the other vans' routes.
- REQ-300 [always] A top bar shall hold the stat chips, a search box "Search vans, stops or requests…" that jumps to the match, a bell with the count of new Inbox items, and the owner's avatar with "Rosa Delgado · Owner" (interpreted).
- REQ-301 [always] Page titles shall follow the exemplar: a big white title, a grey subline, and a right-side pill selector "Today" / "This week" that switches the spare-minutes figures (interpreted).
- REQ-302 [always] Above the Fleet map there shall be segmented filter pills with count badges (for example "All 6", "Most spare 2", "Late risk 1", "New stops 0"), plus lime toggles "Show routes" and "Show van icons" (interpreted).
- REQ-303 [always] Motion shall follow the exemplar:
  - a route draw-on when a map opens
  - card slide-up and fade
  - a gauge sweep and a fill wave
  - a halo pulse
  - a sliding highlight on segmented pills and springy toggle knobs
  - hover lifts
- REQ-304 [always] Numbers shall be readable within 400 ms of a screen opening. No animation shall block a click. Reduced motion shall turn decorative motion off.
- REQ-305 [always] The pass shall not copy the exemplar's logo, truck art, compass or any invented telemetry such as speed or fuel.
- REQ-306 [always] Every gauge, bar and figure shall come from the engine.
- REQ-307 [always] The pass shall keep every copy string, control and data-testid that earlier journeys check, and keep the chat in the center pane.

## Quality requirements
```
Q-45 Tag: Cosmetic.ExemplarFidelity
     Scale: count of the exemplar elements in REQ-293 to REQ-303 that are missing or clearly off
     Meter: human, side-by-side with haulix_ref.png at 1440x900
     Must: 2
     Plan: 0
```
```
Q-46 Tag: Perf.MapWithMotion
     Scale: seconds to route line and van icons drawn on Van 2 with animations on
     Meter: headless browser, 3 loads, max
     Must: 2
     Plan: 1.2
```
