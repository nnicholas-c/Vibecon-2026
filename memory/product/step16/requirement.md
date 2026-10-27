# Phase: step16 — Task 9: demo reset and freeze (user's task text is authoritative)

Version: step16-1. No tester, no full suites; quick targeted checks plus one scripted two-tab browser CHECK by the builder. Don't change pricing math, insertion, optimizer or agent.py limits/model.

## Functional requirements
- REQ-1100 [event] When Reset demo data runs, the system shall produce exactly 3 vans with 8 stops each, every stop before the demo clock marked Done, demo clock 10:00am, zero inbox requests, zero events, zero rules, auto-send on, floor 15 and usual 55.
- REQ-1101 [always] The system shall keep the 8 stops per van as a subset of today's seeded addresses, spread across the shift (no idle gap over 30 min where possible), with Van 2 still passing the Telegraph Ave, Racine St and Grand Ave areas so the demo requests honestly price low on a nearby van. (interpreted)
- REQ-1102 [state] While right after a Reset, the Dispatch stat strip shall show "New stops 0" and "Saved customers $0".
- REQ-1103 [always] The Dispatch stat strip shall include a "New stops N" value counting stops booked today. (interpreted: new stat needed by the CHECK)
- REQ-1104 [always] The system shall hide the Rehearse/presenter step bar by default, with its on/off toggle only on /dev.
- REQ-1105 [state] While demo mode is on, the system shall not show the step bar unless it was turned on from /dev. (interpreted)
- REQ-1106 [event] When a booking event (kind "booked") arrives, the system shall show a toast bottom-right for 8 s with the event text (keeping the price ruler), flash the booked van's row in the table, and scale that van's new map pins to 1.4 for 3 s.
- REQ-1107 [always] The system shall show exactly one toast per booking, from whichever poll (/api/live every 5 s or /api/events every 10 s) sees it first. (interpreted, so the CHECK fits in 30 s)
- REQ-1108 [event] When "Open the demo" is clicked (the new landing masthead button, the sign-in screen and the About page), the system shall run Reset demo data first, then route to /dispatch.
- REQ-1109 [always] The landing masthead shall show a secondary "Open the demo" button next to "Price a job". (interpreted: the landing had no "Open the demo" button, and the CHECK needs one)
- REQ-1110 [always] The system shall serve a /dev page (not linked in the nav) with "Fire demo email" and the step-bar toggle.
- REQ-1111 [event] When "Fire demo email" is clicked, the system shall insert the Grand Ave request ("pickup at 3220 Grand Ave Oakland between 1 and 2pm, drop at 4100 Piedmont Ave by 4pm") as if from Gmail (source gmail, sender dana@grandlakeoptometry.example) through the same ingest path, so it's read, priced, quoted, and auto-committed after the 20 s window.
- REQ-1112 [always] The system shall never send real email to dana@grandlakeoptometry.example (the confirmation goes to the Customer demo phone). (interpreted)

## Quality requirements
Q-1100 Tag: Check.Task9
      Scale: seconds from clicking "Fire demo email" on /dev (tab 2) to the dispatch tab (tab 1, opened via landing "Open the demo") showing the toast, the van flash, "New stops 1" and a non-zero "Saved customers", with no clicks on tab 1
      Meter: builder's scripted two-tab browser run; report elapsed
      Must: 30
      Plan: 27
Q-1101 Tag: Reset.Exact
      Scale: deviations from REQ-1100 counts after Reset
      Meter: API script
      Must: 0
      Plan: 0
