DESIGN UPDATE 2. A white-model opening story and a light look for Drivepast.

This replaces the DESIGN UPDATE I sent earlier (the dark MapLibre opening with the lime accent) and section 3.13 of the plan. If you've built any of that opening, remove it. Don't change any data, pricing logic, flows, or the Gmail and sign-in work.

The attached zip, drivepast-opening-kit.zip, holds data files only (the city model and the demo routes) plus this message. There's no code in it, so write all the code yourself.

## 0. The files

Unzip it and copy everything in data/ to frontend/public/drivepast/, so each file is served at /drivepast/<name>.json. The big files are large, so don't open, print or edit them. Use sample.json to test your decoder.

| File | Size | What it holds |
|---|---|---|
| meta.json | 1 KB | Origin and scale, the model base, the sun, the customer building, Van 2's street point, depots, place labels, van names and the loader counts |
| fleet.json | 0.4 MB | The six demo vans' routes, with a time for every point |
| buildings-core.json | 1.0 MB | Buildings within 2.5 km of the customer, plus every big or tall building |
| buildings-rest.json | 1.5 MB | All other buildings |
| shadows-core.json | 0.7 MB | Merged sun shadows within 2.5 km of the customer, plus every big one |
| shadows-rest.json | 0.8 MB | All other shadows |
| roads.json | 0.3 MB | Streets, highways and rail |
| water.json | 0.02 MB | The bay and other water |
| sample.json | 5 KB | Small slices of the files, with the values a correct decoder returns |

How the data is stored
- Every coordinate is an integer pair (x, y). Longitude is o[0] + x / s and latitude is o[1] + y / s, where o = [-122.43, 37.755] and s = 100000 (both in meta.json).
- A ring is a flat list of integers [x0, y0, x1, y1, ...]. In the buildings, shadows, roads and water files, and in meta.customerBuilding.ring, rings are delta-encoded. The first pair is absolute, and each later pair is the change from the point before, so decode with running sums. Rings aren't closed, so the first point isn't repeated at the end.
- Everything else is absolute. That covers fleet.json paths and stops, meta.slab, meta.customerBuilding.center and door, meta.customer.street and meta.depots.
- Each buildings file is a list of [height in meters, minimum height in meters, ring]. Ignore the minimum height.
- Each shadows file is a list of polygons. A polygon is a list of rings, where the first ring is the outline and any others are holes.
- roads.json is a list of [class, ring], where the ring is an open line. Class 0 is motorway or trunk, 1 is primary, 2 is secondary or tertiary, 3 is a minor street and 4 is rail.
- water.json is a list of rings.
- fleet.json is {"vans": [{"id", "loop", "path", "ts", "stops"}]}. The path is a flat absolute list with one point for each entry in ts. ts is minutes after 12:00 noon, negative before noon. stops is a list of [x, y] pairs. loop is how many minutes one lap of the route takes, since each route repeats through the day.
- In meta.json, slab is [x0, y0, x1, y1], the corners of the model base. customerBuilding is {h, ring, center, door}. customer is {street, passTime, window}, where street is the point on Van 2's route closest to the door, Van 2 passes it at 105 minutes (1:45pm), and the pickup window runs from 60 to 180 minutes (1:00 to 3:00pm). sun gives the light direction, vans gives the names and nicknames, places gives the map labels, and counts gives the loader numbers.
- The customer building isn't in the buildings files, so draw it on its own.

Decoder check. Decode sample.json first and confirm you get the values in its "expected" block. For example, the first building's first point is (-122.42339, 37.82668), the customer's door is (-122.28122, 37.83576), and Van 2's street point is (-122.28142, 37.83562).

## 1. What it is

The landing page is a short film people scroll through. It shows a white architectural model of the East Bay and San Francisco, built from real streets and buildings and lit by the sun at 1:45pm. Six demo vans drive their afternoon routes. Scrolling follows Van 2 through five chapters, which cover the fleet, a new request, a view where every route is lifted into the time of day, the price at the customer's door, and sending the offer. It starts playing by itself a few seconds after it loads, and any scroll, tap or key press takes over.

## 2. Look

Colors

| Name | Value | Use |
|---|---|---|
| Table | #D6D3CA | Page background behind the model |
| Paper | #F4F2EC | Panels, bars, the loader and secondary buttons |
| Ink | #141414 | Text, rules, borders and primary buttons |
| Body | #2B2A27 | Paragraph text |
| Muted | #5C5A54 | Labels and small print, which passes 4.5 to 1 on paper |
| Hairline | #CFCBC2 | Thin rules inside panels |
| Accent | #FF5B1F | Van 2, the customer and active states. Text on it is ink. Never use it for text on paper, because it fails contrast. |
| Sign green | #0E5A43 | The offer sign only, with white text |

3D colors, as RGB from 0 to 255

| Thing | Color |
|---|---|
| Model base | 232, 230, 223 |
| Buildings | 247, 246, 242 |
| Water | 194, 202, 205 |
| Roads, classes 0 to 4 | 178, 175, 168 / 190, 187, 180 / 199, 196, 190 / 208, 206, 201 / 186, 183, 176 |
| Shadows | 70, 62, 50 at alpha 41 |
| Other vans' trails and route ghosts | 30, 30, 30 |
| Other vans' dots and 3D bodies | 44, 44, 44 |

Type
- Overpass (weights 400, 600, 700 and 800) is for text and headlines. Overpass Mono (400, 500 and 600) is for labels, times, prices and miles. Install @fontsource/overpass and @fontsource/overpass-mono so they're served from our app. Wait for both to load, or 2.5 seconds, before creating the 3D text labels.
- Labels are Overpass Mono at 11 to 12px, uppercase, with 0.08 to 0.12em letter spacing.

Shapes
- Corners are square everywhere except the offer sign. Panels and bars have 1px ink borders and no shadows.
- Buttons are plain rectangles 44 to 52px tall. Primary buttons are ink with paper text, and secondary buttons are paper with a 1px ink border and ink text.

Don't use any gradient (including a fade over the map), glow, blur, glass, card shadow, pill-shaped chip, emoji, italic serif accent word or neon on black. Don't model anything on another company's site. In particular, there's no dotted world-map loader, news ticker, cloud-shaped transition or giant stat counter.

## 3. Page structure

The landing page lives at the root URL. A canvas is fixed behind everything at full window size. The window scrolls normally, and six sections scroll over the canvas. The masthead is fixed at the top and the timeline bar at the bottom. From back to front, the layers are the canvas, the sections, the pinned labels, the masthead and bar, the loader, and the error note.

3.1 Masthead. It's fixed at the top, 60px tall, paper, with a 1px ink line along the bottom and side padding of clamp(12px, 3.4vw, 52px).
- On the left is the mark, then "Drivepast" in Overpass 800 at 21px with -0.035em letter spacing. The mark is a 34 by 24 inline SVG. It's a 2.2px ink line along the path "M2 19 H11 C13.5 19 14 11.5 17 11.5 C20 11.5 20.5 19 23 19 H32" with square caps, and an accent dot of radius 3.4 at (17, 5) with a 1.4px ink outline. It reads as a route with a small detour to a door.
- In the middle, at 900px wide and up, are five chapter buttons the full height of the bar, "01 Fleet", "02 Request", "03 Time", "04 Price" and "05 Send", in Overpass Mono 12px uppercase with the number in weight 600. Under 1180px wide, show only the numbers plus the current chapter's name. The current chapter is ink with a 3px accent bar along its bottom edge and aria-current="step", and the others are muted. Clicking one glides to that chapter (5.7).
- On the right, at 1240px and up, is "Demo fleet, Bayline Courier" in muted mono 12px uppercase. Then come a "Motion on" or "Motion off" switch (a secondary button in mono 12px, hidden on phones), a Play, Pause or Replay button with its icon (secondary), and "Price a job" (primary), which opens the Inbox. On phones, Play shows as an icon only, with an aria-label.

3.2 Timeline bar. It's fixed at the bottom, 76px tall, paper, with a 1px ink line along the top and the same side padding.
- On the left, "Bayline time" in muted mono 11px uppercase sits over the live clock in Overpass Mono 600 at 24px with tabular numbers, for example "1:45 PM".
- The middle holds a ruler from 12:00 to 3:30pm and fills the remaining space. It has a 1px ink baseline, a tick every 15 minutes (hour ticks 15px tall, quarter ticks 8px) and the hour labels "12 PM", "1 PM", "2 PM" and "3 PM" under it, which are hidden on phones. The customer's 1:00 to 3:00pm window shows as a band with a 1px accent border and accent fill at 18% opacity, and it fades in from chapter 2. A 5 by 32px accent marker with a 1px ink outline sits at the current time and slides smoothly (120ms linear).
- On the right, except on phones, is the credit line in muted 11px, "Map data © OpenStreetMap contributors. Tiles OpenFreeMap © OpenMapTiles. Routes by OSRM. Shadows set for 1:45pm on Oct 24." On phones, one 10px line under the ruler reads "© OpenStreetMap contributors, OpenMapTiles, OSRM".
- Wheel and touch over either bar scroll the page too.

3.3 Sections. In order, they're 1, 1, 1, 1, 1.6 and 1 window heights tall. Use svh units so phones don't jump. Each section has 96px of padding on top and 100px at the bottom.

Section 0 is the hero. It's left-aligned and vertically centered, with a max width of 640px.
- The kicker is a 28 by 2px ink rule, then "For courier companies with 2 to 20 vans" in mono 12px, shown in uppercase.
- The headline (h1) is Overpass 800 at clamp(36px, 6.2vw, 102px), line height 0.92 and letter spacing -0.045em, in three lines, "Price every job", "from the van that" and "already drives past."
- The body reads "Drivepast checks each new stop against the routes your vans already run, then prices it from the real extra minutes and miles." It's 16 to 19px in the body color, with a max width of 30em.
- The buttons are "Price a job" with a small right arrow (primary, opens the Inbox) and "Play the afternoon" with a play triangle (secondary).
- A scroll cue sits at the bottom left, 104px up. It's a 1 by 40px hairline with an ink segment sliding down it every 2.2 seconds, next to "Scroll to follow Van 2" in mono 11px, shown in uppercase.

Sections 1 to 5 each hold one panel, which we call a route sheet. It's clamp(300px, 28vw, 410px) wide, paper, with a 1px ink border, and it sticks 96px from the top while its section is on screen (position sticky), then scrolls away. The chapter 2 panel sits on the right, and the others sit on the left.
- The header row starts with an ink box at least 46px wide holding the chapter number in paper mono 600, then the chapter name, then a muted tag at the right, all in mono 12px uppercase. A 1px ink line runs under the row.
- The body has 18px of padding on top and 20px on the sides and bottom. It starts with an h2 in Overpass 800 at clamp(24px, 2.3vw, 36px), line height 1.02 and letter spacing -0.03em. Then comes a 16px paragraph with 1.5 line height, then any rows, in mono 13px with a hairline above each and the label on the left and the value on the right.

Panel copy, word for word
- 01 Fleet, tag "6 vans". The title is "Six vans, thirty stops, one afternoon." The paragraph is "Bayline Courier is a demo fleet driving real East Bay and San Francisco streets. Each line is a route a van already runs today."
- 02 Request, tag "Emeryville". The title is "A lab in Emeryville wants a daily pickup." The paragraph is "Most couriers would price it as a new trip from the depot. Drivepast first asks which van is already nearby." The rows are Pickup with "Daily, Mon to Fri", Window with "1:00 to 3:00pm", and Usual price with "$14 a visit".
- 03 Time, tag "1 to 3 PM". The title is "Lift the afternoon and look for a pass." The paragraph is "Height is time of day, so each route climbs as its van drives. The ring is the customer's window. Van 2 crosses it at 1:45pm." Then comes a legend of three rows, a 26 by 4px accent bar with "VAN 2", a 26 by 2px ink bar with "REST OF THE FLEET", and a 24 by 12px ellipse with a 1.5px accent outline and "PICKUP WINDOW".
- 04 Price, tag "Van 2". The title is "Four extra minutes, 0.6 extra miles." The paragraph is "The stop is priced from what it really adds to Van 2's route. Your floor price is the minimum, and the usual price is the cap." The rows are "Extra time, 4 min" with $1.28, "Extra miles, 0.6 mi" with $0.46, "Cost with 100% markup" with $3.48, "Floor price" with $11.00, and "Offer" with "$11 a visit" in weight 600 under a 2px ink line. Under the rows, in muted mono 11px, it says "Driver time $19.27 an hour (BLS). Mileage $0.76 a mile (IRS)." Get every number in this panel and on the sign from the pricing engine, by pricing a recurring visit that adds 4 minutes and 0.6 miles with the current Settings. With the default Settings, that gives the numbers above.
- 05 Send, tag "No login". The title is "Send the offer in one tap." The paragraph is "The customer gets an email with an Accept link. When they accept, the stop joins Van 2's route." Then come two buttons, "Price a job" (primary, opens the Inbox) and "Replay" (secondary).

3.4 Labels pinned to the 3D scene. These are HTML elements placed by projecting a 3D point onto the screen. While one is showing, update its position up to 30 times a second, and only when the value changes.
- The request tag shows from P 1.72 to 2.6 (see 5.6) and fades over 320ms. It's centered above the pin top (layer 12 in section 4), with its bottom edge 14px above it, and kept on screen, with x between 130 and the width minus 130 and y between 150 and the height minus 90. It has a 1px ink border, paper fill and mono 12px text. A header strip in the accent reads "NEW REQUEST" in ink, weight 600. Under it, two rows read Pickup with "Daily, Mon to Fri" and Window with "1:00 to 3:00pm", with the labels muted.
- The offer sign shows from P 4.28 to 5.06. On desktop it's 318px wide, with its bottom-left corner 22px left of the pin top and 16px above it, kept on screen with x between 40 and the width minus 340 and y between 340 and the height minus 90. On phones it docks under the masthead, 12px in from each side. It's sign green with 6px padding and 14px corners, and inside is a 2px white border with 9px corners. All text is white.
  - In the top row, a 26px white square with 6px corners holds a green "2" in Overpass 800 at 16px, followed by "VAN 2 PASSES", with "DAILY" at the right, all in mono 12px 600 uppercase.
  - Next is "1:45 PM" in Overpass 800 at 46px, line height 0.9 and letter spacing -0.035em.
  - Next is "Our van already passes your door at 1:45pm." in Overpass 600 at 16px.
  - Then comes a 2px white rule, with "Add a daily pickup" at 15px on the left and "$11 a visit" on the right (the price at 24px 800, and "a visit" at 13px).
  - Last is "USUALLY $14" in mono 12px, color #D7E6E0.
  - It fades in over 420ms and rises 18px over 640ms with cubic-bezier(0.16, 1, 0.3, 1). Give it role="status" so screen readers read it.

3.5 Loader. It covers the page until the scene is ready.
- It's paper. The top row has the mark and wordmark on the left and "Demo data" in muted mono uppercase on the right.
- In the middle, "Building the Bay Area from real streets." is set in Overpass 800 at clamp(34px, 5vw, 76px), line height 0.95 and max width 11em. Below it are four rows in mono 14px with a hairline above each, labeled "Street segments", "Buildings", "Vans" and "Stops today" in uppercase, with the values 10,526, 56,364, 6 and 30 from meta.json counts on the right. Each value shows as "..." at 32% opacity until its file has loaded and been decoded, then appears at full opacity.
- At the bottom is a 2px hairline track with an ink fill that grows with download progress.
- When everything for the first view is ready, wait about 600ms, then slide the loader up out of view (translateY(-100%) over 1100ms, cubic-bezier(0.76, 0, 0.24, 1)). With reduced motion, fade it out instead.
- The hero text comes in 950ms after the loader starts leaving. The kicker fades in and rises 16px. Each of the three headline lines slides up from behind a mask (1100ms, cubic-bezier(0.16, 1, 0.3, 1), delays of 150, 240 and 330ms). The paragraph follows at 480ms and the buttons at 600ms.

3.6 Error note. If the scene can't start, show a small paper box with a 1px ink border in the middle of the screen, reading "The 3D view couldn't start on this device, so here's the story without it." Then switch to the fallback in section 6.

## 4. The 3D scene

Setup
- Use deck.gl 9.0.38 exactly (npm install deck.gl@9.0.38), loaded with a dynamic import only on the landing page. Use the Deck class directly with our canvas, not the React DeckGL component. Use one MapView with farZMultiplier 4 and no controller, and cap the device pixel ratio at 2.
- Drive it from one requestAnimationFrame loop that calls deck.setProps({viewState, layers}) every frame. Keep per-frame values in refs, not React state, and pause the loop while the tab is hidden.
- Light it with a LightingEffect holding an AmbientLight (color 242, 245, 255, intensity 1.0) and a DirectionalLight (color 255, 250, 240, intensity 1.0, direction [0.227, 0.743, -0.629]). That's the sun at 1:45pm on October 24 in Emeryville, at azimuth 197 degrees and elevation 39 degrees, which is the same sun the shadow files were made with.
- The base and buildings use material {ambient 0.78, diffuse 0.36, shininess 12, specularColor [16, 16, 16]}. The vans use {ambient 0.62, diffuse 0.62, shininess 48, specularColor [90, 90, 90]}.

Layers from the bottom up, with the height (z, in meters) each one sits at
1. Model base. One extruded SolidPolygonLayer covering the meta.slab rectangle, at z -520.6 with elevation 520, so its top sits at -0.6. It's the plinth of a table-top model, and the light shades its sides.
2. Water. A flat SolidPolygonLayer at z 0.
3. Roads. A PathLayer at z 0.25, with widths in meters of 20, 15, 12, 8 and 3.5 for classes 0 to 4, widthMinPixels 0.6, and colors by class.
4. Shadows. Flat SolidPolygonLayers at z 0.5, the core file first and the rest when it loads, with opacity from the intro.
5. Route ghosts. A PathLayer at z 0.8 showing each van's first full lap, from its first point until the time passes its first time plus loop. Van 2 is the accent at alpha 130 and 6m wide, and the others are ink at alpha 56 and 4m wide, with widthMinPixels 1.1, widthMaxPixels 6 and rounded joints.
6. Stops. A ScatterplotLayer at z 1.0, radius 3px, in building white with a 1.5px outline, accent for Van 2's stops and ink for the rest.
7. Detour. It fades in from P 4.3 to 4.5, then stays. It's a PathLayer at z 1.1, accent, 3px wide with rounded ends, running from Van 2's street point to the customer's door and back to Van 2's path 0.6 minutes later. Add a 4.5px accent dot with a 1.5px ink outline at the door.
8. Buildings. Extruded SolidPolygonLayers, the core file first and the rest when it loads, with the base at z -0.6, elevation equal to height, building white, and elevationScale animated by the intro from 0.02 to 1.
9. Customer building. The same style, drawn on its own, with its color moving from building white to the accent between P 1.55 and 1.85.
10. Trails. Two TripsLayers at z 1.3. One draws the five other vans in ink (6m wide, min 2.2px, max 9px), and the other draws Van 2 in the accent (9m wide, min 4px, max 14px). Both use trailLength 22 minutes, fadeTrail on, rounded caps and joints, and currentTime equal to the story clock (5.4).
11. Vans. Under zoom 14.9, each van is a ScatterplotLayer dot at z 1.6 (Van 2 at radius 6px in the accent, others at 4.5px in 44, 44, 44) with a 2px paper outline. From zoom 15.7 up, each van is a 3D van drawn with a SimpleMeshLayer (described below), and the two crossfade between zoom 14.9 and 15.7. Place the 3D van at the van's point with yaw from its heading, color it the accent for Van 2 and 44, 44, 44 for the others, and set sizeScale = clamp(2 ^ (17.4 - zoom), 1.5, 9).
12. Customer pin. It fades in from P 1.55 to 1.8, then stays. It's a 1.5px ink line going straight up from the roof (the building height times the intro rise) for 66 screen pixels, converted to meters with meters per pixel = 40075016.686 times cos(latitude) / (512 times 2 ^ zoom). At its top is a 6px accent dot with a 2px ink outline. The request tag and the offer sign pin to this top point.
13. Time view. It's drawn only while lift is above 0 (5.5).
14. Place labels. A TextLayer with the meta.places entries at their z, in Overpass Mono 600 at 11px, ink at alpha 190, with an outline in the base color (fontSettings {sdf: true, fontSize: 64, buffer: 8, radius: 12} and outlineWidth 4). Draw them on top with parameters {depthCompare: 'always'}, fade them out between zoom 13.0 and 14.2, and hide them during the time view.

Build the base, water, roads, shadows, ghosts, stops and labels once. Each frame, pass only the props that change (opacity, elevationScale and currentTime), and rebuild only the small layers (vans, pin, detour and time view). Never change accessors or updateTriggers on the buildings, shadows or roads after the first build.

The 3D van. Build it in code at startup as a plain triangle list with per-vertex colors and no normals, so deck.gl uses flat shading. Each vertex color is multiplied by the van's color, so white parts take the van's color. The van faces +x (east) at yaw 0, its origin is at the center of its footprint on the ground, and the units are meters.
- Body. Take the side profile polygon in (x, z), which is (-3.0, 0.38), (2.95, 0.38), (3.0, 0.98), (2.55, 1.28), (1.55, 2.36), (1.2, 2.6), (-3.0, 2.6), and extrude it across y from -1.05 to 1.05. Fan-triangulate each side and add one quad per profile edge. The vertex color is white, except that the windshield edge from (2.55, 1.28) to (1.55, 2.36) is glass [0.11, 0.12, 0.14], and the bottom and front bumper edges are trim [0.2, 0.2, 0.21].
- Side windows. One quad on each side, 1.5cm outside the body, with corners (1.3, 1.42), (2.42, 1.42), (1.68, 2.22) and (1.3, 2.22), in glass color.
- Sliding door seam. A thin trim strip on each side from x -2.0 to -1.95 and z 0.62 to 2.44.
- Wheels. Four 10-sided cylinders with radius 0.38 and half-width 0.16 along y, centered at x 2.05 and -2.0, y 0.86 and -0.86, and z 0.38, in tire color [0.07, 0.07, 0.08].
- Heading. The yaw in degrees is atan2(north, east) of the van's current path segment, where east is the change in longitude times cos(latitude) and north is the change in latitude. Keep the last heading while the van is stopped.
- Position at time t. Binary-search the van's ts for the segment that holds t and interpolate linearly.

## 5. The story

5.1 Progress. P is window.scrollY divided by the height of one section unit in pixels, measured from section 0. P runs from 0 at the top to 5.6 at the bottom. Section i's panel is in view around P = i, and section 4's from about 4.0 to 4.9.

5.2 Camera keyframes. Each keyframe puts a subject point at a spot on the screen, given as fractions of the width and height from the top left (fx, fy), with a zoom, a pitch and a bearing. To get the map center for a keyframe, make a deck.gl WebMercatorViewport centered on the subject S with that zoom, pitch and bearing and the canvas size. Unproject the screen point at fx times the width and fy times the height to get a ground point G, and use 2S - G as the center, computed in Web Mercator coordinates. On desktop, add log2(min(width / 1440, height / 900)), clamped between -1.2 and 0.8, to every zoom. On phones (width under 760, or width divided by height under 0.85), use the phone values and add log2(min(width / 390, height / 844)) instead.

| Key | Hold, P from and to | Subject | fx, fy | Zoom | Pitch | Bearing | Orbit | Drift | Phone fx, fy, zoom, pitch |
|---|---|---|---|---|---|---|---|---|---|
| 0 Hero | 0 to 0.3 | Model center (-122.3328, 37.8314) | 0.66, 0.56 | 11.0 | 50 | -35 | 6 | 0.1 | 0.5, 0.72, 9.65, 47 |
| 1 Fleet | 0.92 to 1.3 | (-122.272, 37.834) | 0.63, 0.54 | 12.5 | 54 | -20 | 8 | 0.1 | 0.5, 0.36, 11.7, 50 |
| 2 Request | 1.95 to 2.3 | Customer building center | 0.40, 0.60 | 16.2 | 58 | -28 | 14 | 0.14 | 0.5, 0.38, 15.7, 56 |
| 3 Time | 2.95 to 3.3 | Customer door | 0.60, 0.84 | 14.5 | 62 | -10 | 16 | 0 | 0.5, 0.58, 13.9, 60 |
| 4 Price | 3.95 to 4.85 | Van 2's street point | 0.56, 0.70 | 18.1 | 66 | -14 | 10 | 0.1 | 0.46, 0.5, 17.5, 64 |
| 5 Send | 5.5 to 5.6 | (-122.276, 37.832) | 0.62, 0.52 | 12.5 | 42 | -18 | 2 | 0 | 0.5, 0.34, 11.6, 42 |

- During a hold, the bearing turns by the orbit amount and the zoom moves by the drift amount, going from minus half to plus half across the hold. Recompute the center every frame so the subject stays at (fx, fy).
- Between holds, fly from the end of one hold to the start of the next. Let e be an ease-in-out cubic of the progress between the two holds. The zoom is z0 + (z1 - z0) times e. If the zoom changes by less than 0.05, interpolate the center in Web Mercator. Otherwise zoom about the fixed point F = (C1 - r times C0) / (1 - r), where r = 2 ^ -(z1 - z0), so the center is F + (C0 - F) times 2 ^ (z0 - z). That makes each flight one smooth move instead of a pan followed by a zoom. Ease the pitch and the bearing with the same e, and turn the bearing the shorter way round.
- On top of everything, add a slow sway of 1.3 times sin(0.26 s) to the bearing and 0.7 times sin(0.24 s) to the pitch, where s is the time in seconds.

5.3 Intro. Start the camera looking straight down (pitch 0, bearing -12) over the model center at zoom 10.35 plus the size offset, or at 9.0 on phones. When the loader starts leaving, fly to the scroll camera over 2.9 seconds. Buildings rise from elevationScale 0.02 to 1 over 2.3 seconds, starting 0.15 seconds in, with an ease-out cubic. Shadows fade in from 1.5 to 2.6 seconds in, and trails from 1.3 to 1.9 seconds.

5.4 Story clock, in minutes after 12:00 noon. In the hero, while P is 0.24 or less, the clock runs by itself from 12:30 to 1:20pm at 5 minutes a second, starting 1.4 seconds into the intro. It loops, and the trails fade out and back in over 1.3 minutes of clock time at each loop. Once P passes 0.24, the clock stops running on its own and follows scrolling as below.

| P | Clock |
|---|---|
| 0.24 to 0.86 | Eases from the hero time to 82 (1:22pm) |
| 0.86 to 1.95 | 82 to 95 |
| 1.95 to 2.95 | 95 to 99 |
| 2.95 to 3.95 | 99 to 101.5 |
| 3.95 to 4.35 | 101.5 to 105, easing out so Van 2 brakes into the door |
| 4.35 to 4.85 | Holds at 105 (1:45pm), with Van 2 at the door |
| 4.85 to 5.6 | 105 to 117 |

The timeline bar shows this clock as text like "1:45 PM" and moves its marker to match.

5.5 Time view, chapter 3. lift is a smoothstep that rises from P 2.32 to 2.9 and falls from 3.3 to 3.78. While lift is above 0, draw the following.
- Ribbons. Each van's path between 12:30 and 3:30pm (t from 30 to 210) is a 3D PathLayer with z = (t - 30) times 6 meters, scaled by lift through the layer's modelMatrix, which scales z only. Van 2 is the accent at 3.4px with rounded caps, and the others are ink at alpha 170 and 1.6px. The opacity is min(1, 1.4 times lift).
- Window column at the customer's door. Three rings of 29 points with radius 38m sit at the 1:00, 2:00 and 3:00pm heights (accent at alpha 235, 110 and 235, 1.6px wide), with six vertical lines between the 1pm and 3pm rings (accent at alpha 150, 1.1px).
- Pass point. A 6.5px accent dot with a 2px ink outline sits at Van 2's street point at the 1:45pm height. Its label reads "VAN 2 PASSES 1:45 PM" in Overpass Mono 600 at 12px, ink on an accent box with 6 by 4px padding, ending 14px to the left of the dot.
- Hour labels. "1 PM", "2 PM" and "3 PM" sit 58m east of the door at each height, in mono 600 at 11px, ink on a paper box at alpha 240.
- Now dots. Each van's current position sits at the current clock's height as a 4px dot in the van's color with a 1.5px paper outline.
- The labels fade in once lift passes 0.55 and draw on top with depthCompare 'always'. The ground trails and van markers fade out by 1 - lift.

5.6 When things show

| What | P |
|---|---|
| Customer building turns accent | 1.55 to 1.85, then stays |
| Pin | 1.55 to 1.8, then stays |
| Window band on the timeline bar | 1.6 to 1.9, then stays |
| Request tag | In from 1.72 to 1.9, out from 2.42 to 2.6 |
| Time view | 2.32 to 3.78 |
| Offer sign | In from 4.28 to 4.42, out from 4.92 to 5.06 |
| Detour and door dot | 4.3 to 4.5, then stays |
| Place labels | By zoom, and hidden during the time view |

5.7 Playing by itself
- 3.4 seconds after the loader starts leaving, if nobody has scrolled, tapped or pressed a key, the story plays by scrolling the window. It holds for 2.6 seconds at P 0, moves to 1 over 4.4 seconds, holds 2.8, moves to 2 over 4.6, holds 3.0, moves to 3 over 4.6, holds 3.4, moves to 4.0 over 4.4, holds 0.1, moves to 4.62 over 5.4 with an ease-in-out sine, holds 3.2, and moves to 5.6 over 4.8, then stops. All the other moves use an ease-in-out cubic.
- Any wheel, touch, pointer press or scrolling key stops it.
- The masthead button says Pause while it's playing, Play when it's stopped, and Replay at the end (P above 5.45). Replay scrolls to the top and plays from the start. "Play the afternoon" and Play start from the current spot after 0.8 seconds.
- The chapter buttons glide to P 1, 2, 3, 4.5 and 5.6 over 0.9 + 0.55 times the distance in seconds, with an ease-in-out cubic, scrolling the window every frame.

## 6. Phones, reduced motion, fallback and speed

Phones (width under 760, or width divided by height under 0.85)
- Use the phone keyframes, and load only the core buildings and shadows.
- Panels become bottom sheets, the full width less 12px on each side. They sit at the bottom of their section and stick 88px above the bottom of the screen, and section padding becomes 72px on top and 90px at the bottom. Hide the rows, keeping the title and paragraph.
- Hide the chapter buttons, the masthead label and the Motion switch.
- The offer sign docks under the masthead.

Reduced motion. When the device asks for reduced motion, or the Motion switch is off, nothing moves by itself. There's no intro flight or rise (buildings start at full height), no sway, no autoplay and no hero clock loop, and the hero clock stays at 1:10pm. The camera cuts to the current chapter's keyframe instead of flying, the loader fades, and scrolling still moves the clock. The Motion switch remembers the choice in localStorage.

Fallback. If WebGL isn't available, a file fails to load, or the first view isn't ready after 12 seconds, hide the canvas and the loader and show the error note for 4 seconds. Then show the page as plain scrolling text on the table color, with the hero and the five panels in order and the timeline bar at 1:45 PM.

Speed
- Load meta, fleet, water, roads, buildings-core and shadows-core, in that order, and start the intro once they're ready. On desktop, then load buildings-rest and shadows-rest and add them as extra layers.
- Measure the frame time. If the average over 3 seconds is above 40ms, drop the rest layers and the shadows and cap the pixel ratio at 1.5.

Build order. Build it in this order and check each part before the next. First the static page with the sections, panels, bars and copy. Then the loader and the data decoding, checked against sample.json. Then the base, water, roads, buildings and shadows. Then the trails, vans and pin. Then the camera keyframes, scrolling and the clock. Then the time view. Then the pinned labels, the sign and autoplay. Last, phones, reduced motion and the fallback.

## 7. Carry the look into the app

Do this right after the landing works, in no more than about 150 credits. It's a restyle only, so don't move, rename or remove anything, and don't change any data, logic or flows. If it would take more credits than that, stop and tell us.
- The app background is #ECEAE4. Panels and the rail are paper, with 1px ink borders around major panels, hairlines inside them, square corners and no shadows.
- Text is ink, secondary text is muted, and the accent marks the selected van, the active rail item and key highlights, always with ink text on it. Remove the lime accent and the charcoal background.
- Overpass and Overpass Mono replace IBM Plex everywhere, with prices, times and miles in Overpass Mono.
- Buttons follow the landing, ink for primary and paper for secondary. The stat-chip row becomes a ruled strip of mono labels and values divided by hairlines.
- The quote card and prospect offers use the route-sheet panel style, and the customer-facing quote preview uses the green sign style from 3.4.
- Amber "Needs clarification" flags use dark amber text #92400E on a pale amber fill #FBEBD3.
- 2D maps use OpenFreeMap's light style at https://tiles.openfreemap.org/styles/positron. Keep each van's route color, but darken any that falls under 3 to 1 contrast against the light map. Prospect pins are green #1F7A4D under $2.50, yellow #A86A00 from $2.50 to $4, and red #B83A14 over $4.

## 8. Credits

The "About and credits" page lists these lines exactly, and the landing keeps its own credit line visible.
- Map data © OpenStreetMap contributors
- Buildings, roads and water from OpenFreeMap vector tiles © OpenMapTiles
- Map tiles: OpenFreeMap © OpenMapTiles Data from OpenStreetMap
- Demo routes computed with OSRM from OpenStreetMap data
- Shadows computed for the sun at 1:45pm on October 24
- 3D drawn with deck.gl. Fonts Overpass and Overpass Mono, SIL Open Font License

Remove the Kenney and React Three Fiber lines unless an extra still uses them.

## 9. Done when
- On a laptop in Chrome, the loader shows within a second, the city rises within 6 seconds, and the story plays itself through all five chapters with no visible stutter.
- Scrolling by hand at any speed, down and back up, never makes the camera jump, and the clock only moves forward while scrolling down.
- At P 4.6, Van 2 is stopped at the door, the clock reads 1:45 PM, and the sign shows the engine's price for 4 added minutes and 0.6 added miles, which is $11 a visit, usually $14, with default Settings.
- In chapter 3, the routes rise, the window column stands at the door, and "VAN 2 PASSES 1:45 PM" sits where Van 2's ribbon crosses it.
- At 1440 by 900, 1280 by 720, 1920 by 1080 and 390 by 844, the customer building, pin, tag and sign are fully on screen in their chapters and never cover a panel.
- With reduced motion on, nothing moves by itself and every chapter still shows its picture.
- With WebGL off, the page still reads as text with all five panels.
- There are no gradients, glows, pill chips or IBM Plex anywhere, and the credits page lists every line in section 8.

## 10. Where it goes
- The landing (sections 0 to 6 and 8) replaces step 9 of the work list, and the app restyle (section 7) comes right after it as part of step 9.
- In the extras, replace the two 3D items with these two. One is a "3D view" toggle on each van's page that replays that van's day in this white-model scene, reusing the landing's scene with the camera on that van's route. The other is the procedural van from section 4 turning slowly on a paper tile for empty and loading states.
- If the landing isn't working by Sunday 7am, turn Motion off by default so the camera cuts between chapters, and keep everything else.
- After each part, reply with one line saying what's done, what you checked and how many credits you've used.
