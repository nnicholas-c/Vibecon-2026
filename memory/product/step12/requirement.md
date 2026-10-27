# Phase: step12 — Task 6: price visibility, explain fix, polling (user's task text is authoritative)

Version: step12-1. No full tester; E3 runs the CHECK. Don't change the pricing math, insertion or optimizer, or agent.py limits (except the one system-prompt line below).

## Functional requirements
- REQ-900 [always] The system shall seed the demo business with floor_per_run 15, usual_per_run 55, markup 100, leaving cost per hour and per mile unchanged.
- REQ-901 [event] When Reset demo data runs, the system shall apply those seed settings.
- REQ-902 [state] While an option's price is above the floor and below usual, the system shall word customer_line exactly as "Van 2 already passes 1.6 miles from you at 1:22pm, so it's $19 for the run instead of our usual $55." (values from the engine).
- REQ-903 [state] While an option's price is capped at usual, the system shall word customer_line as "Our usual price for this run is $55."
- REQ-904 [always] The system shall keep every other customer-line wording unchanged.
- REQ-905 [event] When explain_stop gets a value that isn't an exact stop key, the system shall fuzzy-match it against that van's stop names today, including stops booked today (case-insensitive substring first, then closest edit distance).
- REQ-906 [always] explain_stop shall return the matched stop's name, position, arrival and window, plus, for booked stops, the added_minutes, added_miles and pass_by line stored at booking.
- REQ-907 [unwanted] If nothing matches, then explain_stop shall return the list of stop names on that van.
- REQ-908 [always] The agent system prompt shall include "If you do not know a stop key, pass the customer name; the tool will match it."
- REQ-909 [state] While document.visibilityState is "visible", the frontend shall poll /api/live every 5 s, and not poll it otherwise.
- REQ-910 [always] The frontend shall not POST /api/import/sync-all (a backend job does it); /api/events stays at 10 s.
- REQ-911 [unwanted] If explain_stop matches no booked or route stop but an open inbox request for that van matches the name or address, then the system shall return that option's added_minutes, added_miles and pass_by, marked "not booked yet". (interpreted, needed for the CHECK when auto-send is off after Reset)

## Quality requirements
Q-900 Tag: Check.Task6
      Scale: after Reset + POST "pickup at 3220 Grand Ave Oakland between 1 and 2pm, drop at 4100 Piedmont Ave by 4pm": two cards with different prices, neither $35; agent reply to "Why is the Grand Ave pickup on Van 2 where it is?" contains added minutes
      Meter: E3 curl script; report both prices and the reply
      Must: pass
      Plan: pass
