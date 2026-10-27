# Journeys: step16

superseded: the seed of 20 stops per van and the 14 seeded inbox requests; "Reset turns auto-send off"; the presenter step bar showing by default on /present; the landing's one-button masthead.

- JRN-380 steps: Reset demo data, then check the APIs. expected: 3 vans, 8 stops each, stops before 10:00am Done, clock 10:00am, 0 requests, 0 events, 0 rules, auto-send on, floor 15, usual 55.
- JRN-381 steps: open /dispatch after Reset. expected: "New stops 0" and "Saved customers $0"; no step bar.
- JRN-382 steps: open "/" and click "Open the demo". expected: Reset runs, then /dispatch opens clean.
- JRN-383 steps: in a second tab open /dev and click "Fire demo email". expected: within 30 s, with no clicks on the dispatch tab: a bottom-right toast for 8 s with the Booked text, the booked van's row flashes, its new pins scale up for 3 s, "New stops 1", and "Saved customers" non-zero.
- JRN-384 steps: on /dev toggle the step bar on, open /present. expected: the step bar shows; toggling it off hides it.
- JRN-385 steps: open the Customer demo phone after the booking. expected: the confirmation message; no real email to the example address.
