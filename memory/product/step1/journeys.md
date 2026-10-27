# Step 1 journeys

The Phase 4 journeys JRN-53 to JRN-73 stay valid. In them, "backup" now means the built-in key with Claude Haiku 4.5 and 5 examples, and the seeded set is 14 requests. Fresh Reset, demo clock 10:00am, AI mode Auto, "Our model" blank.

- **JRN-74** Model settings
  - steps: Open Settings.
  - expected:
    - "Reading model" shows Claude Haiku 4.5, and "Examples in the prompt" shows 5.
    - "Assistant model" shows Claude Sonnet 5.5. Each offers Claude Haiku 4.5, Claude Sonnet 5.5, GPT-5.5 and Gemini 3 Flash.
    - "Our model" is blank and AI mode is "Auto".
    - Changing the reading model to Gemini 3 Flash and saving persists after a refresh. Set it back afterwards.

- **JRN-75** Last answered by
  - steps: Read request 1, then open Settings.
  - expected: "Last answered by" names the built-in key and Claude Haiku 4.5, with the seconds taken and the time. The request's AI-written summary carries the "backup" tag.

- **JRN-76** Requests 1, 4, 7, 8 and 9
  - steps: Press "Read all requests", then open requests 1, 4, 7, 8 and 9 in turn.
  - expected:
    - Request 1 matches JRN-62 and JRN-53.
    - Request 4 matches JRN-63 (closes at 4:30pm, Preferred window 4:15pm on Van 4).
    - Request 7 matches JRN-64 (which city, Mission St).
    - Request 8 matches JRN-65 (impossible window, about 9:15am, capped at $55).
    - Request 9 matches JRN-66 (copy of request 1).
    - Every price sits between the floor and the usual price.

- **JRN-77** New formats are seeded and read
  - steps: Open the Inbox after "Read all requests" and open requests 11, 12, 13 and 14.
  - expected:
    - 11 (forwarded purchase order) reads the pickup, dropoff, time and frequency out of the PO text, ignoring the forwarding headers.
    - 12 (long reply chain) reads the real ask from mid-thread, not the signatures or quoted old messages.
    - 13 (WhatsApp paste) reads the job from the chat lines, ignoring timestamps and names.
    - 14 becomes two linked requests marked "1 of 2" and "2 of 2", each with its own fields and options.
    - Each shows confidence marks and any problems in amber.

- **JRN-78** The stand-in never ships
  - steps: With the stand-in env flag off, call /api/dev/stub-llm/v1/chat/completions. Search every screen for "stand-in" and check every tag.
  - expected: The call is refused (404 or a plain "not available" message). No screen mentions the stand-in, and no tag reads "our model" unless "Our model" was actually set to a real address.

- **JRN-79** Only Drivepast
  - steps: Visit every screen and search the visible text and images.
  - expected: No "Haulix", "Phenomenon" or other company's name or logo appears. The app is named Drivepast, and Bayline Courier appears only as the business.

- **JRN-80** No-AI mode with the new formats
  - steps: Set AI mode to "No AI" and press "Read all requests". Then set it back to "Auto".
  - expected: All 14 requests (15 after the split) get read without crashing. Request 1's locations are found, and the tags read "backup".
