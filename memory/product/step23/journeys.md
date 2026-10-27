# Step 23 journeys: what a judge does on the live site

All of these run on https://drivepast.emergent.host.

- JRN-440 steps:
  - Open "/".
  - Read the hero and scroll the story.
  - Click "Price a job", then go back and click "Open the demo".
  expected:
  - The hero reads "Price every job from the van that already drives past."
  - The story or the plain fallback renders. With no WebGL, the plain fallback is fine.
  - Both buttons lead to the login screen, which has "Open the demo".
  - No console errors that break the page.
- JRN-441 steps: open "/research".
  expected:
  - Four findings with their sources show.
  - The owner interviews section shows.
  - Every link works.
- JRN-442 steps: on the login screen, click "Open the demo".
  expected:
  - /dispatch opens on a fresh board: 3 vans, clock 10:00am.
  - "New stops 2" and "Saved customers $80".
  - Three question chips show.
  - Inbox has 3 morning requests: 2 Booked and Rockridge Florist held with its reason.
  - Activity lists the morning's events, each showing who did it.
  - Memory shows 2 rules, both on.
- JRN-443 steps: in the Fleet chat, tap "Which van has the most spare time today?", then "Why is Van 2's next stop where it is?".
  expected:
  - Each gets a short plain reply within 15 s.
  - The van and minutes in each reply match the Fleet numbers.
  - No raw error.
- JRN-444 steps: keep Fleet open, and in a second tab open /dev and click "Fire demo email".
  expected, with no clicks on the Fleet tab:
  - It shows "Reading a request from Dana at Grand Lake Optometry".
  - The booking pop-up shows "Booked Dana at Grand Lake Optometry, $19.50 instead of $55, Van 2 already passes 1.8 mi away." plus "Bayline earns $19.50 for a stop that costs it about $10 extra."
  - The chat then asks why by itself and gets a reply.
  - The Phones panel opens: the driver's new stop is highlighted, and the customer's message has the reason line.
  - The booking lands within 30 s.
- JRN-445 steps: on /dev click "Fire tricky email".
  expected:
  - Fleet shows it held: "Lakeshore Dental closes at 4:30pm."
  - No booking pop-up.
  - No automatic chat question.
- JRN-446 steps: in Inbox, click "Add a request", paste the Maya text (5600 Bay St Emeryville to 1100 Gilman St Berkeley by 4pm) and price it. Do not send.
  expected:
  - The main card is Van 2 at $15, with the far-van line "A new trip on Van 3 would cost $52".
  - "See other options" lists Van 3 at $52.
- JRN-447 steps:
  - Open a booked request's detail page.
  - Open /driver/van-2 and the customer page for a booked request.
  - Open /q/bad-token.
  - Click Sign out.
  expected:
  - The detail page shows the price math and the "Booked automatically" or "Accepted by customer" tag.
  - The driver and customer pages render at phone width.
  - The bad quote link shows "This link isn't valid."
  - Sign out returns to the login screen.
- JRN-448 steps: view Fleet at 1920×1080 and at 1440×900.
  expected:
  - Nothing is cut off or overlapping.
  - No horizontal scroll.
