# UI-3D requirements: 3D city map and realistic look (user request, Oct 2026)

**Version:** ui-3d

**Goal:** The user says the app still lacks the exemplar's 3D feel and real-city feel, and doesn't look real enough. The exemplar is `/app/memory/product/design_refs/haulix_ref.png`, with more shots in `/app/memory/product/step2b/refs/`. The current look is in `/app/memory/product/design_refs/screens/routes_van1_1440.jpeg`. Make the maps look like a real, dense dark city seen at a 3D tilt, with realistic 3D vans and depth on the panels. Keep every function, number and testid. Product context: `/app/memory/product/overview.md`. This step runs before the user's list of functional fixes.

What's wrong now (from the screenshots): the map is a flat raster tile zoomed out to show terrain and parks, not a city grid. There are no buildings and no tilt. The vans are small flat icons. The panels look flat.

## Functional requirements
- REQ-420 [always] The van and Fleet maps shall use MapLibre GL with free OpenFreeMap vector tiles (`https://tiles.openfreemap.org/planet`), with no API key (interpreted).
- REQ-421 [always] The map shall use a custom near-black style in the exemplar's palette: charcoal blocks, grey street casings, faint labels and no bright parks or water (interpreted).
- REQ-422 [always] The map shall show buildings as 3D extruded blocks with their real heights, in dark grey with soft lighting (interpreted).
- REQ-423 [always] The map shall open tilted at about 50 degrees, at a street-level zoom where the city block grid fills the view (interpreted).
- REQ-424 [event] When a van page opens, the camera shall fly in a smooth tilted move to fit that van's route (interpreted).
- REQ-425 [event] When the user drags with the right mouse button or two fingers, the map shall rotate and tilt (interpreted).
- REQ-426 [event] When the user presses the map's reset control, the map shall return to the default tilted view of the route.
- REQ-427 [always] Routes shall keep the real street lines from step 3a, drawn over the 3D city: lime with a soft glow for the selected van and dimmed for the others.
- REQ-428 [always] Each van shall be a realistic 3D-rendered top-down van image with a soft shadow, at its demo-clock position and pointed along its heading. The image is generated for this app, not the exemplar's truck art.
- REQ-429 [always] The selected van shall keep its pulsing lime halo, drawn on the ground under the van.
- REQ-430 [always] Stop number markers shall stay readable on top of the buildings, keeping their numbers and their order.
- REQ-431 [always] The floating detail card, gauges, map controls, filter pills and toggles from step 2b shall stay in place and keep working on the new map.
- REQ-432 [always] Panels shall gain depth through a subtle top highlight edge, inner shadow, soft drop shadow and a faint grain on the backdrop, matching the exemplar (interpreted).
- REQ-433 [always] Gauges shall look more real, with tick marks, a glossy dial and a gradient arc, like the exemplar's speed and fuel tiles. They still show only engine numbers.
- REQ-434 [always] The map shall carry a bottom strip with the copy "Drag to pan · Right-drag to tilt · Scroll to zoom" on the left (interpreted).
- REQ-435 [unwanted] If the device can't run WebGL, then the system shall fall back to the existing flat Leaflet map with no error.
- REQ-436 [unwanted] If the vector tiles fail to load, then the system shall show the routes and vans on the plain dark backdrop with the note "Map tiles unavailable".
- REQ-437 [state] While reduced motion is on, the system shall skip the camera fly-in and the halo pulse.
- REQ-438 [always] The pass shall keep every copy string, control, data-testid, the chat in the center pane, the "Open the demo" entry and the Google sign-in.
- REQ-439 [always] The pass shall not copy the exemplar's logo, compass, truck art, or any invented telemetry such as speed or fuel.
- REQ-440 [always] The pass shall not change the pricing engine, routes, the Gmail flow or any API contract.

## Quality requirements
```
Q-420 Tag: Cosmetic.RealCityFeel
      Scale: count of these that are missing or clearly off next to haulix_ref.png at 1440x900: dense block grid, 3D buildings, tilt, realistic vans, glow route, panel depth
      Meter: human, side by side
      Must: 1
      Plan: 0
```
```
Q-421 Tag: Perf.MapFirstDraw
      Scale: seconds from opening Van 2 to buildings, route and vans drawn
      Meter: headless browser, 3 loads, max
      Must: 3
      Plan: 1.5
```
```
Q-422 Tag: Device.MobileMap
      Scale: frames per second while panning the map on a 390px phone view
      Meter: human on a phone
      Must: 30
      Plan: 55
```
```
Q-423 Tag: Cosmetic.VanArt
      Scale: vans that look stretched, blurry, pixelated or have a visible box behind them at default zoom
      Meter: human, screenshot at 1440 and 390
      Must: 0
      Plan: 0
```

## Revision 1 (user feedback after the first pass)
- REQ-441 [event] When a van page opens, the camera shall fly to a close-up street-level view (zoom about 16.5, tilt about 55) centered on that van, so the buildings read at real scale like the exemplar.
- REQ-442 [state] While a van page is open and the user hasn't panned, the camera shall follow the van's demo-clock position and heading (interpreted).
- REQ-443 [event] When the user scrolls or pinches out, the system shall allow zooming out to see the whole route. The reset control returns to the close-up follow view.
- REQ-444 [always] The Fleet page shall keep the flat overview as it is.
- REQ-445 [always] On a phone (width under 768px), the van detail card shall start collapsed to one slim row: van name, status pill, "Stop N of M" and spare minutes.
- REQ-446 [event] When the user taps the collapsed card, the system shall expand it to the full card. Tapping again collapses it.
- REQ-447 [always] Vans shall look like real vehicles at map scale: slim, sized to a real van's footprint (about 5 m by 2 m) relative to the streets, top-down and photoreal, with a subtle contact shadow (interpreted).
- REQ-448 [always] Vans shall never cover a stop number marker or the route line ahead in a way that hides it. Stop markers sit above vans (interpreted).
- REQ-449 [always] On the Fleet overview, vans shall show as small, low-profile markers (a slim van silhouette or dot with a heading arrow, about 14 to 18 px), not large images (interpreted).
