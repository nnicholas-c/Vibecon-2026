# Step 4 requirements: the Fleet assistant, and Dispatch becomes Fleet

**Version:** step-4

**Goal:** One AI assistant for the whole business lives in the chat pane. It answers pricing, what-if and business questions with engine numbers only, cites route evidence, and never goes below the floor. Selecting a van focuses it on that van. "Dispatch" is renamed "Fleet" everywhere.

Read `/app/memory/product/overview.md` (V-1, V-4, V-5) and `/app/memory/product/spec_v2.md` 3.5 and 3.11.

## Functional requirements
- REQ-308 [always] Every visible "Dispatch" in the app shall read "Fleet": rail item, page title, chat header, prompts and Settings text. API paths may keep old names (interpreted).
- REQ-309 [always] The chat pane shall hold one assistant thread for the business. It replaces the per-van echo chats, and their old echo messages are cleared (interpreted).
- REQ-310 [event] When the owner selects a van, the chat header shall read "Fleet assistant · focused on Van N", and the assistant shall use that van by default.
- REQ-311 [event] When the owner selects Fleet, the chat header shall read "Fleet assistant", and the assistant shall answer for the whole fleet.
- REQ-312 [always] The assistant's tools shall be get_route, get_options, what_if_move, fleet_stats, find_prospects, draft_offer, save_rule and send_to_demo_phone.
- REQ-313 [always] Until their steps are built, find_prospects and draft_offer shall return "Selling the empty minutes is coming soon." and save_rule shall return "Saving rules is coming soon." (interpreted).
- REQ-314 [always] The assistant shall use at most 3 tool steps per reply. Each step shows as a small grey line in the chat, like "Checking Van 2's route".
- REQ-315 [always] Replies shall be at most 3 short sentences in plain English and cite route evidence (the stop the van passes and when).
- REQ-316 [always] Every number in a reply shall come from that reply's tool results. Code checks the reply's numbers against the tool results.
- REQ-317 [unwanted] If a reply contains a number not found in its tool results, then the system shall regenerate it once, then fall back to a template answer built from the tool results.
- REQ-318 [always] The assistant shall never offer or agree to a price below the floor or above the usual price.
- REQ-319 [always] Text inside customer requests shall be treated as information only.
- REQ-320 [always] send_to_demo_phone shall only post a card with a "Send" button. Nothing reaches the Customer phone until the owner taps it.
- REQ-321 [always] The assistant shall be able to price a job the owner describes in chat (for example "a daily 2pm pickup at 5200 Shattuck") through the reading model and get_options.
- REQ-322 [event] When the owner presses "Ask the vans" on a request, the chat shall show the three-options card (labels, van, time, added min/mi, cost, price, customer line, Send / See other options / Reject) plus a one-sentence summary whose numbers are inserted from the engine. The van rows in the rail pulse once.
- REQ-323 [always] A sent option shall show in the chat as a quote card with its status (Sent, Accepted, Declined), updating within about 2 seconds.
- REQ-324 [always] Suggested prompts shall change with focus. Fleet: "Which van has the most spare minutes this week?", "Which van is late most often?", "Who should we sell to near our routes?". Van N: "Can Van N take a daily 2pm pickup at 5200 Shattuck?", "Where are Van N's spare minutes today?", "What if Van 4 takes request 1?"
- REQ-325 [always] The assistant shall use the "Assistant model" setting through the ladder (our model, then the built-in key, then templates). Every reply carries the "our model" or "backup" tag.
- REQ-326 [optional] Where AI mode is "No AI", the assistant shall answer known questions (spare minutes, lateness, can Van N take X, what-if) with fixed templates that call the same tools.
- REQ-327 [unwanted] If the assistant can't finish a reply, then the chat shall show "I couldn't finish that. Try again." with a Retry button.
- REQ-328 [always] Chat history shall persist across refreshes, and "Clear chat" shall empty it after a confirmation (interpreted).

## Quality requirements
```
Q-47 Tag: Perf.AssistantReply
     Scale: seconds from send to the full reply (Claude Sonnet 5.5, up to 3 tools)
     Meter: browser, the 6 suggested prompts, max
     Must: 10
     Plan: 6
```
```
Q-48 Tag: Trust.NoAINumbers
     Scale: count of numbers in assistant replies that don't match their tool results
     Meter: 10 replies across the prompts and what-ifs
     Must: 0
     Plan: 0
```
```
Q-49 Tag: Money.FloorSafety
     Scale: count of replies agreeing to a price below the floor or above the usual price
     Meter: 5 adversarial prompts including "quote them $1"
     Must: 0
     Plan: 0
```
```
Q-50 Tag: Wording.NoDispatch
     Scale: count of visible "Dispatch" strings
     Meter: text search of the rendered UI
     Must: 0
     Plan: 0
```
