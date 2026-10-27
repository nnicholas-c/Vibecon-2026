# Journeys: step8

superseded: any journey clicking "Optimize route" on a van page; any journey expecting three option cards or a "Preferred window" card on requests without an asked time; any journey asserting the "Day used" tile label.

- JRN-230 steps: open a van page. expected: no "Optimize route" button or sentence; tile reads "Driving and stops: X of Y min".
- JRN-231 steps: accept a request (customer phone or email link) with any page open. expected: within 10 s, if the order changed, a toast "Van N reordered, saves M min"; the route shows the new order.
- JRN-232 steps: mark a stop done on the driver phone, or move a stop through the assistant. expected: the same auto-reorder and toast if the order changes; no toast if it doesn't.
- JRN-233 steps: compare spare minutes in the fleet strip, the van table and the van page. expected: the same number everywhere, equal to shift - driving - service.
- JRN-234 steps: at demo clock T, paste a request near a van that's mid-leg. expected: the first new stop's arrival includes travel from where the van is at T (no zero-travel arrival).
- JRN-235 steps: open a request whose cheapest and soonest are the same van at the same price. expected: one card "Cheapest and soonest".
- JRN-236 steps: open a request with no asked time. expected: no "Preferred window" card; at most two cards.
- JRN-237 steps: open a request with an explicit time ("around 2pm"). expected: a "Preferred window" card can show; still at most two cards.
- JRN-238 steps: Reset demo data, open each van page. expected: same stop counts and addresses; windows spread across the shift; no gap between consecutive arrivals over 30 minutes.
- JRN-239 steps: accept any request, then GET /api/units/van-3. expected: no optimize field; spare_minutes = shift - driving - service; max gap between consecutive arrivals < 35 min.
