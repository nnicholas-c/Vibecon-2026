# Phase: step17 — Final pre-publish: real-email setup, Task 7 demo polish, research page, mistake case

Version: step17-1. Web only (no mobile app). No tester, no full suites; quick checks per item, reported in order. Don't change pricing math, insertion or optimizer; agent.py limits/model unchanged except the rename in its prompt.

Live inbox: emergentcourier413@gmail.com (the presenter emails it from ANOTHER address). The user publishes; E3 can't.

## Functional requirements
- REQ-1150 [always] The system shall wait 5 s (was 20 s) for a customer Accept before auto-committing, and the countdown shall follow.
- REQ-1151 [always] The system shall use the live site's address in email Accept/quote links once deployed, saving it from /api/auth/google/start, /api/auth/google/callback and /api/live on any non-localhost host. PUBLIC_APP_URL is a last resort only.
- REQ-1152 [always] The system shall start the Gmail (10 s) and sheet (30 s) pollers in production with their leases.
- REQ-1153 [always] The scripted "Run the demo" request shall be a real seeded-area case where the cheapest card is a nearby van under $25 and another card is a far van at $45 or more, all from the engine. (Task 7.1)
- REQ-1154 [always] The system shall show "Fleet" instead of "Dispatch" everywhere a user can see it (titles, rail, buttons, toasts, the assistant's name and its system prompt), keeping /dispatch and /api/agents/dispatch working. (Task 7.2)
- REQ-1155 [event] When a request is sent or booked without the owner tapping, the system shall show "Auto-sent within your rules" with a link to the setting next to it in the Inbox, the toast and Activity. (Task 7.3)
- REQ-1156 [always] The assistant's reply and the stop chip shall say "booked" or "not booked yet" when it explains a stop. (Task 7.4)
- REQ-1157 [event] When "Price a job" is clicked on the landing (masthead, hero, chapter 05), the system shall open the Inbox. (Task 7.5)
- REQ-1158 [always] The system shall add a Morning Brief card at the top of the Fleet chat with each van's spare minutes today and the van most often late, from the engine and seed data. (Task 7.6; the user said earlier to ignore credit limits)
- REQ-1159 [always] The system shall add an "Our research" page linked from the footer and the Fleet page, in plain words, listing: 5,367 US local courier businesses (Census County Business Patterns 2023, NAICS 492210); an added stop on an existing route costs about $3.50 to $4 while an average stop costs about $12.28 (Routerra benchmark); Bay Area on-demand runs cost $45 to $65 (published rates of local couriers); leads answered within an hour are nearly 7 times as likely to qualify (Harvard Business Review, 2011). Each finding gets one line naming the Drivepast feature that answers it.
- REQ-1160 [always] The research page shall have an "Owner interviews" section with clear placeholders.
- REQ-1161 [event] When the old seeded request 4 (the office-closes-at-4:30 case) is fired from /dev ("Fire tricky email"), the system shall show the amber "Needs clarification" flag and offer 4:15pm. (interpreted: Task 9's Reset leaves zero requests, so request 4 no longer exists after Reset)

- REQ-1162 [state] While a request's options include a van other than the main card's van whose price is at least $20 higher, the system shall show one small muted line on each main option card in the owner Inbox: "A new trip on Van N would cost $X", where X is the highest such engine price (e.g. "A new trip on Van 3 would cost $52"). (E3 autonomy add-on; owner view only, customer_line wording unchanged per Task 6)
- REQ-1163 [state] While no other van is at least $20 dearer, the system shall show no such line.

## Quality requirements
Q-1150 Tag: Check.FarVan
      Scale: card prices after Reset + Run the demo
      Meter: report both
      Must: one < $25 and one >= $45
      Plan: same
Q-1151 Tag: Check.NoDispatchWord
      Scale: visible "Dispatch" matches in the frontend
      Meter: grep of user-visible strings
      Must: 0
      Plan: 0
Q-1152 Tag: Gmail.Latency
      Scale: seconds from a real email to Booked with the 5 s window
      Meter: estimate (10 s poll + ~3 s read + 5 s + up to 5 s UI poll)
      Must: 30
      Plan: 20
