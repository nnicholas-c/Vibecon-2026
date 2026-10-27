# Phase: step19 — Task 6 (re-issued): remove demo button + re-verify price visibility, explain fix, polling

Version: step19-1. Items 1–4 of this Task 6 were built in step12 (seed floor 15 / usual 55 / markup 100, customer_line wording, explain_stop fuzzy match + prompt line, /api/live 5 s visible-only, no frontend sync-all). This phase adds item 5 and makes the CHECK pass on the Task 9 seed. No tester; E3 runs the CHECK.

## Functional requirements
- REQ-1250 [always] The system shall not render a "Run the demo" button on the Fleet (/dispatch) page; its component and wiring are deleted, not hidden with CSS.
- REQ-1251 [always] The system shall not render the Rehearse/presenter step bar on any page; PresenterStrip and its Rehearse logic and the /dev step-bar toggle are deleted. /present still loads (map + phones) without it. (interpreted)
- REQ-1252 [always] The system shall keep the Google sign-in path and the landing "Open the demo" button unchanged.
- REQ-1253 [state] While merging leaves only one distinct main card (Cheapest, Soonest and Preferred window all the same van and price), the system shall show as the second card the best-priced engine option on a different van, labelled "Another van", so the owner sees two different prices. (interpreted: on the Task 9 seed the Grand Ave request collapses to one card, and the CHECK needs two)
- REQ-1254 [always] The system shall keep at most two main cards, and keep items 1–4 of the task as built in step12.

## Quality requirements
Q-1250 Tag: Check.Task6b
      Scale: after Reset + POST the Grand Ave text: two cards with different prices, neither $35; agent reply to "Why is the Grand Ave pickup on Van 2 where it is?" contains added minutes; /dispatch has no Run the demo button
      Meter: E3 curl + grep/build check; report both prices and the reply
      Must: pass
      Plan: pass
