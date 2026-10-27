# Journeys: step6 — Memory and Activity

superseded: any earlier journey asserting a Memory or Activity placeholder page.

- JRN-180 steps: in the Dispatch chat type "Don't send Van 2 downtown after 3". expected: assistant confirms in one line; the chat shows a save_rule tool line; Memory shows a chip with that text, switched on.
- JRN-181 steps: open an inbox request whose stop is in Downtown Oakland with a window after 3pm (or the builder's seeded equivalent), view options. expected: Van 2 is not offered; its row says it can't because of the rule.
- JRN-182 steps: on Memory, switch that rule off, reopen the same request. expected: Van 2 is offered again where the engine allows; reload keeps the switch off.
- JRN-183 steps: type "Never send Van 1 to SF after 3pm". expected: a second chip appears; SF stops after 3pm aren't given to Van 1.
- JRN-184 steps: save a non-area rule like "Always mention the floor price". expected: chip appears and toggles; options don't change.
- JRN-185 steps: delete a rule. expected: chip is gone after reload.
- JRN-186 steps: open Activity after: reading a request, sending an option, accepting on the customer phone, declining one, undoing, adding/toggling a rule, asking the assistant a question. expected: one row each, newest first, each with time, actor (owner / customer / assistant / driver) and a plain line; the assistant question shows its tool call (e.g. get_fleet_summary).
- JRN-187 steps: Reset demo data, open Activity and Memory. expected: "Nothing has happened yet today." and no rules (or only seeded ones if the builder seeds none, empty state text shown).
- JRN-188 steps: check the rail. expected: order business name, Dispatch, vans, Inbox, Memory, Activity, Settings, Phones.
