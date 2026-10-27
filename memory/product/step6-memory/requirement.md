# Phase: step6 — Memory rules and Activity feed (spec_v2 3.6, 3.7; work list step 5)

Goal: rules the owner states become on/off chips the engine respects, and every action is visible in one timeline with who did it.

Version: step6-1. Builds on the working Dispatch/Fleet assistant (`backend/agent.py`: save_rule tool, `agent_rules` collection {business_id, text, active, created_at}, `events` collection {ts, scope, tool, args, result_summary}). Don't change the assistant's limits or model config.

## Functional requirements
- REQ-500 [event] When the owner states a standing rule in chat (e.g. "Never send Van 1 to SF after 3pm", "don't send Van 2 downtown after 3"), the system shall save it in agent_rules via save_rule.
- REQ-501 [always] The system shall show a Memory page (rail item "Memory") listing every saved rule as a square chip with its text and an on/off switch.
- REQ-502 [event] When the owner flips a rule's switch, the system shall persist `active` and keep it after reload.
- REQ-503 [event] When the owner deletes a rule, the system shall remove its chip. (interpreted)
- REQ-504 [unwanted] If a rule save or toggle fails, then the system shall show "Couldn't save that rule. Try again." and keep the previous state.
- REQ-505 [always] The system shall parse rules of the type "van X not to area A after time T" into structured form {van, area, after_minutes}; other rules stay assistant instructions only.
- REQ-506 [state] While an area/time rule is active, the system shall exclude options that put that van's new stop in that area after that time.
- REQ-507 [state] While an area/time rule is off, the system shall ignore it in options.
- REQ-508 [always] The system shall recognise the areas "SF"/"San Francisco" and "downtown" (= Downtown Oakland) for rule enforcement. (interpreted)
- REQ-509 [event] When an option is blocked by a rule, the system shall say why in plain words on that van's row, e.g. "Van 2 can't: your rule 'don't send Van 2 downtown after 3'".
- REQ-510 [event] When a rule is added, toggled or deleted, the system shall recompute the options shown for open inbox requests on next view.
- REQ-511 [always] The system shall show an Activity page (rail item "Activity") as a newest-first timeline.
- REQ-512 [always] The system shall log to the timeline every request read, option sent, accept, decline, undo, rule change and assistant tool call.
- REQ-513 [always] The system shall show on each timeline row the time, the actor (owner, customer, assistant or driver) and one plain-English line.
- REQ-514 [state] While there is no activity, the system shall show "Nothing has happened yet today."
- REQ-515 [always] The system shall keep Reset demo data clearing rules and activity back to a clean state. (interpreted)
- REQ-516 [always] The system shall keep the left rail order: business name, Fleet/Dispatch, vans, Inbox, Memory, Activity, Settings, Phones.

## Quality requirements
Q-500 Tag: Rules.Correctness
      Scale: options that violate an active rule
      Meter: API test on seeded requests with "don't send Van 2 downtown after 3" on and off
      Must: 0
      Plan: 0
Q-501 Tag: Activity.Completeness
      Scale: actions from REQ-512 missing from the feed after doing each once
      Meter: e2e, one of each action
      Must: 0
      Plan: 0
Q-502 Tag: Activity.Speed
      Scale: ms to render Activity with 200 events
      Meter: Playwright, 3 trials
      Must: 1500
      Plan: 500
