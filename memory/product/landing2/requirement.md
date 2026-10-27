# Phase: landing2 — DESIGN UPDATE 2 white-model scroll story (+ app restyle)

Goal: replace the current MapLibre landing at "/" with the deck.gl white-model scroll story, then carry the light look into the app.

Source of truth (read both, in full): `/app/memory/product/design2/PROMPT.md` and `/app/memory/product/design2/FIXES.md` (FIXES wins where they differ). This doc only adds the bar; it doesn't restate every value.

Version: landing2-1

## Functional requirements
- REQ-450 [always] The system shall serve the landing story at the root URL "/", replacing the existing MapLibre landing.
- REQ-451 [always] The system shall load deck.gl 9.0.38 by dynamic import on the landing page only, using the Deck class on our own canvas.
- REQ-452 [always] The system shall load the data files from /drivepast/<name>.json in the order meta, fleet, water, surroundings, roads, buildings-core, shadows-core.
- REQ-453 [always] The system shall decode sample.json to the values in its "expected" block (first building point (-122.42339, 37.82668), door (-122.28122, 37.83576), Van 2 street point (-122.28142, 37.83562)).
- REQ-454 [always] The system shall render the masthead, timeline bar, six sections and five route-sheet panels with the copy word for word from PROMPT.md section 3.
- REQ-455 [always] The system shall show the loader with counts 10,526 / 56,364 / 6 / 30 from meta.json until the first view is ready.
- REQ-456 [always] The system shall draw the ground, water, far roads, roads, shadows, ghosts, stops and detour with depthCompare 'always' and depthWriteEnabled false.
- REQ-457 [always] The system shall drive the camera from scroll progress P through the six keyframes (FIXES values for 0, 1, 5).
- REQ-458 [always] The system shall drive the story clock from P per PROMPT.md 5.4, showing it on the timeline bar like "1:45 PM".
- REQ-459 [state] While P is between 4.35 and 4.85, the system shall hold the clock at 1:45 PM with Van 2 at the door.
- REQ-460 [always] The system shall take every number in panel 04 and on the offer sign from the pricing engine for a recurring visit adding 4 minutes and 0.6 miles under current Settings. (Builder may add a small read-only backend endpoint for this.) (interpreted)
- REQ-461 [state] While lift is above 0, the system shall draw the time view with the ribbons, window column, "VAN 2 PASSES 1:45 PM" label, hour labels and now dots.
- REQ-462 [state] While P is between 1.72 and 2.6, the system shall show the "NEW REQUEST" tag pinned above the customer pin.
- REQ-463 [state] While P is between 4.28 and 5.06, the system shall show the green offer sign with role="status".
- REQ-464 [event] When 3.4 seconds pass after the loader leaves with no input, the system shall autoplay the story by scrolling the window.
- REQ-465 [event] When the user wheels, touches, presses a pointer or a scroll key during autoplay, the system shall stop autoplay.
- REQ-466 [event] When a chapter button is clicked, the system shall glide to P 1, 2, 3, 4.5 or 5.6.
- REQ-467 [event] When "Price a job" is clicked, the system shall open the Inbox (/inbox, behind the existing sign-in / demo gate).
- REQ-468 [state] While reduced motion is requested or Motion is off, the system shall move nothing by itself.
- REQ-469 [event] When the Motion switch is toggled, the system shall remember the choice in localStorage.
- REQ-470 [unwanted] If WebGL is missing, a file fails, or the first view isn't ready in 12 seconds, then the system shall show the error note for 4 seconds, then the plain-text fallback with all five panels.
- REQ-471 [state] While the viewport is a phone (width < 640 or w/h < 0.85), the system shall use phone keyframes, bottom-sheet panels and core files only.
- REQ-472 [always] The system shall list the six credit lines of PROMPT.md section 8 on the "About and credits" page, without the Kenney and React Three Fiber lines.
- REQ-473 [always] The system shall use no gradients, glows, blur, pill chips or IBM Plex on the landing.
- REQ-474 [event] When the landing is done, the system shall apply the section 7 light restyle to the app without moving, renaming or removing anything, within about 150 credits.
- REQ-475 [unwanted] If the restyle would exceed about 150 credits, then the system shall stop and report before continuing.

## Quality requirements
Q-450 Tag: Landing.LoadSpeed
      Scale: seconds from navigation to loader visible / city risen
      Meter: Playwright on preview, desktop 1440x900, 3 trials
      Must: loader < 1.5 s, city risen < 8 s
      Plan: loader < 1 s, city risen < 6 s
Q-451 Tag: Landing.Framing
      Scale: chapters with empty background, or customer building/pin/tag/sign off screen or covering a panel
      Meter: screenshots at 1440x900, 1280x720, 1920x1080, 390x844 at P 0..5.6
      Must: 0
      Plan: 0
Q-452 Tag: Landing.Smoothness
      Scale: visible stutter, ground flicker, camera jumps while scrolling up and down
      Meter: human (Chrome laptop)
      Must: none seen
      Plan: none seen
Q-453 Tag: Landing.PriceTruth
      Scale: mismatches between sign/panel numbers and the engine
      Meter: compare with engine result for 4 min / 0.6 mi under default Settings
      Must: 0 ($11 a visit, usually $14, $1.28, $0.46, $3.48, $11.00)
      Plan: 0
Q-454 Tag: App.RestyleSafety
      Scale: broken flows after restyle (inbox, options, send/accept/undo, chat, settings)
      Meter: e2e regression
      Must: 0
      Plan: 0
