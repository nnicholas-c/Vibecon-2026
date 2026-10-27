# Drivepast Vision (verbatim from the user, Oct 25)

Read this before every task. It is the north star; the task prompts are the steps. When a task and this document disagree, the task wins for that task, and this document wins for everything the task did not mention.

## What Drivepast is
Drivepast is dispatch for small businesses whose workers drive to customers: couriers first, then plumbers, HVAC, cleaners. A new request arrives by email or spreadsheet. The engine works out which van is already going to pass nearby, what it costs to add the stop to that van's day in minutes and miles, and prices the job from that cost. The customer sees a lower price because the van was already there. The owner sees the route update live with the new stop in it. Nobody clicks anything to make this happen.

The two things that make it worth building are the live route update and the price cut that comes from it. Everything else exists to make those two things visible.

## The one demo
Everything built this weekend serves this 60 to 90 second sequence. If a change does not make one of these steps work better or look cleaner, it is not needed.
1. The Dispatch page is open. Three vans, their routes drawn on the map, one stat strip, nothing else.
2. The presenter sends an email from a phone to the connected Gmail: a pickup address, a drop-off address, a deadline.
3. Within 30 seconds, with no clicks: the Inbox badge ticks up, the request appears already parsed and priced, the quote goes out, and one van's route redraws with the new stop highlighted. A toast reads: "Booked Clay Street, $35 instead of $55. Van 2 already passes 0.2 mi away."
4. The presenter clicks that van. The new stop sits in the list with a New tag, timed between its neighbours.
5. The presenter asks the agent panel why the stop went there. The answer cites the added minutes and the pass-by.
6. A phone frame on the same screen shows the driver's list with the new stop and the customer's message with the price cut.

Steps 1 to 5 are the product. Step 6 is the proof that both ends of the business see it.

## User decisions on top (Oct 25)
- The stop joins the route only after the customer taps Accept (not at quote time).
- Cut the demo fleet to 3 vans everywhere.
- Spreadsheet: Google Sheet via the existing Google sign-in, auto-checked like Gmail, plus CSV upload.
- Build the toast, New tag and side-by-side phones. Make the demo automated and easy to present.
- Dropped: training/scoring pages, prospect pins/offers, van tiles. Testing only when the user asks.
