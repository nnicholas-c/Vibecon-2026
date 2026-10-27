# Phase 3 journeys

All earlier journeys (JRN-1 to JRN-43) stay valid. Fresh "Reset demo data" unless stated.

- **JRN-44** The new look, everywhere
  - steps: Open Dispatch, Van 2, Settings (including Engine test), Inbox and Phones on a laptop, then repeat at 390x844.
  - expected:
    - Every screen uses the same dark Haulix-style look (reference `/app/memory/product/design_refs/haulix_ref.png`): charcoal surfaces, rounded cards, pill stat chips with real engine values, lime accent, a dark map.
    - No Haulix logo, truck art, compass or gauges appears.
    - The six van colors are still distinct and match between rail dot, timeline and map.
    - Amber appears only for problems and red only for "can't do it".
    - Prices and times line up in columns (tabular numbers).
    - Body text is easily readable.

- **JRN-45** Earlier journeys still pass
  - steps: Rerun the Phase 1 and Phase 2 suites.
  - expected: Every earlier journey passes unchanged, with the same copy and controls.

- **JRN-46** Van 2's map
  - steps: Open Van 2.
  - expected:
    - Within 2 seconds a map shows OpenStreetMap tiles with "© OpenStreetMap contributors".
    - It shows a line in Van 2's color from the Emeryville depot through 20 numbered stops and back.
    - Markers 1 to 20 match the timeline order. The depot has its own marker.
    - The map is zoomed to fit the route.
    - Clicking marker 1 shows its customer name, address, arrival time and window.

- **JRN-47** Fleet map on Dispatch
  - steps: Open Dispatch. Click "Van 5" in the map legend.
  - expected: The fleet map shows six routes, each in its van's color, covering both the East Bay and San Francisco, with a legend naming Van 1 to Van 6. Clicking Van 5 in the legend opens Van 5's page (interpreted).

- **JRN-48** Show a priced job on the map
  - steps: In Settings > Engine test, press "Run all", then "Show on map" on request 1.
  - expected:
    - Van 2's page opens.
    - Two "new request" pins in a distinct style mark 5200 Shattuck and Ashby Medical Center, with a dashed line showing where they'd slot in.
    - Van 2 still has 20 stops on its timeline, so nothing was booked.

- **JRN-49** Booked stops appear, and Undo removes them
  - steps: Accept request 1's winning option (API), open Van 2, then undo (API) and reload Van 2.
  - expected: After accept, the map shows 22 numbered markers with the two new ones marked "New", matching the timeline. After undo it shows 20 markers again, identical to before.

- **JRN-50** Tiles down
  - steps: Block the OpenStreetMap tile server and open Van 2.
  - expected: Route line and numbered markers still draw. "Map tiles couldn't load. Routes are still shown." appears. No error text or JSON.

- **JRN-51** Map on a phone
  - steps: At 390x844 pick Van 2 in List and open the Page tab. Scroll the page past the map, then pinch-zoom the map.
  - expected: The map fills the width with no horizontal scrolling, the page scrolls past it, and pinch zoom works on the map. The timeline and stats are below it as before.

- **JRN-52** Reduced motion
  - steps: Turn on the reduced-motion setting and open several screens.
  - expected: Decorative motion is off. All content and numbers show immediately.
