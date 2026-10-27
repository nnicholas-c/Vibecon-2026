# Journeys: step9

superseded: step8's note that Done marks the earliest open stop on the most recently booked van.

- JRN-250 steps: at demo clock 10:00am, tap Done on the driver phone. expected: the stop the van is at or heading to is marked done (not an earlier past stop); later stop times shift on the driver phone and van page within 10 s.
- JRN-251 steps: tap Done when the van has finished its day. expected: "No stop to mark done right now."; nothing changes.
- JRN-252 steps: trigger a reorder (accept a request or move a stop). expected: on the van's map, the old route shows dashed and faint, the new route in the van's color, stop numbers update, for about 6 s, then the new route stays.
- JRN-253 steps: trigger a reorder while on Inbox, click "Show on map" in the toast. expected: the van page opens and plays the overlay.
- JRN-254 steps: accept the Hollis St demo quote. expected: the "Booked …" toast includes a ruler with the marker sliding from $55 to $35, both labelled; the numbers match the toast text.
- JRN-255 steps: with reduced motion on, repeat JRN-252 and JRN-254. expected: static before/after overlay and the marker at $35 without sliding.
