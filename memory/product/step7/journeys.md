# Journeys: step7

superseded: any earlier journey asserting 6 vans (rail rows, fleet table, landing "Six vans, thirty stops", loader "Vans 6 / Stops today 30", requests offering Vans 4-6), and step6 JRN-183 "Van 1 to SF" stays valid. Training/scoring/prospect/van-tile journeys from the earlier draft are dropped.

- JRN-210 steps: Reset demo data, open Dispatch. expected: 3 vans in the rail, map and table; routes drawn; one stat strip.
- JRN-211 steps: open "/". expected: only 3 vans drive; panel 01 reads "Three vans, N stops, one afternoon." with tag "3 vans"; loader shows Vans 3; Van 2 chapters still end at $11 a visit, usually $14.
- JRN-212 steps: ask the assistant "What is Van 5 doing?". expected: it says there's no Van 5.
- JRN-213 steps: send a real email with a pickup, a drop-off and a deadline to the connected Gmail with the app open and Demo mode on. expected: within 30 s, with no clicks, the Inbox badge ticks up, the request is parsed and priced, and the quote is sent (status Quoted).
- JRN-214 steps: tap Accept on the Customer phone. expected: within 3 s the van's route redraws with the new stop in the accent; the toast reads "Booked <place>, $X instead of $Y. Van N already passes D mi away." matching the option card.
- JRN-215 steps: click that van. expected: the new stop is in the list with a "New" tag, timed between its neighbours.
- JRN-216 steps: ask the agent "Why did the new stop go there?". expected: the answer cites the added minutes and the pass-by.
- JRN-217 steps: presenter layout. expected: Driver phone shows the stop list with the new stop and time; Customer phone shows the quote with the price cut; both next to the map.
- JRN-218 steps: send a request that's missing a city. expected: no auto-send; amber "Needs clarification" flag; it waits for the owner.
- JRN-219 steps: click "Run the demo", choose "Use the scripted email". expected: data resets, presenter layout opens, the scripted request appears parsed and priced, quote goes out, the step strip advances.
- JRN-220 steps: in the demo, turn on "Auto-accept after 5 s". expected: Accept is tapped visibly after 5 s, then JRN-214 and JRN-215 happen, and the agent box is pre-filled with "Why did the new stop go there?".
- JRN-221 steps: click "Reset demo" in the presenter strip. expected: the New stop and toast are gone; 3 vans clean.
- JRN-222 steps: Inbox, Import jobs, upload a 5-row CSV, confirm the column match. expected: 5 requests appear read and priced.
- JRN-223 steps: click Sync now. expected: "Imported 0 new, skipped 5 already imported".
- JRN-224 steps: connect a Google Sheet through Google sign-in, confirm the match, add a row in the sheet, wait 30 s with the app open. expected: one new request appears; earlier rows are not duplicated.
- JRN-225 steps: give an unreadable sheet link. expected: "We couldn't read that sheet. Check the link or the file."
