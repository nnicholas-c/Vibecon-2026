# Phase: step14 — Task 8: driver and customer pages, phone frame (user's task text is authoritative)

Version: step14-1. Read-only pages except the customer Accept/Decline. Use existing endpoints; add at most two new ones. No tester, no full suites; quick targeted checks only.

## Functional requirements
- REQ-1000 [always] The system shall serve /driver/:vanId as a 375px mobile page with no login and no nav.
- REQ-1001 [always] /driver/:vanId shall show a header with the van name and driver, then today's stops in order with time, customer, address, window and a Done button.
- REQ-1002 [always] /driver/:vanId shall show a "New" tag on stops booked today.
- REQ-1003 [event] When Done is tapped, the system shall call the existing mark-done endpoint.
- REQ-1004 [state] While /driver/:vanId is visible, the system shall poll the van endpoint every 5 s.
- REQ-1005 [always] The system shall serve /customer/:requestKey as a 375px mobile page with no login and no nav.
- REQ-1006 [always] /customer/:requestKey shall show the customer's original text in a grey bubble, then a reply bubble with the sent option's customer_line, the pickup and drop-off times, and Accept and Decline buttons.
- REQ-1007 [event] When Accept is tapped, the system shall call the existing commit (accept) endpoint.
- REQ-1008 [event] When Decline is tapped, the system shall set the request status to Declined.
- REQ-1009 [state] While the request is Booked, /customer/:requestKey shall show the reply bubble, then "Accepted. Van N arrives about T." and no buttons.
- REQ-1010 [state] While auto-send is on, the system shall send the quote immediately, then wait up to 20 s for an Accept from the customer page.
- REQ-1011 [event] When 20 s pass after the quote with no Accept, the system shall commit automatically (same path as now).
- REQ-1012 [unwanted] If the customer accepts and the auto-commit fires at the same moment, then the system shall book the stop only once.
- REQ-1013 [event] When "Phones" in the /dispatch top bar is clicked, the system shall open a right-side drawer (the same drawer as the assistant, one open at a time) holding a phone-shaped frame with Driver and Customer tabs.
- REQ-1014 [always] The Driver tab shall embed /driver/:vanId in an iframe for the van most recently booked today, falling back to Van 1.
- REQ-1015 [always] The Customer tab shall embed /customer/:requestKey in an iframe for the most recent quoted or booked request.
- REQ-1016 [always] The left nav shall have "Demo phones" pointing at /dispatch with the Phones drawer open.
- REQ-1017 [always] The system shall keep /present and Rehearse working with the 20 s wait (Rehearse may tap Accept on the customer page or let the timer commit). (interpreted)

## Quality requirements
Q-1000 Tag: Check.Task8
      Scale: with auto-send on: Add a request, open /dispatch, click Phones. (1) Customer tab shows the price line with Accept within 30 s, (2) tapping Accept marks it Booked, (3) Driver tab shows the new stop with a New tag without reload
      Meter: builder's browser check with screenshots; report the three observations
      Must: all three
      Plan: all three
Q-1001 Tag: Gmail.Latency (Task 3)
      Scale: seconds from a real Gmail send to Booked with no clicks, now including the 20 s wait
      Meter: estimate; report
      Must: report it
      Plan: report it
