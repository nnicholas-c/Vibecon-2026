# Phase: step13 — Far-van demo email, booked/pending label, sheet sync status, booking timer

Version: step13-1. Small polish. No tester, no full suites; quick targeted checks only. Don't change the pricing math, insertion or optimizer, or agent.py limits/model config.

## Functional requirements
- REQ-950 [always] The system shall use, for the scripted demo email (POST /api/demo/scripted-email, Run the demo, Rehearse), a real seeded-area address whose two option cards are on different vans with a clear price gap. The nearby van should be Van 2 if the engine honestly allows (about $15 to $22), and the far van should be about $45 to $55, all from the engine with current Settings. (interpreted: pick the address by searching candidates, never by forcing prices)
- REQ-951 [unwanted] If no candidate gives two different vans with a gap of at least $20, then the system shall keep the current Hollis email and report the best gap found.
- REQ-952 [always] The system shall keep the scripted email's wording style (pickup, drop-off, deadline, sender Ana) and update the presenter copy and test notes to the new address and toast.
- REQ-953 [event] When the assistant calls explain_stop, the system shall show beside that tool line in the chat a small square label "Booked" or "Not booked yet" with the matched stop name, from the tool result (booked_today / not-booked-yet fallback). Route stops from the seed show "On today's route". (interpreted)
- REQ-954 [always] The system shall keep the chat layout otherwise unchanged.
- REQ-955 [always] The system shall show on the Import page the time and result of the last automatic sheet sync, e.g. "Last synced 2:14pm: 1 new, 5 skipped", or the plain error text "We couldn't read that sheet. Check the link or the file." if the last sync failed.
- REQ-956 [state] While no sheet is connected, the system shall show "No sheet connected" instead.
- REQ-957 [event] When a request becomes Booked, the system shall store booked_seconds = booked time minus arrival time (Gmail internalDate for Gmail requests, else received_at).
- REQ-958 [always] The system shall show "Booked in N s" (or "Booked in M min S s" over 60 s) on the booked request's inbox row and detail.
- REQ-959 [state] While a request isn't booked, the system shall show no timer.

## Quality requirements
Q-950 Tag: Demo.PriceGap
      Scale: dollar gap between the scripted email's two cards
      Meter: POST /api/demo/run then /api/demo/scripted-email (auto-send off for the card check)
      Must: 20
      Plan: 30
Q-951 Tag: Timer.Truth
      Scale: seconds difference between booked_seconds and (booked_at - arrival)
      Meter: script on one scripted booking
      Must: 1
      Plan: 0
