# Drivepast PRD

## Original problem statement
Drivepast gives every van of a small courier (Bayline Courier, 6 vans) its own agent. 10 phases. The source docs are /app/memory/product/overview.md (D-1 to D-13 win), spec_part_a.md, and phase1/requirement.md + journeys.md.

## Architecture
- Backend FastAPI (/api, OpenAPI at /api/openapi.json) + MongoDB (motor). Plain Python math only.
  - engine/timing.py: haversine x road factor, SF/East Bay/cross-bridge speeds, compute_route (window waits, learned service minutes, feasibility, duration, spare). Phase 2 reuses it.
  - seed/data.py + seed/build.py: deterministic seed (random seed 20260912). Reset writes to staging collections, then renames them (no half-wiped data).
  - server.py: fleet, units, route plans (versioned, previous kept), stops, run history, directory, prospects, requests, echo agents, settings (validated), demo reset.
- Frontend React + Tailwind + shadcn: three panes (rail 260px / chat / page), mobile tabs List/Chat/Page. IBM Plex Sans + Plus Jakarta Sans, deep green accent.

## Persona
Non-technical owner/dispatcher (Rosa Delgado, fictional) on a laptop and a phone. No login.

## Implemented (Phase 1, Oct 2026)
- All spec section 4 collections; seed: 6 vans x 20 stops, 2,400 run records, 11 directory businesses, 40 fallback prospects, 10 requests.
- Route timing + route_plans with versions; recompute when travel settings change (~13ms).
- Rail, echo chat (agent_threads), unit page (header, stats, timeline), Dispatch table, Settings (all defaults, validation, connection rows, reset demo).
- Testing: iteration_1 passed 100% (18 backend tests in /app/backend/tests/test_drivepast_api.py, plus UI flows).

## Implemented (Phase 2, Oct 2026): pricing engine
- engine/matrix.py (cached travel_matrix, rebuilt on travel settings change), engine/insertion.py (single/pair/multi-stop insertion, D-14 added minutes, D-15 hours, D-16 pair window search, D-17 demo clock, neighbor swaps, plain reasons + where/until), engine/pricing.py (floor/markup, 50-cent round up, explanation lines), engine/jobs.py (hand-built jobs for the 10 seeded requests, stored on requests).
- core.py: weekday plans + date plans; unit page/Dispatch show today's route.
- engine_api.py: /api/engine/{jobs,price,run-all,what-if,accept,undo,changes}, /api/stats/fleet, /api/stats/units/{key}.
- Settings > Engine test tab (Run all, per-van rows, winner, hand check, ms, what-if).
- Testing: iteration_2 passed 36/36 (phase1 + phase2 suites).
- Results: R1 Van 2 +8 min 0.1 mi $2.65 -> $11/$231; R2 Van 3 $35; R3 Van 5 $11/$94.60; R4 shifted 4:15pm Van 4 $35; R8 shifted delivery by 9:15am Van 2 $87.50. All under 12 ms.

## Seeded numbers (spare min / on-time)
Van 1 45 / 97.2%, Van 2 50 / 99.2%, Van 3 42 / 97.8%, Van 4 43 / 98.8%, Van 5 55 / 98.5%, Van 6 62 / 91.2% (lowest).

## Backlog
- P0 Phase 3: maps.
- P1 Phases 4 to 7: maps, request reading with the AI ladder, agents, quotes and phones, prospecting.
- P2 Phases 8 to 10: analytics, polish, optional plumbing, deploy.
- Note for Phase 2: waits sit inside route duration, so new stops in a waiting gap add about 0 minutes (request 1 best insertion ≈ $0.08).

## Phase 3 (Oct 24, 2026): new look + maps
- Dark skin based on Phenomenon Studio's Haulix dashboard (replaces the earlier studio-website skin). Manrope (tabular figures), charcoal surfaces, lime accent #E2F37A, pill stat chips, rounded rail tiles.
- Leaflet + OSM maps with a dark filter on the tiles only: unit map, Dispatch fleet map with legend, Engine Test "Show on map" preview (does not book), message when tiles fail, round zoom/reset controls, fit to route after a phone tab switch.
- Van colors re-tuned for the dark map: #60A5FA #A78BFA #F472B6 #22D3EE #FB923C #34D399 (existing data synced at startup).
- Tested in iteration_4: 46/46 backend tests pass, no UI bugs.
- Next: Phase 4 (waiting on spec).

## Phase 4 + v2 Step 1 (Oct 24, 2026): three options, reading any request
- Master spec is now /app/memory/product/spec_v2.md (work list). Step 1 = Phase 4 plus the step1 adjustments.
- Engine: every feasible van × slot is priced. Labeled Cheapest / Soonest / Preferred window (one card when two labels share a slot), plus up to 5 "other options" (at most 2 per van). Shifted windows are used when nothing fits as asked. Usual price cap ($14 recurring, $55 one-off; a floor above the usual price is refused). "Loses money" goes to a draft. Customer line comes from templates.
- AI ladder: Our model (blank by default) -> built-in Emergent key (reading: Claude Haiku 4.5 + 5 examples; switchable to Sonnet 5.5 / GPT-5.5 / Gemini 3 Flash; assistant model setting defaults to Sonnet 5.5) -> no-AI keyword reader. AI mode Auto / Skip our model / No AI. Test stand-in at /api/dev/stub-llm is gated by DEV_STUB_ENABLED (off by default) and tagged "test stand-in".
- Reading: record_request with per-field confidence, more than one job per message (request 14 splits into linked "1 of 2"/"2 of 2"). Locations: directory -> geo_cache -> Nominatim. Problem checks in code: city, missing addresses, impossible window, opening hours, duplicate.
- Inbox: list + request page (raw left, details right), Ask the vans / Ask the customer (editable draft) / Decline. Uploads: PDF (pypdf) and photo go to Emergent Object Storage. 14 seeded requests (11 to 14 are new formats).
- Tests: iteration_5 and iteration_6 passed. 84 backend tests pass. Field accuracy 120/120 at the built-in level and in No AI mode (seeded set).
- Next: work-list step 2 (send, accept, undo, customer behavior).

## v2 Step 2 (Oct 24, 2026): send, accept, undo, Demo phones
- Option cards: Send / See other options / Reject (next best for that label swaps in). Sending a loss-making option asks "This loses money at your usual price. Send anyway?" first.
- Setting "Auto-send the cheapest option within my rules" replaces the old auto-send. It is off by default.
- Demo phones drawer with Customer / Driver / Owner phones, refreshed every 2 s while open. Accept books through the engine and sends Driver + Owner notes. New stops glow on the timeline for 10 s. Stale slot sends the REQ-274 messages. "Yes" replies accept, anything else is read again, and with no open quote a text becomes a new request. Undo works from the request or van page and sends "Change cancelled". Ask the customer posts to the Customer phone. The Settings demo controls work. Real texting stays OFF (phones are in-app, stored in phone_messages).
- Tagline: "Price every job from the van that already drives past."

## v2 Step 2b (Oct 24, 2026): closer Haulix look
- Studied the Dribbble shot: video plus 3 stills, frames saved in /app/memory/product/step2b/refs.
- Floating rounded panes on a near-black backdrop. Top bar with stat chips, search across vans, stops and requests, bell with the Inbox count, and "Rosa Delgado · Owner".
- Pages have a big title and a Today / This week pill (week = today × 5 weekday routes).
- Fleet map: filter pills with counts, toggles for routes and van icons, a stack of round map controls, van selection (lime route, others dimmed), and 62vh height.
- Van map: floating detail card with status, Stop N of M, next stop, striped day bar, return time, a Day used dial, a Spare minutes fill, and a late insight banner from run history (only Van 6 has one now).
- Each van shows as our own top-down icon at its demo-clock position, turned to its heading, with a lime halo when selected. Motion: route draw-on, slide-up, gauge sweep and wave, pill slide, springy switches, hover lifts. Reduced motion is respected.
- Q-46: Van 2 route + icon drawn in 0.8 to 1.25 s.
- Tests: iteration_7 passed with no issues. Backend 84/84 (run serially, -n 0).

## v2 Step 3a (Oct 24, 2026): sensible routes, optimizer, street lines
- Re-seeded each van as one geographic loop (area by area, waterfront stops mirrored inland). Spare 43/48/40/43/56/58. Van 2 1:50pm Shattuck / 2:15pm Telegraph. Van 4 ends 3:50/4:05pm. Van 6 least on time after noon.
- Request 1: Van 2 at $2.65, $11. Request 4: Van 4 at 4:15pm. Request 8: Van 1, delivery by 9:44am.
- engine/optimize.py: 2-opt + or-opt, feasibility via compute_route. "Optimize route" bar with Apply/Cancel/Undo (routes_api.py). Auto-runs after each booking. Booked windows = quoted ±15. Booking undo restores the previous seqs.
- OSRM street lines: /api/map/geometry/{unit}, lazy, 1 req/s, custom UA, cached in route_geometry (kept on reset). Freeway-snap detours are trimmed to straight legs. Straight-line fallback with a note. Attribution "Routes © OSRM".
- Retired 3 outdated e1_tests. Tests: iteration_8 all pass (2 stand-in tests fail by design while DEV_STUB_ENABLED=false).

## Our model = OpenAI (your key) (Oct 24, 2026)
- call_ours: no chat_template_kwargs to api.openai.com. gpt-5/gpt-6/o-series get no temperature and get reasoning_effort "minimal". A 400 naming a field drops it and retries. json_schema then JSON-only fallback.
- Settings "Use OpenAI (your key)" shortcut fills https://api.openai.com/v1 + gpt-5-nano. The UI never shows the saved key.
- Labels "OpenAI (your key) · <model>". 401 → "OpenAI turned the key away. Check the key." 429 → "OpenAI says the key is out of credit or rate-limited."
- Checked by scripts/openai_slot_check.py (mocked) and a live 401 against api.openai.com with a fake key.

## Step 4 (Oct 24, 2026): real email, Google sign-in, sign-in screen
- google_api.py: the team's own OAuth client (start/callback with signed single-use state, redirect built from X-Forwarded-Host/Proto). Tokens server-side, plus a signed HttpOnly Secure Lax session cookie, /auth/me, /auth/logout, and /dev/test-session (off unless DEV_TEST_SESSION_ENABLED=true).
- Gmail: check from the open Inbox (30 s) or the Check inbox button. Only mail after connect, deduped by ID, 30 per hour, attachments to object storage then the reader, own sent IDs skipped, newsletters skipped.
- Quotes to Gmail requests reply in-thread with signed single-use /q/<token> Accept/Decline. Fallback is Emergent-managed email with reply-to set to the owner. Undo emails "Change cancelled.". Stale sets Needs attention. Directory and prospect addresses are refused.
- Frontend: AuthGate sign-in screen (Google / Open the demo, remembered), top bar shows the Google name, picture and Sign out. /q page is public at 390px. Settings "Email and Google" section. Inbox GmailBar.
- REQ-395: the settings API returns no key characters ("saved" only).
- Tests: scripts/step4_mock_check.py 32/32 (mocked Google), iteration_9 passed (UI 100%).

## Backlog (next)
- Work-list step 3 (agents/assistant answers), then prospecting, analytics, deploy.


## Implemented (UI-3D pass, Oct 2026)
- MapLibre GL 5 + OpenFreeMap vector tiles (no key), custom near-black olive style (mapStyle.js), 3D fill-extrusion buildings (render_height; heights boosted x2.2 at z13 tapering to x1 at z17).
- CityMap.jsx: pitch-aware whole-route fit (route long axis turned up-screen, avoids the detail card), pitch 55, van-page zoom floor 13.05, 2.4s fly-in (skipped under reduced motion), reset/zoom/fullscreen/layers drive MapLibre, cooperative gestures on touch.
- Routes: lime + two blurred glow layers for selected, others dimmed; stop/depot/request pins and vans as DOM markers (always above buildings). Van = generated PNG /assets/van-topdown.png (rotationAlignment+pitchAlignment map) with a van-color roof dot and ground halo.
- Leaflet kept as LeafletRouteMap.jsx fallback (no WebGL, or localStorage dp-flat-map=1). Tiles down -> "Map tiles unavailable".
- Panel depth (grain backdrop, highlight edges, inner/drop shadows), glossy tick-marked gradient Day-used dial, ticked Spare tile.
- Testing: iteration_10, 11/11 UI-3D journeys pass. Screens in /app/memory/product/ui-3d/screens/.
- Revision 1 (REQ-441..449): van pages open in a close-up follow view (z16.5, pitch 55, bearing = heading), which stops following on drag, wheel, rotate or +/- and comes back on reset. Real building heights from z15.5. Van position is snapped to the drawn street line for display. New slim van PNG at its real footprint (5.2 m, clamped 30-64 px). Stop pins sit above vans. Fleet uses 16px dot+arrow markers. On phones the detail card starts collapsed (van-detail-toggle, van-detail-collapsed-summary, van-detail-collapsed-spare, van-detail-body). Tester iteration_11: everything passed except the wheel-unfollow bug, now fixed and self-checked. Screens in ui-3d/screens/rev1/.
- Next: step 5 (Fleet assistant + Dispatch->Fleet rename).

## Implemented (Task 1 + Design Update 2 app side, Oct 24 2026)
- backend/agent.py: real dispatch/van agent over the OpenAI-compatible chat completions API using the AGENT_* env vars. Caps: max_completion_tokens 300, at most 3 tool rounds, last 8 history messages, no retries, 300 model calls a day (agent_usage collection, keyed by Pacific date). Tools: get_fleet_summary, get_van_route, explain_stop, get_options, move_stop, save_rule (agent_rules collection). Every tool call is logged to the events collection. reasoning_effort is "none" because every call sends tools. The Our model UI is removed from Settings.
- GET /api/landing/price (engine_api.py): engine pricing for a recurring visit that adds 4 min and 0.6 mi. With default Settings it returns $11 a visit, usually $14.
- Section 7 restyle: paper and ink tokens, #FF5B1F accent, Overpass and Overpass Mono, square corners, no shadows, blur or gradients. Maps use the OpenFreeMap positron style, van colors are darkened to at least 3:1 on the light map, and the glows and halos are gone. Option cards use the route-sheet style; the customer quote and the public quote page use the green sign.
- The landing (src/landing, public/drivepast) is owned by a separate agent.

## Step 6 (Oct 25, 2026): Memory rules + Activity feed, landing FIXES
- engine/rules.py: "van X not to SF/downtown after T" rules exclude options (options.blocked rows with the plain reason). Open requests are re-priced on view when rules change. memory_api.py: /api/memory/rules (list/PATCH/DELETE) and /api/activity (events, newest first). activity.py logs read/send/accept/decline/undo/rule/ask/driver events.
- Landing FIXES applied (surroundings ground, polygon water, keyframes, DPR 1.5, rest 3.3 s, etc.). /?e2e=1 turns off the 12 s fallback. Tester iteration_12 passed 100%.

## Step 7 (Oct 25, 2026): the one demo
- 3-van fleet (seed/data.py). The old 6-van DB auto-reseeds on start. Landing draws vans 1-3 ("Three vans, sixteen stops").
- Auto-send (Demo mode = auto_send_cheapest) only for status priced; flagged or money-losing requests are held.
- Booking toast (phones_api.booking_toast) is stored on quote.booking. LiveWatcher.jsx polls /api/live every 1.5 s (toast, reload, highlight) and checks Gmail plus sheet sync every 30 s app-wide.
- Presenter: /present (PresenterView: strip + FleetMap + Driver and Customer phones), /api/demo/run|scripted-email|stop. The scripted email is a Hollis St pickup, which the engine prices on Van 2 at $35 instead of $55. Auto-accept after 5 s. After booking it opens the van page with the agent box pre-filled.
- Import jobs (import_api.py): Google Sheet via the Google token, or CSV to Object Storage. One AI column match (keyword fallback), confirm, rows become requests (read in background), dedupe by row hash, Sync now, 30 s sheet sync.
- Dispatch page: removed the 3 stat cards (one stat strip + map + table).
- Backlog: real-Gmail run of JRN-213/224 by the user. Optional: auto-inject the scripted email if no real email arrives.

## Step 8 (Oct 25, 2026): routing fixes
- Auto-reoptimise (routes_api.auto_optimize): runs on accept, stop done (POST /api/units/{u}/stops/{s}/done, or the driver phone saying "done"), assistant move_stop, and fleet change. Done or passed stops stay locked; a new order is skipped if it opens an arrival gap over 30 min. Writes an events row {kind:"reorder", van_id, text}. GET /api/events?since= feeds a 10 s toast poll (ReorderToasts). The Optimize route button is removed.
- spare = shift - driving - service (timing.py). The tile reads "Driving and stops: X of Y min" (unit.busy_minutes).
- Insertion from current position: Base adds a "where the van is now" node when the van is mid-leg at the demo clock.
- Options: same van + same price merge ("Cheapest and soonest"); Preferred window only shows when asked_minutes is set; at most 2 cards.
- Seed windows are spread over the shift with consecutive arrivals ≤ 28 min apart (seed/build.timing_pass).
- Checks: scripts/step8_check.py, scripts/step8_reorder_check.py, scripts/runall_snapshot.py (before/after JSON in scripts/).

## Step 9 (Oct 25, 2026): Smarter Done, reorder overlay, price ruler
- Driver Done marks the stop the van is at or heading to at the demo clock (phones_api.driver_done). If there's none: "No stop to mark done right now." Done stops store done_minutes; compute_route re-times later stops from done_at (only on today's date plan, so pricing is unchanged). /api/live routes_sig triggers a reload within 1.5 s.
- Reorder events carry old_order/new_order. The van map shows the old order dashed and faint, the new order in the van's color and pins as old → new for 6 s. The toast has "Show on map". Reduced motion is static.
- The booking toast has a PriceRuler ($0 to usual, accent marker slides from usual to price) fed from booking.ruler (the same engine numbers as the toast text).
- Checks: scripts/step9_done_check.py, scripts/step9_visual_trigger.py.

## Step 10 (Oct 25, 2026): savings tally, Done time jump, hands-free rehearsal
- /api/live returns saved_today = sum over accepted quotes of (booking.usual - price). The Dispatch strip shows "Saved customers $X today". Undo and Reset drop it.
- mark_done stores time_shifts (later stops whose arrival moved ≥ 1 min). The unit timeline has time_shift → "+N/−N min" tag (hidden after 60 s, cleared by the next Done or reorder). The driver phone lists "Times moved: …".
- Rehearse (presenter strip) runs presenter/rehearsal.js: 8 steps, stopwatch excluding pauses, any key pauses, Esc or Stop ends. It asks the agent through ChatPane (dp-agent-ask event, one real model call) and ends with "Rehearsal done in M:SS" plus per-step times. A failed step is named in plain words.
- Checks: scripts/step10_check.py.
- REQ-812: SavedBump.jsx shows a "+$N" ink-on-accent box for 1.5 s on Dispatch when saved_today rises (not on Undo or Reset).

## Step 17 (final pre-publish, Oct 2026)
- Auto-commit wait cut to 5 s, still behind the accept-once lock. remember_base saves the public URL from Google auth start and callback and from /api/live. Pollers run under leases.
- Visible "Dispatch" renamed to "Fleet". Auto actions show "Auto-sent within your rules", linking to /settings#auto-send. The stop chip and the reply say booked or not booked yet.
- Landing "Price a job" opens the Inbox. The Fleet chat starts with a Morning Brief (GET /api/brief). New /research page.
- On /dev, "Fire tricky email" (Lakeshore Dental, 5pm) comes back Needs clarification with 4:15pm offered.
- Reader times out at 15 s and falls back with no AI. Whole read and price is capped at 18 s, then goes to needs_info.
- Demo addresses are pre-geocoded in Mongo geo_cache (GEO_SEED, seeded at startup).
- Startup no longer reseeds automatically. Reset is explicit only.
- Backlog: fill in owner interviews on /research. Decide whether /api/demo/reset needs protection in production.


## Step 22: hands-free demo with the owner's Gmail (Oct 2026)
- Reset preloads a morning, built in `backend/morning.py`:
  - two bookings priced by the engine on stops already on the routes before 10am (routes untouched), plus one held request
  - Activity lines, 2 rules and the phones
- Fleet autoplay (`frontend/.../DemoAutoplay.jsx`, demo session on /dispatch only):
  - the arrival and held toasts, then the booking toast with the earnings line
  - an automatic "why" question in chat (explain_stop now returns added_cost)
  - docked Driver and Customer phones, with sequences queued one at a time
- A "why" chip appears after a live booking. The confirmation now includes the customer_line reason, and outgoing mail is sent as "Bayline Courier".
- Gmail pre-check skips non-requests: no entry, no reply.
- Landing autoplay was shortened to about 33 s (`autoplay.js` SCRIPT, start at 2.6 s).
