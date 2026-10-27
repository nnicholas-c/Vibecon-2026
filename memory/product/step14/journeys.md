# Journeys: step14

superseded: step11 behaviour "auto-send books immediately" (now quote, wait up to 20 s for Accept, then auto-commit); the rail item "Phones" → /phones is replaced by "Demo phones" → /dispatch with the drawer open.

- JRN-340 steps: open /driver/van-2 on a 375px screen. expected: header with van name and driver; today's stops in order with time, customer, address, window, Done; booked-today stops tagged New; no login, no nav.
- JRN-341 steps: tap Done on a stop. expected: the existing mark-done runs; the list updates within 5 s.
- JRN-342 steps: open /customer/<key> for a quoted request. expected: grey bubble with the original text, reply bubble with the customer_line, pickup and drop-off times, Accept and Decline.
- JRN-343 steps: tap Accept. expected: the request becomes Booked; the page shows "Accepted. Van N arrives about T." and no buttons.
- JRN-344 steps: tap Decline on another quoted request. expected: status Declined.
- JRN-345 steps: with auto-send on, add a request and do nothing. expected: quoted at once; booked automatically about 20 s later.
- JRN-346 steps: with auto-send on, add a request, open /dispatch, click Phones. expected: within 30 s the Customer tab shows the price line with Accept; tapping Accept books it; the Driver tab shows the new stop with New without reload.
- JRN-347 steps: open the assistant drawer, then click Phones. expected: only one drawer is open.
- JRN-348 steps: click "Demo phones" in the left nav. expected: /dispatch opens with the Phones drawer open.
