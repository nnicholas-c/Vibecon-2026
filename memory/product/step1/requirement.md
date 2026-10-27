# Step 1 requirements: finish reading, options, price band and model settings

**Version:** step-1 (v2 work list)

**Goal:** Requests 1, 4, 7, 8 and 9 show correct fields, confidence marks, problems and labeled options, with the AI models set per v2 and four new request formats seeded and readable.

This step **extends `/app/memory/product/phase4/requirement.md`**. REQ-181 to REQ-245 still apply, except where a line below replaces one. Read `/app/memory/product/overview.md` (V-5, V-6) and `/app/memory/product/spec_v2.md` 3.1 to 3.3 and 3.10.

## Functional requirements (additions and replacements)
- REQ-246 [always] Reading requests through the built-in key shall default to Claude Haiku 4.5 with 5 examples in the prompt (interpreted model choice). This replaces REQ-205's Claude Sonnet 5.5 for reading.
- REQ-247 [always] Settings shall offer a "Reading model" choice of Claude Haiku 4.5, Claude Sonnet 5.5, GPT-5.5 or Gemini 3 Flash.
- REQ-248 [always] Settings shall offer "Examples in the prompt" of 0 or 5 for reading, default 5.
- REQ-249 [always] Settings shall offer an "Assistant model" choice from the same list, default Claude Sonnet 5.5, used from step 4.
- REQ-250 [always] "Our model" shall be blank by default, and AI mode shall default to "Auto".
- REQ-251 [always] When the test stand-in answers, the tag and "Last answered by" shall read "test stand-in", never "our model".
- REQ-252 [always] The test stand-in shall only answer when its env flag is on, and the flag shall be off by default in production.
- REQ-253 [always] The test stand-in shall not appear anywhere in the UI.
- REQ-254 [always] The seed shall include request 11, a forwarded purchase-order email, with status "new".
- REQ-255 [always] The seed shall include request 12, a long reply chain whose real ask sits mid-thread, with status "new".
- REQ-256 [always] The seed shall include request 13, a pasted WhatsApp chat, with status "new".
- REQ-257 [always] The seed shall include request 14, one email holding two separate jobs, with status "new".
- REQ-258 [always] Reading shall support more than one job per message.
- REQ-259 [event] When a message holds two jobs, the system shall create two linked requests, each with its own fields, problems and options, and show "1 of 2" / "2 of 2" on each (interpreted).
- REQ-260 [always] No other company's name or logo shall appear anywhere in the UI ("Haulix", "Phenomenon" or any other). The app says Drivepast. The fictional customer business is Bayline Courier.
- REQ-261 [always] The rail Inbox count shall equal the requests not yet quoted, accepted or declined (14 after reset, plus one more once request 14 is read and split).
- REQ-262 [always] Option cards shall not show Send, Accept or Reject in this step. They show only "See other options". This keeps REQ-245.

## Quality requirements
```
Q-37 Tag: AI.ReadAccuracy.Fast
     Scale: % of record_request fields correct on requests 1 to 14 with Claude Haiku 4.5 + 5 examples
     Meter: compare with hand-checked expected fields, 1 run
     Must: 80
     Plan: 92
```
```
Q-38 Tag: Perf.ReadOneFast
     Scale: seconds from submitting a pasted request to details and options shown (Haiku 4.5)
     Meter: headless browser, 3 requests, max
     Must: 15
     Plan: 6
```
```
Q-39 Tag: Trust.StandIn
     Scale: count of places the stand-in shows as "our model", appears in the UI, or answers with its flag off
     Meter: grep UI and responses; call it with the flag off
     Must: 0
     Plan: 0
```
```
Q-40 Tag: Brand.OnlyDrivepast
     Scale: count of other company names or logos visible on any screen
     Meter: text search of the rendered UI on every screen
     Must: 0
     Plan: 0
```
