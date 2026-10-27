# Step 2 journeys

Fresh Reset, clock 10:00am, auto-send off. Earlier journeys stay valid except JRN-10 (auto-send), JRN-17 (Phones placeholder) and the tagline part of JRN-1, which are superseded here.

- **JRN-81** Flow A: request 1 from Inbox to Van 2
  - steps: Open request 1, press "Ask the vans", then "Send" on the $11 Van 2 option. Open Demo phones and tap "Accept" on the Customer phone.
  - expected:
    - The Customer phone shows the quote ($11 a visit, about 1:54pm) with "Van 2 already passes 0.1 miles from you at 1:50pm, so it's $11 a visit instead of our usual $14." and Accept/Decline.
    - After Accept, the request and quote are "Accepted".
    - The Driver phone shows "New daily stop from Monday. Temescal Diagnostics, 5200 Shattuck, about 1:54pm, then Ashby Medical Center." (or very close).
    - The Owner phone notes the accept.
    - Van 2 shows 22 stops, with the new ones highlighted on the timeline and numbered on the map. The rail and Fleet table match.

- **JRN-82** Flow E: Undo
  - steps: After JRN-81, tap Undo on Van 2's page.
  - expected: Van 2 returns to 20 stops with the same times as before. The request shows "Quoted". The Driver phone gets "Change cancelled: …".

- **JRN-83** Flow B: request 4 at 4:15pm
  - steps: Open request 4, press "Ask the vans", Send the Preferred window option (Van 4, 4:15pm), then type "ok" on the Customer phone.
  - expected: The quote shows a 4:15pm pickup with a price between $35 and $55. "ok" books it, Van 4's timeline shows the 4:15pm pickup today, and the Driver phone gets the stop.

- **JRN-84** Decline
  - steps: Send an option for request 2, then tap "Decline" on the Customer phone.
  - expected: The quote and request show "Declined", the Owner phone notes it, and no route changes.

- **JRN-85** Reject an option
  - steps: On request 1's options, tap "Reject" on the Soonest card.
  - expected: That card is replaced by the next best option for that label, or disappears if there's none.

- **JRN-86** Loses-money confirm
  - steps: Set the usual one-off price to $40, open request 8, and tap Send on a "Loses money" option. Cancel. Then set the usual price back to $55.
  - expected: "This loses money at your usual price. Send anyway?" appears. Cancel sends nothing.

- **JRN-87** Auto-send
  - steps: Turn on "Auto-send the cheapest option within my rules" and read request 1 again (or send request 1 from the customer phone in Settings). Turn it off afterwards.
  - expected: By default the setting is off. When on, the Cheapest option arrives on the Customer phone without a tap.

- **JRN-88** Customer phone messages
  - steps: On the Customer phone with no open quote, type "pickup at 5800 College Ave at 3pm today to 1400 Powell St".
  - expected: A typing indicator shows, then a new request with source "text" appears in the Inbox and gets read.

- **JRN-89** Ask the customer
  - steps: Open request 7, tap "Ask the customer", then Send.
  - expected: The drafted question about which city appears on the Customer phone.

- **JRN-90** Stale slot
  - steps: Send request 1's Van 2 option and request 9's same option. Accept request 1, then accept request 9.
  - expected: The second accept shows "Sorry, that time just filled up…" on the Customer phone, and the owner sees "This slot is no longer free. Price it again."

- **JRN-91** Tagline and the phones on a phone
  - steps: Look at the header or empty states. Open Demo phones at 390x844.
  - expected: The tagline reads "Price every job from the van that already drives past." The three phones stack and stay readable, with no horizontal scroll.
