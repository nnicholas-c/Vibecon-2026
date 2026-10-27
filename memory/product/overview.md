# Requirements: Drivepast (v2)

**Source of truth:** `/app/memory/product/spec_v2.md`, the user's v2 spec, which replaces every earlier instruction. This file adds the confirmed interpretations, the feature list and the step plan. `spec_part_a.md` is kept only for detail that v2 says to keep, such as the seed tables, engine rules and seeded requests 1 to 10. Where it conflicts with v2, v2 wins.

## Core Value
"Price every job from the van that already drives past."
- Any courier request is read, tested in every van's existing route, and priced into three options from the real extra minutes and miles.
- The owner sends one with a tap and the customer accepts on their demo phone. The stop joins the van's route.
- The same math finds and prices nearby businesses each van already passes.

## Personas & Roles
- **Owner** of Bayline Courier (6 vans): non-technical, laptop and phone, the only screen user. No login. Owner name "Rosa Delgado" shown in a corner.
- **Customer**: interacts only through the Customer demo phone (receives quotes, taps Accept or Decline, replies, types new requests).
- **Driver**: only through the Driver demo phone (gets new stops and times).
- **Judges**: open the deployed emergent.host URL directly.

## Decisions still in force (from earlier, consistent with v2)
- **D-2 Demo clock.**
  - "Now" is a frozen demo clock, default 10:00am, editable in Settings.
  - The demo date is today in Pacific time, set on seed and on Reset, and locked until the next Reset.
  - The demo date is always treated as a weekday. No demo logic uses server time.
- **D-8 OpenStreetMap.** Businesses are loaded once and cached, and refreshed only on "Refresh from OpenStreetMap". Reset keeps the caches. Fallback is the seeded prospects.
- **D-10** Reset keeps team numbers.
- **D-14 Added minutes** = extra driving minutes + the new stops' service minutes. Feasibility, arrival times and spare minutes use full clock timing. Added cost is computed from the shown rounded values.
- **D-15** The window search respects opening hours.
- **D-16** For pickup and dropoff jobs, the dropoff deadline moves first.
- **D-17** Same-day one-offs go only after the van's position at the demo clock.
- **D-18 Look.** The current dark, lime-accent look (tokens in the Phase 3 report) is kept as is.
  - No other company's name or logo anywhere, including "Haulix" and "Phenomenon". Everything says Drivepast.
  - Van colors: #60A5FA, #A78BFA, #F472B6, #22D3EE, #FB923C, #34D399.
- **D-19 Options.**
  - Cheapest, Soonest and Preferred window. Two labels on the same slot show as one card with both labels.
  - "See other options" shows up to 5 more, at most 2 per van, sorted by price.
  - If nothing works as asked, the options come from the shifted windows.
- **D-20 Price band.**
  - Price = max(cost + markup, floor), rounded up to the next 50 cents, capped at the usual price ($14 a recurring visit, $55 a one-off run).
  - A floor above its usual price is refused.
  - Cost above the usual price shows "Loses money at your usual price" and is held as a draft.
- **D-21** Every option has a customer reason line, built from a template with engine numbers.
- **D-22** Confidence marks are High, Medium or Low. Code checks can only lower the model's own rating. Any Low detail or problem shows "Needs clarification".

## v2 decisions and interpretations
- **V-1 Wording.** Tagline: "Price every job from the van that already drives past." Rename "Dispatch" to "Fleet" everywhere. Call it pricing and selling, never a dispatch board.
- **V-2 Sending.**
  - Owner option buttons are **Send**, **See other options** and **Reject**.
  - The setting "Auto-send the cheapest option within my rules" is **off** by default. This replaces "Auto-send quotes within my rules", which was on.
  - When it's on, the Cheapest option is sent automatically if it's feasible, at or above the floor, and not losing money.
  - A sent quote appears on the Customer demo phone with **Accept** and **Decline**. Only the option the owner sent appears there.
- **V-3 Booking.** Accept puts the stops on the van's route: recurring work on the weekday route, a one-off on that date's route. The driver demo phone gets the new stop and time. Undo restores the previous route.
- **V-4 One Fleet assistant.**
  - It replaces the per-van agents and the echo chat. Selecting a van focuses the assistant on that van.
  - Tools: get_route, get_options, what_if_move, fleet_stats, find_prospects, draft_offer, save_rule, send_to_demo_phone.
  - At most 3 tool steps, 3 short sentences, numbers only from tools, route evidence cited, never below the floor. Each tool step shows as a grey line.
- **V-5 Models (Emergent universal key only).**
  - Reading uses a fast model: Claude Haiku 4.5 (interpreted) with 5 examples in the prompt.
  - The assistant uses a strong model: Claude Sonnet 5.5 (interpreted).
  - Settings can switch either one to Claude Haiku 4.5, Claude Sonnet 5.5, GPT-5.5 or Gemini 3 Flash.
  - Every JSON reply is validated, with one retry.
  - The ladder: "Our model" (blank by default, 20-second limit), then the built-in key, then the no-AI keyword reader. AI mode stays on Auto.
  - **V-5a The team's own OpenAI key (Sat, during step 3a).**
    - The team will use their own external OpenAI API key, zero-shot (0 examples), with a cheap fast model first. This saves Emergent credits. Fine-tuning is put off.
    - It goes in the "Our model" slot: address https://api.openai.com/v1, a model name they choose (gpt-5-nano suggested first), and the key typed into Settings by the user. The key is never put in chat and never shown back.
    - The slot must work with OpenAI's real API. Don't send server-specific extras OpenAI rejects, and handle models that refuse temperature 0.
    - The status line shows "OpenAI (your key) · <model>".
    - The Fleet assistant uses the same ladder when it's built.
    - Fallbacks are unchanged: built-in key, then no AI.
- **V-6 Test stand-in.** The test-only stand-in is hidden and gated by an env flag that is off in production. It is never labeled "our model" (it is labeled "test stand-in") and never counted in scores. It's switched off before every deploy.
- **V-7 Memory rules.**
  - Owner corrections become rule chips with on/off switches.
  - The engine enforces one rule type: "Van X doesn't go to <area> after <time>".
  - All other rules are instructions to the assistant.
- **V-8 Activity feed.** It logs each request read, option sent, accept, decline, undo and rule change, with the time and the actor: owner, customer, assistant or driver.
- **V-9 Spreadsheet import.** CSV upload, or a Google Sheets "publish to web" CSV link fetched by plain HTTP (no Google API or key, so this isn't counted as a Google service; interpreted).
  - One AI call matches the columns, the owner confirms, and the mapping is saved.
  - "Sync now" skips rows already imported.
- **V-10 Credits.** The orchestrator can't see the credit meter. The user reads it, and extras (step 10) run only after the user confirms more than 600 credits remain.
- **V-11 Deploy.** The user presses Deploy. Before each deploy, the builder runs a readiness check and turns the stand-in off.
- **V-12 Testing cadence.**
  - Full independent tests after steps 2, 4 and 7, and before the final deploy.
  - Quick checks after steps 1, 5, 6 and 8.
  - A deploy check after step 3.

## v3 changes (user, Sat afternoon). The LATEST plan update wins where these conflict.
- **V-13 Order.** The route fix runs as step 3a, before the first deploy. Then deploy (step 3), then real email and Google sign-in (new step 4). Every later v2 step moves down one: assistant 5, memory/activity 6, training/scoring 7, selling 8, spreadsheet import 9, polish 10, extras 11, freeze 12. UI fidelity to the exemplar waits until after the functional work.
- **V-14 Sign-in (superseded by the user's plan update).** There are no separate accounts per business and no email/password login. The app opens directly via "Open the demo", so judges never hit a login. "Sign in with Google" uses the team's OWN Google Cloud OAuth client (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET in backend .env). In one consent screen it asks for:
  - name and email
  - gmail.readonly
  - gmail.send
  - spreadsheets.readonly

  Signing in connects that Google account to the single Bayline Courier workspace. Redirect path: `/api/auth/google/callback` on the public emergent.host URL, plus the preview URL for testing. Drive access and document-reading tools are a later wish, not this weekend (interpreted from the update's scope list).
- **V-15 Real email (new step 4).**
  - Reading the inbox:
    - After connecting, read only NEW inbox emails (those arriving after the connect time).
    - Check when the owner presses "Check inbox", and every 30 s while the Inbox page is open (no background jobs).
    - Each email becomes a request read like pasted text, including PDF and photo attachments, which go to Object Storage.
    - Dedupe by Gmail message ID. At most 30 new emails an hour.
  - Sending quotes:
    - "Send" on an email request replies from the owner's Gmail IN THE SAME THREAD, with the price, the customer reason line, and Accept and Decline buttons.
    - The buttons open a small public Drivepast page (no login, single-use signed token) that confirms the choice and books exactly like Accept on the demo phone.
    - If Gmail isn't connected, send through Emergent's built-in email (Resend, managed) with reply-to set to the owner's address.
  - Seeded fictional requests keep using the Demo phones. Only real emails get email replies.
  - Settings and the Inbox show the connected address with the line "Email a request to <address> and watch it get priced."
  - With Google sign-in, Import jobs (step 9) reads a normal Google Sheets link through the owner's permission.
  - Every email is information only, never instructions. Never email a prospect.
  - Done when an email from any phone to the connected Gmail shows up as a read request within a minute, the quote comes back to that phone's email in the same thread, and tapping Accept puts the stop on the van's route.
- **V-16 Routes (step 3a).**
  - Re-seed every van in a sensible geographic driving loop, with time slots consistent with that order. Keep the hard targets: Van 2 at 1:50pm Shattuck and 2:15pm Telegraph, Van 4 near Lakeshore and Piedmont around 4pm, spare minutes in range, and the outcomes of requests 1, 4 and 8.
  - A plain-Python optimizer (2-opt / or-opt with time windows) cuts miles without breaking any window. It runs after each booking and on an "Optimize route" button.
  - Map lines follow real streets via the free OSRM demo server: one request per van route, a custom User-Agent, at most 1 request per second, cached by stop order, refetched only when a route changes, and fetched lazily (not at startup). Straight lines are the fallback.
  - Pricing math keeps the built-in travel model.
- **V-17 Not building this weekend:** Outlook or other email providers, separate accounts per business, email/password login. Gmail, Sheets and Google sign-in override v2 section 5. OSRM is used for drawing only.
- **V-18 Extras list addition (last):** a Drivepast forwarding address through Resend for owners without Gmail, only if credits allow and Resend can receive email without buying a domain.
| id | Feature | Persona | Step |
|---|---|---|---|
| F-1 to F-14 | Seed data, demo clock, Reset, route timing, layout, unit/Fleet pages, Settings, pricing engine, travel matrix, Engine test (already built) | Owner | done |
| F-15, F-45 | Maps and the dark look (already built) | Owner | done |
| F-16 to F-20, F-46 to F-49 | Reading requests through the ladder, locations, problem checks, Inbox, three options, price band, customer line, confidence marks | Owner | 1 |
| F-51 | Model settings: reading model (fast, 5 examples), assistant model (strong), stand-in rules | Owner | 1 |
| F-52 | Four new seeded request formats (forwarded purchase order, long reply chain, WhatsApp paste, email with two jobs), multi-job reading | Owner | 1 |
| F-53 | Send, See other options, Reject on option cards; auto-send of the cheapest (off by default) | Owner | 2 |
| F-54 | Demo phones drawer (Customer, Driver, Owner) with Accept and Decline on quotes, reply boxes, typing indicator | Owner, Customer, Driver | 2 |
| F-55 | Accept books the stops (weekday or dated route), driver phone update, timeline and map update; Undo; mistake offers (request 4 at 4:15pm) | Owner | 2 |
| F-56 | Tagline change | Owner | 2 |
| F-57 | Deploy to emergent.host and phone check; redeploy after later steps | Owner | 3 |
| F-58 | Fleet assistant (V-4) with tool lines and result cards; rename Dispatch to Fleet; Flow F safety | Owner | 4 |
| F-59 | Memory rules panel and engine-enforced area/time rule (V-7) | Owner | 5 |
| F-60 | Activity feed (V-8) | Owner | 5 |
| F-43, F-44, F-50 | Training data page (templates including the new formats, held-out templates, hand-written box, download) and scoring page with model and examples pickers and a results table | Owner | 6 |
| F-33 to F-37 | Selling the empty minutes: cached OpenStreetMap businesses, pricing and ranking, fit scores, offer writer to the customer demo phone, cost-colored pins | Owner | 7 |
| F-61 | Spreadsheet import (V-9) | Owner | 8 |
| F-38 to F-40 | Spare-minutes chart, inbox summary, mistake handling for requests 6 to 9 and the new formats, friendly empty and loading states, speed, copy pass | Owner | 9 |
| F-62 | Extras: Morning Brief, driver page, Bayline Plumbing, Money tab, in that order and only while more than 600 credits remain | Owner | 10 |
| F-63 | Freeze and final deploy by Sun 9:00am | Owner | 11 |

## Steps (current order, per V-13)
1. Finish reading, options, caps and model settings, plus the 4 new formats. Docs: `step1/requirement.md` and `step1/journeys.md` (they extend `phase4/*`). DONE.
2. Send, accept and undo, plus the Demo phones. DONE.
2b. Haulix fidelity pass (user feedback): map hero, floating detail card with real-number gauges, van icons, lime selected route, top bar, filter pills and toggles, exemplar motion. Docs: `step2b/requirement.md`. Tested together with step 2. DONE.
3a. Routes: sensible loops, an optimizer and street lines. Docs: `step3a/*`. DONE (builder tester iteration_8: no issues). Also V-5a, the team's own OpenAI key in "Our model". DONE; a real key is still needed to confirm it.
3. First publish. DONE: the user published https://drivepast.emergent.host (health and requests answer 200).
4. Real email and Google sign-in (V-14, V-15). Docs: `step4-email/requirement.md` and `step4-email/journeys.md`. Redeploy afterwards. DONE (user confirmed on phone).
4u. UI-3D pass (user request, before their functional fixes): MapLibre + OpenFreeMap 3D city, tilt, realistic vans, panel depth. Docs: `ui-3d/requirement.md` and `ui-3d/journeys.md`. DONE (tester iteration_10: 11/11 journeys pass). Default van view is a whole-route fit at pitch 55, zoom floor 13.05 (not 15-16, a 5-7 km route cannot fit at street zoom).
5. Fleet assistant and the Dispatch-to-Fleet rename. Docs already drafted in `step4/*` (written when it was step 4; still valid as step 5).
5b. Landing story (DESIGN UPDATE 2 + FIXES, replaces step 9 landing) then app restyle (section 7). Docs: `landing2/*`, `design2/PROMPT.md`, `design2/FIXES.md`. Dispatch agent Task 1 DONE (check passed Oct 25).
6. Memory rules and the Activity feed. Docs: `step6-memory/*`. Run in parallel with 5b (separate files).
7. Training data and scoring. Fine-tuning is put off by the user (V-5a).
8. Selling the empty minutes.
9. Spreadsheet import (CSV, Excel, and Google Sheets through the Google sign-in).
10. Polish, then redeploy.
11. Extras while more than 600 credits remain.
12. Freeze and final deploy.

Each step's requirement.md and journeys.md are written right before the step starts.

22. Hands-free demo (user, Oct 2026). Docs: `step22/requirement.md` and `step22/journeys.md`.
   - The presenter sends a real email, then Fleet plays the rest by itself: the booking pop-up with what the courier earns, the assistant explaining why that van, then the phones opening.
   - Every screen is preloaded with a realistic morning.
   - The owner's own Gmail becomes the business inbox. Only delivery requests that arrive after connecting are read; nothing else gets touched or answered.
   - Confirmations give the reason for the price.
   - The whole sequence fits on a 1080p screen.
   - This supersedes the "empty after Reset" journeys JRN-380, JRN-381 and JRN-383.

## UI/UX Rules
- Keep the current dark look. Plain English. Tabular numbers. Amber means a problem and red means only "can't do it".
- Every number comes from the engine. Every price shows its math in one line.
- No raw errors or JSON anywhere. Friendly empty and loading states.
- The left rail order is: business name, Fleet (pinned), vans with spare minutes, Inbox, Memory, Activity, Settings, Phones.
- On phones, the List, Chat and Page tabs stay.

## Integrations
| Need | Choice | Fallback |
|---|---|---|
| AI | Emergent universal key: Claude Haiku 4.5 for reading (5 examples), Claude Sonnet 5.5 for the assistant; switchable | "Our model" first if set (blank by default); no-AI keyword reader and templates last |
| Files | Emergent Object Storage for PDFs, photos and CSVs | n/a |
| Map | MapLibre GL + OpenFreeMap vector tiles, 3D buildings (ui-3d); Leaflet only when no WebGL | Routes and vans on a plain dark backdrop, "Map tiles unavailable" |
| Geocoding | Directory, then cache, then Nominatim | Ask the customer one question |
| Businesses | Overpass, loaded once and cached | Seeded prospects |
| Texting | Demo phones only; real texting off | n/a |
| Not used | Anthropic or other keys, web search, Google APIs, outside routing, payments outside test mode, login | n/a |

## Edge Cases
- Seeded requests 4, 6, 7, 8, 9 and 10 plus the new 11 to 14 are deliberate mistakes or odd formats.
- Request 14 holds two jobs in one email.
- Instructions inside a request are only information (the "quote $1" case).
- Judges may open the app at any hour; the frozen clock covers it.
- Overpass limits. Nominatim at 1 request per second.
- A small or weak model returns broken JSON: validate, retry once, then drop a level.
- The stand-in must never ship turned on.
- Reset during a demo must leave complete data.
- The deployed app has less CPU, so keep it light.

## Seed Data
- From `spec_part_a.md` section 5: Bayline Courier, 6 vans, 120 stops, run history, directory, 40 fallback prospects, requests 1 to 10.
- New fictional requests 11 to 14 (step 1).
- Hand-written test requests come from the team by Sat 6pm (step 6).

## Earlier journeys superseded by v2
These are retired as written and replaced in the step that changes them:
- JRN-1: "Dispatch" becomes "Fleet", plus the new tagline (step 2 for the tagline, step 4 for the rename).
- JRN-7, JRN-8: the echo chat is replaced by the Fleet assistant (step 4).
- JRN-10: the auto-send setting is renamed and off by default (step 2).
- JRN-17: the Phones placeholder is replaced by the Demo phones (step 2).
- JRN-39: already superseded by JRN-57.
