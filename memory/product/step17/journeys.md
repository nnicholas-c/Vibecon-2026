# Journeys: step17

superseded: the 20 s Accept window (now 5 s); every visible "Dispatch" label (now "Fleet"); the old seeded request 4 inbox row after Reset (now fired from /dev).

- JRN-400 steps: Reset, Run the demo. expected: two cards, one nearby under $25 and one far at $45 or more; it auto-books after 5 s.
- JRN-401 steps: grep the frontend for visible "Dispatch". expected: 0; /dispatch still loads.
- JRN-402 steps: send one email request with auto-send on. expected: "Auto-sent within your rules" with a link to the setting in the Inbox row, the toast and Activity.
- JRN-403 steps: with auto-send off, ask "Why is the Grand Ave pickup on Van 2 where it is?" before and after accepting it. expected: the replies and chips say "not booked yet", then "booked".
- JRN-404 steps: on the landing, click "Price a job" in the masthead and chapter 05. expected: the Inbox opens.
- JRN-405 steps: open the Fleet chat. expected: the Morning Brief card shows each van's spare minutes and the van most often late.
- JRN-406 steps: open "Our research" from the footer and from the Fleet page. expected: 4 findings with sources, each with a "feature that answers it" line, plus Owner interviews placeholders.
- JRN-407 steps: Reset, then /dev "Fire tricky email". expected: the amber "Needs clarification" flag and an offer of 4:15pm because the office closes at 4:30.
