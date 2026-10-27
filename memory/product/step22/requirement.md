# Step 22: hands-free demo with the owner's own Gmail

phase-22 (builds on everything in `product/overview.md` and steps 1 to 21; nothing else changes)

## Goal
After "Open the demo", every screen already has a realistic morning on it. The owner's own Gmail is the business inbox. The presenter sends a real email from another account. Drivepast reads it, prices it and books it by itself, then plays the rest on the Fleet page with no clicks:
- the booking pop-up, with what the courier earns,
- the assistant explaining why that van,
- the driver and customer phones updating.

User choices (Oct 2026):
- Autoplay: "I send the email, then the app plays the rest by itself".
- Inbox: "Switch to my own Gmail". The user connects it in Settings → Email and Google on the live site.
- The demo must show three things:
  - a real email booked by itself, with the price cut,
  - the assistant explaining why that van,
  - the driver and customer phones updating.
- Preloaded means both:
  - every screen is full of realistic data,
  - the assistant questions are ready to tap.
- From the user's rubric notes, only the ones that need the app:
  - a line showing what the courier earns,
  - the customer seeing why (the reason in the confirmation),
  - the live URL used in email links,
  - nothing showing the personal Gmail address,
  - everything fits on a 1080p screen.

A "demo session" means the visitor came in through "Open the demo" (the existing demo flag). (interpreted)

## Functional requirements

### Autoplay on the Fleet page
- REQ-1400 [event] When a booking from an incoming request completes while the Fleet page is open in a demo session, the system shall play the demo sequence below on the Fleet page with no clicks. (interpreted)
- REQ-1401 [event] When an email arrives during a demo session, the system shall show on the Fleet page that a request from the sender's name is being read, before it is booked. (interpreted)
- REQ-1402 [unwanted] If the incoming request is held (needs info, can't be priced, or out of rules), then the system shall show the held request and its reason on the Fleet page, with no autoplay after it.
- REQ-1403 [always] The booking pop-up shall add one line with the courier's side: "Bayline earns $15 for a stop that costs it about $3 extra."
  - The price is the booked price.
  - The extra cost is the engine's `added_cost` rounded to whole dollars.
- REQ-1404 [event] When the booking pop-up appears in a demo session, the system shall send "Why did {customer}'s job go on {Van}?" in the assistant chat by itself within 3 seconds.
  - {customer} is the same name the pop-up uses, for example "Maya Chen".
- REQ-1405 [always] The assistant's reply to that question shall state, from the real model and tools, all of these:
  - "Booked",
  - the pass-by distance,
  - the added minutes and miles,
  - the extra cost.
- REQ-1406 [unwanted] If the assistant reply has not arrived within 10 seconds, then the system shall continue to the phones step and leave the chat showing its normal error text.
- REQ-1407 [event] When the assistant reply arrives, the system shall open the Phones panel by itself, showing the Driver phone and the Customer phone for the new booking.
- REQ-1408 [always] The Driver phone shall show the new stop in the van's list with its time, highlighted as new.
- REQ-1409 [always] For email requests too, the Customer phone shall show the quote with its reason line ("Van 2 already passes 0.4 miles from you ...") and the booking confirmation. (interpreted)
- REQ-1410 [always] The sequence shall stay on the Fleet page.
  - It shall never open Inbox, Settings or /dev.
  - It shall never show the connected Gmail address.
- REQ-1411 [state] While a sequence is playing, the system shall queue a second booking's sequence until the first one ends.
- REQ-1412 [state] While not in a demo session, the system shall not autoplay the chat or the phones. (interpreted)

### Preloaded screens
- REQ-1413 [event] When Reset runs (including the login screen's "Open the demo"), the system shall load a realistic morning in the Inbox: at least 3 requests from before 10:00am.
  - At least 2 are booked.
  - 1 is held with its reason.
- REQ-1414 [event] When Reset runs, the system shall fill Activity with the morning's events for those requests, each showing who did it.
- REQ-1415 [event] When Reset runs, the system shall save 2 realistic rules in Memory, both on. They must not change any demo email's options.
- REQ-1416 [event] When Reset runs, the system shall show the morning's last booking on the Driver and Customer phones.
- REQ-1417 [always] The Fleet totals ("New stops", "Saved customers") shall include the morning bookings, so they agree with the Inbox. (interpreted)
- REQ-1418 [always] The morning bookings' stops shall be Done before 10:00am. They must leave every stop after 10:00am unchanged.
- REQ-1419 [always] After Reset, the demo emails shall keep their current results:
  - Maya: Van 2 at $15, with Van 3 at $52 as the alternative.
  - Dana (Fire demo email): Van 2 at $19.50.
- REQ-1420 [state] While no booking has happened since Reset, the Fleet chat shall show the three existing question chips, ready to tap.
- REQ-1421 [event] When a booking happens, the system shall add the chip "Why did {customer}'s job go on {Van}?" to the Fleet chat.

### The owner's own Gmail as the business inbox
- REQ-1422 [event] When the owner connects a different Gmail in Settings → Email and Google, the system shall watch only that inbox from then on.
- REQ-1423 [always] The system shall read only emails that arrive after the inbox was connected. (interpreted)
- REQ-1424 [unwanted] If an email is not a pickup or delivery request, then the system shall skip it, with no Inbox entry. (interpreted)
- REQ-1425 [unwanted] If an email is not a pickup or delivery request, then the system shall send no reply to it. (interpreted)
- REQ-1426 [always] Every email Drivepast sends shall show the sender name "Bayline Courier". (interpreted)
- REQ-1427 [always] The booking confirmation (email and Customer phone) shall include the reason, for example: "You're booked. Van 2 picks up around 2:10pm and drops off around 2:40pm. Van 2 already passes 0.4 miles from you, so it's $15 instead of our usual $55." (interpreted)
- REQ-1428 [always] Accept and Decline links in emails sent from the live site shall start with https://drivepast.emergent.host.

### Recording fit
- REQ-1429 [always] At a 1920×1080 screen (browser area about 1920×960), the whole sequence shall be visible on the Fleet page without scrolling:
  - the pop-up,
  - the chat reply,
  - both phones.

## Quality requirements
```
Q-1400  Tag: Demo.Speed
        Scale: seconds from the email reaching Gmail to the booking pop-up on Fleet
        Meter: Fire demo email on preview, 3 trials; real Gmail on live = human
        Must: 30
        Plan: 20
Q-1401  Tag: Demo.Flow
        Scale: seconds from the booking pop-up to both phones showing the booking
        Meter: browser check on preview, 2 trials
        Must: 25
        Plan: 15
Q-1402  Tag: Gmail.Privacy (exposure / trust)
        Scale: non-request emails that get an Inbox entry or a reply
        Meter: 3 non-request emails through the Gmail ingest path
        Must: 0
        Plan: 0
Q-1403  Tag: Booking.Integrity (money)
        Scale: quote emails and confirmations sent per request
        Meter: count after each trial
        Must: exactly 1 of each
        Plan: exactly 1 of each
Q-1404  Tag: AI.Accuracy (trust)
        Scale: share of numbers in the assistant's "why" reply (van, miles, minutes, extra cost) that match the engine
        Meter: compare to the option record, 3 trials
        Must: 100%
        Plan: 100%
Q-1405  Tag: Demo.Stability
        Scale: change in van or price for the Maya and Dana requests after the preload changes
        Meter: price both after Reset
        Must: 0
        Plan: 0
Q-1406  Tag: Recording.Fit (cosmetic)
        Scale: pixels of vertical scroll needed on Fleet at 1920×960 at the end of the sequence
        Meter: browser screenshot, 1 trial
        Must: 0
        Plan: 0
```
