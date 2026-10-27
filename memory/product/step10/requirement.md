# Phase: step10 — Savings tally, Done time jump, Hands-free rehearsal

Version: step10-1. Small polish on the demo. No full tester run unless the user asks. Don't change pricing, insertion or optimizer logic; don't touch agent.py model config/limits.

## Functional requirements
- REQ-800 [always] The system shall show "Saved customers $X today" in the Dispatch stat strip, where X is the sum over today's accepted quotes of (usual price - quoted price), from stored engine numbers.
- REQ-801 [event] When a booking is accepted, the system shall update the tally within 2 s (same 1.5 s /api/live poll as the booking toast).
- REQ-802 [event] When a booking is undone, the system shall subtract it from the tally.
- REQ-803 [event] When Reset demo data runs, the system shall set the tally to $0.
- REQ-804 [event] When a stop is marked done and later stop arrival times change, the system shall show a tag "+N min" or "−N min" next to each stop whose arrival moved by at least 1 minute, on the van page stop list and the driver phone.
- REQ-805 [state] While a stop's time didn't move (e.g. waiting for a window), the system shall show no tag for it.
- REQ-806 [event] When 60 seconds pass after the Done, or the next Done or reorder happens, the system shall clear the old tags. (interpreted)
- REQ-807 [event] When the presenter clicks "Rehearse" in presenter mode, the system shall play the whole demo by itself: reset, scripted email, read and price, quote out, auto-accept, toast with ruler, van page with the New stop, send "Why did the new stop go there?" to the agent and show the answer, then the phones, with a pause on each step.
- REQ-808 [always] The system shall show a running stopwatch and the current step during a rehearsal, and at the end a summary line "Rehearsal done in M:SS" plus each step's time.
- REQ-809 [event] When the presenter presses any key, clicks Pause or clicks Stop during a rehearsal, the system shall pause or stop it.
- REQ-810 [unwanted] If a rehearsal step fails (e.g. the agent can't reach the model), then the system shall show which step failed in plain words and stop.
- REQ-812 [event] When a booking adds to the savings tally, the system shall briefly show "+$N" (N = that booking's saving) next to the figure for about 1.5 s, as ink text on an accent #FF5B1F box (accent never as text on paper). With reduced motion it appears and disappears without animation. Undo shows nothing.
- REQ-811 [always] The system shall use real engine and agent calls in a rehearsal (one agent message per run, within the daily model limit).

## Quality requirements
Q-800 Tag: Tally.Truth
      Scale: difference between the tally and the sum of (usual - price) over accepted quotes
      Meter: script after 2 bookings and 1 undo
      Must: $0
      Plan: $0
Q-801 Tag: Rehearsal.Length
      Scale: seconds for a full hands-free run
      Meter: stopwatch, 2 runs
      Must: 120
      Plan: 75
