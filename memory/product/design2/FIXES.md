# DESIGN UPDATE 2, FIXES (verbatim intent from the user, Sun Oct 25). These override PROMPT.md where they differ.

Data: surroundings.json (new) and water.json (replaced) are already in /app/frontend/public/drivepast/. Don't open or print them.

- Ground. Replace the model base plinth (old layer 1, meta.slab) with one flat SolidPolygonLayer covering the rectangle in surroundings.json, color 226, 224, 218, so the map fills the screen out to the horizon in every shot. surroundings.json is {"ground": [[x0, y0], [x1, y1]], "roads": [[class, ring], ...]}. The ground corners are ABSOLUTE; the road rings are delta-encoded like roads.json. Draw those roads right after the water, with the same widths and colors as roads.json. (meta.slab is now just the corners of the detailed city area.)
- Water. water.json is now a list of POLYGONS, each a list of rings: first ring is the outline, others are holes (islands like Alameda). Covers the detailed city and coarser water out to the horizon.
- No flicker. Ground, water, both road layers, shadows, route ghosts, stops, detour and door dot all lie on the ground. Draw them in that order with parameters {depthCompare: 'always', depthWriteEnabled: false}. Building bases at z 0 (not -0.6).
- Load order: meta, fleet, water, surroundings, roads, buildings-core, shadows-core.
- Keyframes replaced (wide shots look west across the bay):
  - 0 Hero: subject (-122.288, 37.836) at 0.64, 0.64, zoom 12.9, pitch 56, bearing -78, orbit 6, drift 0.1. Phone 0.5, 0.72, zoom 11.9, pitch 54.
  - 1 Fleet: subject (-122.276, 37.83) at 0.62, 0.58, zoom 13.1, pitch 52, bearing -62, orbit 8, drift 0.1. Phone 0.5, 0.42, zoom 12.1, pitch 50.
  - 2, 3, 4 unchanged from PROMPT.md.
  - 5 Send: subject (-122.283, 37.834) at 0.62, 0.55, zoom 12.9, pitch 46, bearing -95, orbit 2, drift 0. Phone 0.5, 0.4, zoom 11.9, pitch 46.
- Intro: start straight down (pitch 0, bearing -60) over (-122.3228, 37.8314) at zoom 12.4 plus the size offset, or 11.3 on phones.
- Phones: width under 640, or width/height under 0.85 (was 760).
- Speed: cap pixel ratio at 1.5 (was 2). Add buildings-rest and shadows-rest as layers only 3.3 seconds after the intro starts. Frame-time drop (avg > 40ms over 3s): drop rest layers and shadows, cap pixel ratio at 1.
- Small changes: shadows alpha 60 (was 41). Trail max widths 6px other vans, 8px Van 2. Van sizeScale = clamp(2 ^ (18.2 - zoom), 2.4, 10). Detour returns to Van 2's path 0.03 minutes after the street point.
- Done when (added): every chapter fills the screen at 1440x900, 1920x1080, 1280x720 and 390x844 with no empty background, and water and roads never flicker while the camera moves.
