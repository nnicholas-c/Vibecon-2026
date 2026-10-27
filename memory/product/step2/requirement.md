# Step 2 requirements: send, accept and undo, plus the Demo phones

**Version:** step-2

**Goal:** The owner sends one option with a tap. The customer accepts it on the Customer demo phone. The stops join the van's route, the driver phone gets the new stop, and Undo puts the route back.

Read `/app/memory/product/overview.md` (V-1 to V-3) and `/app/memory/product/spec_v2.md` 3.4 and 3.11.

**What's built:**
- Request pages with labeled option cards and "See other options".
- Engine accept/undo API, with stale-slot refusal.
- A Phones placeholder.
- An "Auto-send quotes within my rules" setting, which is on.

## Functional requirements
- REQ-263 [always] Each option card on the request page shall show "Send", "See other options" and "Reject".
- REQ-264 [event] When the owner taps "Send" on an option, the system shall create a quote with status "Sent", set the request to "Quoted", and post the quote to the Customer demo phone.
- REQ-265 [unwanted] If the option is marked "Loses money at your usual price", then "Send" shall ask "This loses money at your usual price. Send anyway?" before sending (interpreted).
- REQ-266 [event] When the owner taps "Reject" on an option, the system shall hide that option and show the next best option for that label (interpreted).
- REQ-267 [always] Settings shall show "Auto-send the cheapest option within my rules", off by default. It replaces the old auto-send setting.
- REQ-268 [optional] Where auto-send is on, the system shall send the Cheapest option as soon as a request is priced, if it's feasible, at or above the floor and not losing money.
- REQ-269 [always] The quote on the Customer phone shall show the price, the van's time, the customer reason line, and "Accept" and "Decline" buttons.
- REQ-270 [event] When the customer taps "Accept", the system shall book the stops through the engine: recurring work on the weekday route with its start date, a one-off on its date's route.
- REQ-271 [event] When a booking succeeds, the system shall set the quote and request to "Accepted".
- REQ-272 [event] When a booking succeeds, the system shall send the Driver phone a message like "New daily stop from Monday. Temescal Diagnostics, 5200 Shattuck, about 1:54pm, then Ashby Medical Center."
- REQ-273 [event] When a booking succeeds, the system shall send the Owner phone a short note like "Rina accepted: $11 a visit on Van 2." (interpreted).
- REQ-274 [unwanted] If the slot is no longer free at Accept, then the Customer phone shall show "Sorry, that time just filled up. We'll send a new option shortly." and the owner shall see "This slot is no longer free. Price it again."
- REQ-275 [event] When the customer taps "Decline", the system shall set the quote and request to "Declined" and note it on the Owner phone.
- REQ-276 [event] When the customer replies "ok", "yes" or "sounds good" to an open quote, the system shall treat it as Accept (interpreted; Flow B).
- REQ-277 [event] When the customer replies anything else, the system shall attach it to that request and re-read the request.
- REQ-278 [event] When the customer types a message with no open quote, the system shall create a new request with source "text".
- REQ-279 [always] After a booking, the van's timeline, map, rail status, stat chips and Fleet table shall show the new stops, highlighted for 10 seconds on the timeline.
- REQ-280 [always] An "Undo" button shall appear on the accepted request and on the van page after a booking.
- REQ-281 [event] When the owner taps Undo, the system shall restore the previous route.
- REQ-282 [event] When the owner taps Undo, the system shall set the request back to "Quoted" (interpreted).
- REQ-283 [event] When the owner taps Undo, the system shall tell the Driver phone "Change cancelled: <stop> is off your route." (interpreted).
- REQ-284 [event] When the owner taps "Ask the customer" and then "Send", the drafted question shall go to the Customer phone.
- REQ-285 [always] The "Demo phones" drawer shall show the Customer, Driver and Owner phones side by side (stacked on a phone screen), styled as real phones with bubbles, timestamps and a short typing indicator before incoming messages.
- REQ-286 [always] Each demo phone shall have a reply box.
- REQ-287 [always] The phones shall refresh every 2 seconds while the drawer is open.
- REQ-288 [always] The Settings demo controls "Send request 1 from the customer phone" and "Customer taps Accept" shall work.
- REQ-289 [always] Real texting shall stay off, and the Twilio adapter shall stay disabled.
- REQ-290 [always] The app tagline shall read "Price every job from the van that already drives past." everywhere the old tagline was.

## Quality requirements
```
Q-41 Tag: Flow.A (it's broken)
     Scale: taps from opening request 1 to an accepted stop on Van 2
     Meter: headless browser
     Must: 6
     Plan: 4 (Ask the vans, Send, open phones, Accept)
```
```
Q-42 Tag: Data.Undo
     Scale: count of differences in Van 2's stops and times, before Accept vs after Undo
     Meter: API and browser
     Must: 0
     Plan: 0
```
```
Q-43 Tag: Perf.PhoneUpdate
     Scale: seconds from Send to the quote showing on the Customer phone
     Meter: browser, 3 trials
     Must: 4
     Plan: 2
```
```
Q-44 Tag: Money.SendBand
     Scale: count of quotes sent above the usual price or below the floor
     Meter: API across all sent quotes
     Must: 0
     Plan: 0
```
