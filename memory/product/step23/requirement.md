# Step 23: judge-readiness bug check (no build)

phase-23. This is a verification pass only. The site is frozen: no code changes and no publish.

## Goal
Prove that everything a judge can touch on the LIVE site (https://drivepast.emergent.host) works with no broken screens, raw errors or dead ends. Judges watch the 2-minute video, open the live URL and read the research.

## What must be true
- REQ-1500 [always] The live landing, the login screen, Fleet, Inbox, Activity, Memory, Phones, Research, the driver and customer pages and the quote page shall load with no raw errors, JSON or blank screens.
- REQ-1501 [always] Every visible button and link on those screens shall lead somewhere sensible. No dead ends and no 404s.
- REQ-1502 [always] The demo flows shall work on live exactly as the step 16 to step 22 journeys describe. The spec deviations listed in the test brief are not bugs.
- REQ-1503 [always] The check shall leave the live site as it found it:
  - Gmail stays connected as emergentcouriers413@gmail.com.
  - Settings values are unchanged.
  - The board ends on a fresh Reset.

## Quality
```
Q-1500  Tag: Judge.Trust
        Scale: judge-visible bugs (raw error, broken screen, wrong number, dead link) on live
        Meter: e2e browser pass on live, 1 run
        Must: 0 high severity
        Plan: 0 of any severity
```
