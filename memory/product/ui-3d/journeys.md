# UI-3D journeys

Fresh Reset, clock 10:00am, via "Open the demo". Earlier journeys stay valid. Map tests use the real browser at 1440x900 unless a size is given.

- **JRN-140** 3D city on a van page (interpreted)
  - steps: Open Van 2.
  - expected: The map is tilted, with dark 3D buildings standing along the streets and a dense block grid filling the view, not a zoomed-out flat map with parks and terrain. The lime route follows the streets over the city, and the camera glides into place.

- **JRN-141** Realistic vans
  - steps: Open the Fleet map, then Van 1.
  - expected: Each van is a realistic 3D-looking top-down van with a shadow, pointed along its route, with no box or background around it. The selected van has a pulsing lime halo on the ground.

- **JRN-142** Rotate, tilt and reset
  - steps: On Van 1's map, right-drag to rotate and tilt, zoom in with the + button, then press reset.
  - expected: The view rotates and tilts while dragging. Reset returns to the default tilted view that fits the whole route.

- **JRN-143** Selection still works
  - steps: On the Fleet map, pick Van 3 from the legend, then from the left rail.
  - expected: Van 3's route turns lime and glows, and the other routes dim.

- **JRN-144** Stop markers readable
  - steps: Open Van 1 and count the numbered markers.
  - expected: All 20 numbered markers show on top of the buildings, in the same order as the timeline.

- **JRN-145** Card and controls intact
  - steps: Open Van 2. Read the detail card, switch Today/This week, and toggle "Show routes" and "Show van icons" on Fleet.
  - expected: The card shows the same engine numbers as before, now with tick-marked glossy gauges. The toggles hide and show the routes and vans on the 3D map.

- **JRN-146** Panel depth
  - steps: Look at the app at 1440x900 next to the exemplar.
  - expected: The panels have a soft highlight edge and shadow on a grained near-black backdrop. They read as floating, not flat.

- **JRN-147** Phone view
  - steps: Open Van 2 at 390x844.
  - expected: The 3D map fits the screen, pans smoothly and shows the vans and route. No overlap hides the detail card's numbers.

- **JRN-148** Tiles down
  - steps: Block tiles.openfreemap.org and open Van 2.
  - expected: The route and vans draw on a plain dark backdrop with the note "Map tiles unavailable". No error.

- **JRN-149** Reduced motion
  - steps: Turn on reduced motion and open Van 2.
  - expected: The map appears straight in its tilted view with no fly-in and no halo pulse.

- **JRN-150** Earlier flows still work
  - steps: Run Optimize route (JRN-104), Flow A (JRN-81) and the Inbox Gmail bar view.
  - expected: Same results as before this pass.

## Revision 1
superseded: [JRN-140 "fits the whole route" opening view is replaced by JRN-151]

- **JRN-151** Close-up follow view
  - steps: Open Van 2.
  - expected: The camera glides to a tilted street-level close-up on Van 2's van, with buildings at real scale filling the view. It stays on the van as the demo clock moves, until the user pans.
- **JRN-152** Zoom out and reset
  - steps: On Van 2, scroll out, then press reset.
  - expected: Scrolling out shows the whole route. Reset returns to the close-up on the van.
- **JRN-153** Collapsed card on phone
  - steps: Open Van 2 at 390x844, then tap the card twice.
  - expected: The card starts as one slim row with the name, status, "Stop 8 of 20" and spare minutes, and most of the map is visible. The first tap expands it to the full card with gauges. The second tap collapses it.
- **JRN-154** Vans look real and don't block
  - steps: Look at Van 1 close-up, then the Fleet overview.
  - expected: Close-up: the van is a slim, real-looking van about the width of a lane, not bulky, and no stop number or route is hidden under it. Fleet: vans are small, low markers that don't cover stop numbers.
- **JRN-155** Fleet unchanged
  - steps: Open the Fleet page.
  - expected: Same flat overview as before, with all routes and the legend.
