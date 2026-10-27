# Journeys: step11

superseded: step7 JRN-213/214 (quote waits for the customer's Accept), JRN-220 (auto-accept switch), the step8/10 rehearsal "accept" step, any journey clicking "Read it" or "Read all requests", and any journey asserting a BACKUP badge.

- JRN-270 steps: with auto-send on and nothing open in a browser, send "pickup 2 boxes at 1300 Clay St Oakland, deliver to 1261 Fallon St by 3pm today" to the connected Gmail. expected: within 30 s, with no clicks: /api/inbox has it with status Booked; /api/fleet shows one van with stops +2; /api/events has "Booked …, $X instead of $Y, Van N already passes D mi away."
- JRN-271 steps: same email with the Inbox open. expected: the row appears within 5 s of ingest with source Gmail, sender and received time, status Reading → Priced → Quoted → Booked; a single booking toast.
- JRN-272 steps: open the request while reading. expected: skeleton "Reading the request", then "Pricing against 3 vans"; then the raw email body beside the parsed fields.
- JRN-273 steps: the poller runs 10 times after the email. expected: still one request (source_key = Gmail message id).
- JRN-274 steps: Add a request manually. expected: it reads and prices by itself; no "Read it" button; "Re-read" on detail works.
- JRN-275 steps: auto-send off, send an email. expected: status Priced, waits for the owner.
- JRN-276 steps: send a request that loses money or needs info. expected: not booked; status Priced with flag.
- JRN-277 steps: grep the frontend. expected: no /api/gmail/check calls, no BACKUP badge.
- JRN-278 steps: presenter Rehearse. expected: still plays end to end with the auto-booking, one toast per booking.
