# Journeys: step10

superseded: none.

- JRN-260 steps: Reset, open Dispatch. expected: stat strip shows "Saved customers $0 today".
- JRN-261 steps: accept the Hollis quote ($35 instead of $55). expected: within 2 s the strip reads "Saved customers $20 today"; a second booking adds its saving; Undo subtracts it.
- JRN-262 steps: mark a stop done on a van whose later stops move. expected: those stops show "+N min" or "−N min" tags on the van page and driver phone; stops that didn't move show none; tags clear after 60 s or the next change.
- JRN-263 steps: in presenter mode click "Rehearse". expected: the demo plays every step by itself with a stopwatch and the current step shown; the agent's answer appears; it ends with "Rehearsal done in M:SS" and per-step times.
- JRN-264 steps: press a key during the rehearsal. expected: it pauses; Resume continues; Stop ends it.
- JRN-265 steps: rehearse while the agent model is unreachable. expected: the rehearsal stops at the agent step and says which step failed.
