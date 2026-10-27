# Step 25: second code-quality report remediation (no behaviour change)

phase-25. The user asked to apply the suggested fixes from a second code-quality report on the backend.

## Rule above all
Nothing a user or judge sees may change:
- The same prices, vans and pass-by lines.
- The same copy, toasts and confirmations.
- The same API responses and operationIds.

The engine's outputs must be byte-identical before and after.

## Functional requirements
- REQ-1600 [always] The backend shall have no circular import chain. The reported chain is agent.py → booking_common.py → google_api.py → import_api.py → ai/ladder.py → agent.py. Fix it by moving what ai/ladder.py needs from agent.py into a small shared module. Old import names keep working.
- REQ-1601 [always] Source shall contain no hard-coded secrets. The flags at google_api.py:73 and tests/test_phase4_options.py:162 are reviewed:
  - A real secret moves to env.
  - A public constant or a fake test value is made clearly non-secret, so scanners stop flagging it.
  - Live keys are not rotated now, because that would break the live site; the user rotates them after judging.
  - .env stays tracked for deployment, and the user cleans history at GitHub push.
- REQ-1602 [always] Every "possibly undefined" variable the type checker reports shall be fixed by initialising it before use, or confirmed unreachable.
- REQ-1603 [always] These functions shall be split into smaller helpers with identical behaviour:
  - ai_api.ai_config_save
  - agent.reply
  - ai/keyword.read_time
  - ai/ladder.read_request
  - email_send._assert_safe_email
  - engine/insertion.price_unit (9 arguments)
  - engine/insertion._simulate (8 arguments)

  The engine argument lists may be grouped into a small internal dataclass only if the outputs stay byte-identical.
- REQ-1604 [always] No loop shall create closures that late-bind the loop variable.
- REQ-1605 [always] In the three listed test files, `is` comparisons against strings or numbers shall become `==`. `is None` stays. `is True` and `is False` may stay as singleton identity checks, and any kept are listed in the report.

## Quality
```
Q-1600  Tag: Behaviour.Unchanged (money)
        Scale: differing bytes in the engine snapshot (all options for the Maya, Dana and three-request sample sets) before vs after
        Meter: the existing snapshot scripts (runall_snapshot.py, step24_check.py)
        Must: 0
        Plan: 0
Q-1601  Tag: Static.Health
        Scale: circular import chains plus possibly-undefined findings
        Meter: pyright / import-cycle check
        Must: 0 cycles, 0 real undefined
        Plan: 0
```
