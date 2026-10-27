# Journeys: step12

superseded: earlier journeys and checks that assume floor $11 / usual $14 for the demo seed (e.g. landing panel 04 "$11 a visit, usually $14" now follows the engine with the new Settings; Hollis/Clay "$35 instead of $55" will change).

- JRN-300 steps: Reset demo data, open Settings. expected: floor per run 15, usual per run 55, markup 100; cost per hour and per mile unchanged.
- JRN-301 steps: Add a request "pickup at 3220 Grand Ave Oakland between 1 and 2pm, drop at 4100 Piedmont Ave by 4pm". expected: two cards with different prices (nearby about $18 to $22, far about $45 to $55), neither $35.
- JRN-302 steps: read the cheaper card's customer line. expected: "Van N already passes D miles from you at T, so it's $X for the run instead of our usual $55."
- JRN-303 steps: read a card capped at usual. expected: "Our usual price for this run is $55."
- JRN-304 steps: ask the dispatch agent "Why is the Grand Ave pickup on Van 2 where it is?". expected: the reply contains added minutes.
- JRN-305 steps: ask about a stop by a misspelled customer name. expected: the tool matches the closest stop; with no match, the agent answers from the van's stop list.
- JRN-306 steps: watch the network while the tab is hidden. expected: no /api/live calls while hidden; every 5 s when visible; no /api/import/sync-all calls from the browser; /api/events every 10 s.
