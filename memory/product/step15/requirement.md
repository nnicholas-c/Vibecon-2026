# Phase: step15 — Demo-safety and presenter polish (chosen by E3 under the user's autonomy rule)

Version: step15-1. Filter: vision.md (does it make the 6-step demo work better or look cleaner). No tester, no full suites; quick targeted checks only. Don't change pricing math, insertion, optimizer or agent.py limits/model config.

## Functional requirements
- REQ-1050 [unwanted] If a request gives no date ("today", "tomorrow", a weekday or a date), then the system shall schedule it for the current demo day, not the next weekday, so it appears on today's routes. (interpreted: fixes the Grand Ave case booking for Monday)
- REQ-1051 [always] The system shall keep explicit dates as parsed ("tomorrow", "Monday", "Oct 27").
- REQ-1052 [event] When a request becomes Booked (customer Accept or auto-commit), the system shall send the customer a short confirmation in the same channel: for Gmail requests a reply in the same thread, "Booked. Van N picks up about T and drops off about T2. Price $X." For other sources, a message on the Customer demo phone.
- REQ-1053 [unwanted] If the confirmation email fails, then the system shall still keep the booking and log "Confirmation email didn't send" in Activity.
- REQ-1054 [always] The system shall never email prospect or directory addresses (existing blocked_address rule).
- REQ-1055 [always] The system shall tag Inbox rows and request detail "Booked automatically" when the auto-commit booked it, and "Accepted by customer" when the customer page or email link did.
- REQ-1056 [always] The system shall show one short talking point under the current step in the presenter strip during Run the demo and Rehearse (e.g. step 3: "No clicks: read, priced and quoted from the van that already passes."), one line per step, plain English.
- REQ-1057 [event] When the presenter clicks "Hide notes", the system shall hide the talking points and remember that in localStorage.
- REQ-1058 [state] While a quote is waiting in the 20 s auto-commit window, the customer page shall show "Books automatically in N s" counting down from the server's commit time, and remove it once booked. (E3 autonomy add-on)
- REQ-1059 [event] When the driver taps Done, the system shall show that stop as done (greyed, check mark) on the Dispatch map and the van page within 5 s. (E3 autonomy add-on)

## Quality requirements
Q-1050 Tag: Date.Default
      Scale: undated test requests not on today's route after booking
      Meter: script with 3 undated texts
      Must: 0
      Plan: 0
Q-1051 Tag: Confirm.Delivery
      Scale: bookings without a confirmation message
      Meter: one scripted booking and one Gmail-sourced booking (stub or real)
      Must: 0
      Plan: 0
