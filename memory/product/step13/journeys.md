# Journeys: step13

superseded: step7/step10/step12 notes naming the Hollis St scripted email and its toast "Booked Ana, Hollis Street Bio, $15 instead of $55…" (only if REQ-950 finds a better address).

- JRN-320 steps: Reset, then use the scripted email with auto-send off. expected: two cards on different vans, the nearby one about $15 to $22 and the far one about $45 to $55.
- JRN-321 steps: Run the demo or Rehearse. expected: it books the nearby van automatically; the toast and ruler show the new numbers; the savings bump matches.
- JRN-322 steps: ask the assistant "Why is the Grand Ave pickup on Van 2 where it is?" before booking. expected: the chat shows the explain_stop line with a "Not booked yet" label and the stop name.
- JRN-323 steps: after a booking, ask about that stop. expected: the label reads "Booked"; for a seeded stop it reads "On today's route".
- JRN-324 steps: open the Import page with a connected sheet. expected: "Last synced <time>: N new, M skipped", updating after the 30 s backend sync; with no sheet, "No sheet connected".
- JRN-325 steps: let a request auto-book. expected: the inbox row and detail show "Booked in N s"; unbooked requests show no timer.
