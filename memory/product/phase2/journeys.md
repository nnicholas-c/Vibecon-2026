# Phase 2 journeys

All Phase 1 journeys (JRN-1 to JRN-23) stay valid. Each journey starts from a fresh "Reset demo data" with the demo clock at 10:00am unless it says otherwise. Times are Pacific.

- **JRN-24** Engine test lists the seeded requests
  - steps: Open Settings, then "Engine test".
  - expected: All 10 seeded requests are listed, each with a one-line summary of its structured job (pickups, dropoffs, window, frequency). Requests 6 and 7 show "Can't price yet" with a plain reason (missing delivery addresses; the city for Broadway and Mission St is unclear). No route changes on the unit pages.

- **JRN-25** Request 1 wins on Van 2 for a few dollars
  - steps: Press "Run all" and open request 1.
  - expected:
    - Van 2 is highlighted as the winner. It is feasible, with the pickup at 5200 Shattuck placed after the 1:50pm stop and the dropoff at Ashby Medical Center after it.
    - Added minutes are about 7 to 11 (extra driving plus 2 x 4 stop minutes) and added cost is under $4.
    - The price is $11 a visit, $231 a month.
    - The line reads "Adds N min and M mi to Van 2, which costs $X. Your floor is $11, so the quote is $11 a visit, or $231 a month."
    - The pass-by line names a Van 2 stop and its time, like "Van 2 stops at 5100 Shattuck at 1:50pm, 0.1 miles from you."
    - Every other van shows either a higher cost or a plain-words reason.

- **JRN-26** Hand check of the cost
  - steps: Read request 1's winner minutes, miles and cost, and the hand-check formula.
  - expected: Shown minutes x ($19.27 / 60) + shown miles x $0.76 equals the shown cost within 1 cent. The formula line shows those exact numbers.

- **JRN-27** Request 2, same-day one-off
  - steps: Open request 2's result.
  - expected:
    - A van is the winner, with the pickup at 1300 Clay St before the dropoff at Fallon St and 12th St, and the dropoff arriving by 3:00pm.
    - New stops sit after the van's 10:00am position.
    - The price is at least $35 for the run.
    - "A typical on-demand run in the Bay Area is $45 to $65." is shown.
    - No monthly total is shown.

- **JRN-28** Request 3, specific weekdays
  - steps: Open request 3's result.
  - expected: The winner is a San Francisco van (Van 5 or Van 6) (interpreted). The price is at least $11 a visit. The monthly total equals price x 4.3 x 2 (Mondays and Thursdays), and the line says so.

- **JRN-29** Request 4 asks for 5pm but Lakeshore Dental closes at 4:30
  - steps: Open request 4's result.
  - expected: As asked (5pm pickup), every van is infeasible with a plain reason such as "past shift end". The working shifted window is a 4:15pm pickup on Van 4, with its added cost and price. No option with a pickup at or after 4:30pm is offered.

- **JRN-30** Request 5, several stops
  - steps: Open request 5's result.
  - expected:
    - The four pickups (4100 Piedmont Ave, 5600 College Ave, 3100 Telegraph Ave, 2900 College Ave) and the dropoff at Emeryville Central Lab are inserted in that order on the winning van.
    - Each pickup arrives between 3:00 and 4:00pm and the dropoff by 5:00pm.
    - Totals for minutes, miles and cost are shown, with a price of at least $11 a visit and a monthly total.
    - Or, if no van can take it, each van shows a plain reason and a shifted window is reported.

- **JRN-31** Request 8, impossible window
  - steps: Open request 8's result.
  - expected: As asked (pickup 8:00am in Berkeley, deliver to Mission Bay by 8:15am), every van is infeasible with a plain reason such as "can't reach it in time". A later delivery time that works is reported (within 2 hours), with its van and added cost.

- **JRN-32** Requests 9 and 10
  - steps: Open requests 9 and 10.
  - expected: Request 9 prices exactly like request 1 (same winner, minutes, miles, cost, price); duplicate detection is not in this phase. Request 10 prices a daily 11:30 pickup at Elmwood Pharmacy (2900 College Ave), with its drop locations on Solano Ave marked as approximate.

- **JRN-33** Fast enough
  - steps: Press "Run all" three times.
  - expected: Every priceable request except request 5 shows an engine time under 500 ms on each run. Request 5 shows under 1000 ms.

- **JRN-34** Plain-words reasons only
  - steps: Look at every infeasible van row across all 10 requests.
  - expected: Each reason is one of "the window has already passed", "can't reach it in time", "past shift end", "no room" or "missing skill", with where the van is and until when. No codes, blanks, "NaN" or JSON.

- **JRN-35** What-if move
  - steps: In Engine test, use the what-if control to move one of Van 1's stops to Van 2. Then refresh and open Van 1.
  - expected: Both vans' changes are shown (minutes, miles, cost; Van 1 lower, Van 2 higher), or a plain reason if Van 2 can't take it. After the refresh, Van 1 still has the stop and its stop count is unchanged.

- **JRN-36** Accept a priced option
  - steps: Through the API, accept request 1's winning option on Van 2. Open Van 2 and Dispatch.
  - expected:
    - Van 2 shows 22 stops, with Temescal Diagnostics Lab (5200 Shattuck) at about 1:52 to 1:58pm and Ashby Medical Center after it, each marked as starting next Monday if a start date was set.
    - Spare minutes are updated, and the same in the rail, header and Dispatch table.
    - A previous plan for Van 2 is saved.

- **JRN-37** Undo
  - steps: After JRN-36, call undo. Then call undo again.
  - expected: After the first undo, Van 2 shows 20 stops with the same stops and arrival times as before JRN-36. The second undo returns "Nothing to undo" and changes nothing.

- **JRN-38** Stale accept is refused
  - steps: Price request 1 and keep the option. Accept a different job that takes the same slot on Van 2. Then accept the kept option.
  - expected: The kept option is refused with "This slot is no longer free. Price it again." and Van 2 is unchanged by that call.

- **JRN-39** Settings drive the price
  - steps: Set floor per recurring visit to $15 and save. Run request 1. Then set the wage to $40 and run it again.
  - expected:
    - With the $15 floor, request 1 quotes $15 a visit, $315 a month.
    - With a $40 wage, the added cost rises and the hand check uses $40 / 60.
    - No price is ever below the floor in force.

- **JRN-40** Speed change rebuilds the matrix
  - steps: Note request 1's added minutes on Van 2. Set the East Bay speed to 15 mph and save. Run request 1 again.
  - expected: Added minutes (the driving part) and the new stops' arrival times change. Van 2's spare minutes in the rail match the recomputed route.

- **JRN-41** Same-day window already passed
  - steps: Set the demo clock to 4:00pm and save. Run request 2 ("by 3"). Then set the clock back to 10:00am.
  - expected: At 4:00pm every van shows "the window has already passed". At 10:00am request 2 is feasible again, as in JRN-27.

- **JRN-42** Fleet and unit stats
  - steps: Call fleet stats and unit stats for Van 6 through the API.
  - expected:
    - Each unit has stops, spare minutes today, spare minutes Monday to Friday plus the week's total, revenue per day, cost per stop, on-time rate, morning and afternoon on-time rates, late-run count and average minutes late.
    - Van 6 has the lowest afternoon on-time rate and the most late runs.
    - Stops, spare minutes, revenue and cost per stop match the unit pages and the Dispatch table.

- **JRN-43** Bad job input
  - steps: Through the API, price a job with no stops, then a job whose window ends before it starts.
  - expected: Each returns a plain-words error and no price. Nothing in the app shows a raw error.
