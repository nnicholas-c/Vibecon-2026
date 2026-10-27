# Phase: step7 — The one demo: 3-van fleet, email-to-booking flow, spreadsheet import, presenter mode

Goal: make the vision's 60-90 s demo work end to end and be easy to present: email or sheet in, parsed and priced with no clicks, quote out, customer taps Accept, route redraws with a New stop and a "Booked ..." toast, agent explains it, driver and customer phones visible side by side.

Version: step7-1. North star: the user's Vision doc (saved in `/app/memory/product/vision.md`). Dropped by the user: training/scoring pages, prospect pins/offers, van tiles. Don't change the Dispatch assistant config/limits (agent.py), pricing math, or Gmail/sign-in plumbing beyond what's listed.

User decisions (Oct 25): booking happens only after the customer taps Accept. Cut the demo fleet to 3 vans everywhere. Sheets come in through the existing Google sign-in, checked automatically like Gmail, plus CSV upload. Build the toast, the New tag and side-by-side phones. Make the demo automated and easy to present.

## Part 1 — Three-van fleet
- REQ-600 [always] The system shall seed the demo fleet as 3 vans (Van 1, Van 2, Van 3, keeping Van 2 "Emeryville labs" and its drivers/colors) with their stops, run history and routes; Vans 4-6 and their stops are removed. (interpreted: keep Vans 1-3)
- REQ-601 [always] The system shall keep the 14 seeded requests valid against 3 vans, re-pointing any that named Van 4-6. (interpreted)
- REQ-602 [event] When Reset demo data runs, the system shall rebuild the 3-van fleet.
- REQ-603 [always] The system shall show only Vans 1-3 on the landing scene, and update the landing copy and loader counts to match ("Three vans, N stops, one afternoon.", "Vans 3", "Stops today N" with N counted from fleet.json for those vans; panel 01 tag "3 vans"). (interpreted — overrides PROMPT.md word-for-word copy because the user chose 3 vans everywhere)
- REQ-604 [unwanted] If an assistant question names Van 4, 5 or 6, then the system shall answer that there is no such van.

## Part 2 — Email to quote with no clicks
- REQ-610 [event] When a new email arrives in the connected Gmail, the system shall have it in the Inbox read and priced within 30 seconds while the app is open (existing 30 s Gmail check).
- REQ-611 [event] When a new request lands, the system shall tick the Inbox badge up.
- REQ-612 [state] While Demo mode is on, the system shall auto-send the cheapest option within the rules (auto_send_cheapest on), replying in the email thread when the request came from Gmail.
- REQ-613 [unwanted] If the request needs clarification or would lose money, then the system shall hold it for the owner with the amber flag instead of auto-sending.

## Part 3 — Accept, live route update, toast, New tag
- REQ-620 [event] When the customer taps Accept (email link or Customer demo phone), the system shall book the stop onto the chosen van's route (existing booking logic).
- REQ-621 [event] When a booking happens, the system shall redraw that van's route on the open Dispatch map within 3 seconds with the new stop highlighted in the accent.
- REQ-622 [event] When a booking happens, the system shall show a toast on the owner screen: "Booked <street or customer>, $<price> instead of $<usual>. <Van> already passes <d> mi away." with every number from the engine.
- REQ-623 [always] The system shall tag a newly booked stop "New" in that van's stop list, timed between its neighbours, until Reset demo data.
- REQ-624 [unwanted] If the booking fails (window no longer fits), then the system shall show "Couldn't add that stop. The route changed. Try another option." and leave the route unchanged.

## Part 4 — Phones side by side
- REQ-630 [always] The system shall offer a presenter layout showing the Driver phone (ordered stop list with the new stop and time) and the Customer phone (the quote message with the price cut and Accept / Decline) side by side on the same screen as the Dispatch map. (interpreted)

## Part 5 — Spreadsheet import
- REQ-640 [always] The system shall offer "Import jobs" in the Inbox with two sources: a Google Sheet picked/linked through the existing Google sign-in, and a CSV upload.
- REQ-641 [event] When a sheet is first loaded, the system shall make one AI call to match its columns to request fields and show the match for the owner to confirm.
- REQ-642 [unwanted] If the AI match fails, then the system shall pre-fill the match by header keywords.
- REQ-643 [event] When the owner confirms, the system shall save the mapping and import each row as an Inbox request read and priced like an email.
- REQ-644 [state] While a Google Sheet is connected and the app is open, the system shall check it for new rows every 30 seconds, like Gmail.
- REQ-645 [event] When "Sync now" is clicked, the system shall import new rows and skip rows already imported, showing "Imported N new, skipped M already imported".
- REQ-646 [unwanted] If the sheet can't be read, then the system shall show "We couldn't read that sheet. Check the link or the file."
- REQ-647 [always] The system shall store uploaded CSVs in Emergent Object Storage.

## Part 6 — Presenter mode (automated demo)
- REQ-650 [event] When the owner clicks "Run the demo", the system shall reset demo data, open the Dispatch page in the presenter layout, and turn Demo mode on.
- REQ-651 [event] When the demo runs and no real email arrives within the first step, the system shall inject the scripted demo request (pickup, drop-off, deadline, e.g. Clay Street) through the same reading path as Gmail, so the demo never depends on Gmail being up. (interpreted)
- REQ-652 [always] The system shall let the presenter choose between sending a real email (shows the Gmail address to send to) and "Use the scripted email".
- REQ-653 [event] When the quote reaches the Customer phone, the system shall wait for the presenter to tap Accept, with an optional "Auto-accept after 5 s" switch that taps it visibly. (interpreted)
- REQ-654 [event] When the booking shows, the system shall open the van page with the New stop and pre-fill the agent panel with "Why did the new stop go there?" for the presenter to send.
- REQ-655 [always] The system shall show a small presenter strip listing the steps with the current one marked, plus "Next" and "Reset demo".
- REQ-656 [always] The system shall keep the Dispatch page to the map with 3 vans, their routes and one stat strip, with the presenter strip and phones only in presenter layout. (interpreted)

## Quality requirements
Q-600 Tag: Demo.Latency
      Scale: seconds from email sent (or scripted inject) to priced request in Inbox
      Meter: stopwatch, 3 trials
      Must: 30
      Plan: 15
Q-601 Tag: Demo.Booking
      Scale: seconds from Accept tap to redrawn route + toast
      Meter: stopwatch, 3 trials
      Must: 3
      Plan: 1.5
Q-602 Tag: Demo.Reliability
      Scale: failed full presenter runs out of 5 (scripted email path)
      Meter: human
      Must: 0
      Plan: 0
Q-603 Tag: Price.Truth
      Scale: toast/quote numbers not equal to the engine option
      Meter: compare with option card
      Must: 0
      Plan: 0
Q-604 Tag: Import.Duplicates
      Scale: duplicate requests after repeat syncs of an unchanged sheet
      Meter: API, 5-row sheet, 3 syncs
      Must: 0
      Plan: 0
