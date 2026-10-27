# Step 22 journeys

superseded: [JRN-380, JRN-381, JRN-383]
- JRN-380 said 0 requests, 0 events and 0 rules after Reset.
- JRN-381 said "New stops 0" and "Saved customers $0".
- JRN-383 said "New stops 1".

The preloaded morning replaces all three. Everything else in JRN-380 still holds: 3 vans, 8 stops each after 10:00am behaviour, clock 10:00am, auto-send on, floor 15, usual 55.

- JRN-420 steps: Reset demo data, then open Inbox, Activity and Memory.
  expected:
  - Inbox has at least 3 requests from before 10:00am: at least 2 Booked and 1 held with a reason.
  - Activity lists the morning's events, each with who did it.
  - Memory shows 2 rules, both on.
  - No screen is empty.
- JRN-421 steps: after Reset, open Fleet.
  expected:
  - "New stops" and "Saved customers" include the morning bookings and match the Inbox.
  - The chat shows the three question chips, ready to tap.
  - The Phones panel shows the morning's last booking.
- JRN-422 steps: after Reset, price the Maya request (5600 Bay St Emeryville to 1100 Gilman St Berkeley by 4pm) and the Dana request (Fire demo email text).
  expected:
  - Maya: Van 2 at $15, with Van 3 at $52 as the alternative.
  - Dana: Van 2 at $19.50.
  - Same as before this step.
- JRN-423 steps: from landing, click "Open the demo", then "Open the demo" on the login screen. In a second tab, open /dev and click "Fire demo email". Touch nothing on the Fleet tab.
  expected, in order on the Fleet tab, which stays on /dispatch:
  - It shows a request from "Dana at Grand Lake Optometry" being read.
  - The booking pop-up shows "Booked Dana at Grand Lake Optometry, $19.50 instead of $55, Van 2 already passes 1.8 mi away." It also shows "Bayline earns $19.50 for a stop that costs it about $N extra." N is the engine's added_cost, rounded.
  - Within 3 s the chat sends "Why did Dana at Grand Lake Optometry's job go on Van 2?" by itself. (The exact name is whatever the pop-up uses.)
  - The reply says Booked, the pass-by miles, the added minutes and miles, and the extra cost. All match the engine.
  - The Phones panel then opens by itself:
    - the Driver phone shows the new stop highlighted with its time,
    - the Customer phone shows the quote with its reason line and the confirmation with the reason.
  - Total time from the pop-up to the phones is 25 s or less.
- JRN-424 steps: after JRN-423, look at the Fleet chat.
  expected: a chip "Why did {customer}'s job go on Van 2?" is there, ready to tap.
- JRN-425 steps: in a demo session, on /dev click "Fire tricky email".
  expected:
  - Fleet shows the held request and its reason.
  - No booking pop-up.
  - No automatic chat question.
  - The Phones panel does not open by itself.
- JRN-426 steps: fire two demo bookings a few seconds apart in a demo session.
  expected:
  - The second sequence starts only after the first one ends.
  - Each request gets exactly 1 quote and 1 confirmation.
- JRN-427 steps: sign in without the demo flag (normal session) and fire a demo booking. (interpreted)
  expected:
  - The booking pop-up still shows.
  - The chat does not ask by itself.
  - The Phones panel does not open by itself.
- JRN-428 steps: put a non-request email ("Lunch on Friday?") through the Gmail ingest path, then an email dated before the inbox was connected. (interpreted)
  expected:
  - Neither gets an Inbox entry.
  - Neither gets a reply.
  - Neither shows in Activity.
- JRN-429 steps: after a booking from an email request, read the stored confirmation and the outgoing email headers.
  expected:
  - The confirmation includes the reason ("... already passes ... so it's $X instead of our usual $55.").
  - The sender name is "Bayline Courier".
- JRN-430 steps: at a 1920×960 browser area, run JRN-423 and take a screenshot at the end.
  expected:
  - The pop-up (or the flashed row once it closes), the chat reply and both phones are all visible.
  - No vertical scroll is needed.
- JRN-431 steps (human, live site):
  - On https://drivepast.emergent.host, connect the owner's own Gmail in Settings → Email and Google.
  - Click "Open the demo", then "Open the demo" again.
  - From another account, send the Maya email.
  expected:
  - Within 30 s the Fleet page shows it being read, then booked: "Booked Maya Chen, Bay Street Design, $15 instead of $55, Van 2 already passes 0.4 mi away." plus the earnings line.
  - The chat then explains by itself, and the phones open.
  - The sender's inbox gets one quote email from "Bayline Courier". Its links start with https://drivepast.emergent.host.
  - The sender's inbox then gets one confirmation with the reason.
