# Journeys: landing2

superseded: the ui-3d landing journeys that assert the dark MapLibre opening at "/" (lime accent, dark map hero). Any journey asserting the lime accent or charcoal background in the app is superseded by the restyle (JRN-170).

- JRN-156 steps: open "/" on desktop. expected: a paper loader shows "Building the Bay Area from real streets." with rows Street segments 10,526, Buildings 56,364, Vans 6, Stops today 30; values show "..." until loaded; loader slides up; hero shows the three headline lines "Price every job" / "from the van that" / "already drives past.".
- JRN-157 steps: let the page load. expected: the white city model fills the whole window (no table-colored empty areas) with water, roads, buildings and shadows; masthead shows "Drivepast", 5 chapter buttons, Motion switch, Play/Pause, "Price a job"; timeline bar shows "Bayline time" and a clock.
- JRN-158 steps: wait without touching. expected: within ~4 s of the loader leaving the page starts scrolling by itself through all five chapters and stops at the end; the masthead button reads Pause while playing and Replay at the end.
- JRN-159 steps: during autoplay, scroll the mouse wheel. expected: autoplay stops; the button reads Play.
- JRN-160 steps: click "04 Price" (or scroll to P 4.6). expected: clock reads "1:45 PM"; Van 2 is at the customer door; the green sign shows "VAN 2 PASSES", "1:45 PM", "Our van already passes your door at 1:45pm.", "$11 a visit", "USUALLY $14"; panel 04 rows show $1.28, $0.46, $3.48, $11.00, "$11 a visit".
- JRN-161 steps: change Settings floor per recurring visit, reload "/", go to chapter 04. expected: panel and sign numbers follow the engine with the new Settings (then restore defaults).
- JRN-162 steps: scroll to chapter 02. expected: customer building turns orange, a pin rises above it, the "NEW REQUEST" tag shows Pickup "Daily, Mon to Fri" and Window "1:00 to 3:00pm"; the timeline window band appears.
- JRN-163 steps: scroll to chapter 03. expected: routes rise into ribbons, the ring column stands at the door, and "VAN 2 PASSES 1:45 PM" label shows; place labels are hidden.
- JRN-164 steps: scroll down slowly then back up through all chapters. expected: no console errors; clock only increases while scrolling down; no blank/black canvas.
- JRN-165 steps: click "Price a job" in the masthead, hero and panel 05. expected: each opens the Inbox (through the existing sign-in / "Open the demo" screen if not signed in).
- JRN-166 steps: open "/" at 390x844. expected: chapter buttons, masthead label and Motion switch hidden; panels are bottom sheets without rows; sign docks under the masthead; map fills the screen.
- JRN-167 steps: open "/" with prefers-reduced-motion, or toggle Motion off and reload. expected: no autoplay, buildings at full height, hero clock "1:10 PM"; scrolling still changes chapters and the clock; Motion choice survives reload.
- JRN-168 steps: open "/" with WebGL disabled. expected: the note "The 3D view couldn't start on this device, so here's the story without it." shows, then plain text with the hero and all five panels and the timeline at 1:45 PM.
- JRN-169 steps: open "/about". expected: the six credit lines of PROMPT.md section 8, no Kenney or React Three Fiber lines.
- JRN-170 steps: open the app (/dispatch, a van page, Inbox, Settings). expected: background #ECEAE4, paper panels with ink borders, square corners, Overpass fonts (no IBM Plex), no lime accent, no charcoal background, light positron 2D maps; all existing flows still work.
