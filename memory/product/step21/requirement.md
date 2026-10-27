# Phase: step21 — Backend code-quality fixes (from the user's code review report)

Version: step21-1. Behaviour-preserving only: no changes to pricing, insertion, optimizer outputs, API contracts, response fields, routes, texts or agent.py limits/model. The demo is about to be recorded, so every change must be safe. No tester and no full suites; run the targeted check scripts listed below.

## Requirements
- REQ-1350 [always] The system shall remove the server.py ↔ live_api.py and engine_api.py ↔ phones_api.py import cycles by moving the shared pieces into a small common module (e.g. backend/common.py or demo_core.py), keeping every endpoint path and behaviour identical.
- REQ-1351 [always] The system shall contain no hardcoded secrets. Verify google_api.py:59 and tests/test_phase4_options.py:162. Real secrets move to env vars; constants that only look like secrets (URLs, header names, test dummies) get a short comment or a clearer name. Report which was which.
- REQ-1352 [always] The system shall have no possibly-undefined variables. Review all 43 flagged spots (ruff/pyflakes F821/F841-type and pylint "possibly-used-before-assignment"), initialise or guard each, and report the count fixed vs false positives.
- REQ-1353 [always] Tests shall use subprocess.run([...], check=True) instead of os.system (tests/test_drivepast_api.py:374).
- REQ-1354 [always] Dynamic imports in test_step6_memory_activity.py:143,161 and scripts/step20_signin_check.py:42 shall become static imports where possible.
- REQ-1355 [always] The system shall split these high-complexity functions into smaller helpers without changing outputs: ai/keyword.py read_locations() and dir_matches(), agent.py _open_request_match() and t_explain_stop(), engine/insertion.py build_nodes(), and the test test_rule_from_chat_blocks_and_toggles() (into smaller tests or fixtures).
- REQ-1356 [always] The flagged late-binding closure in a loop shall bind its loop variable explicitly.
- REQ-1357 [always] Tests shall compare constants with == (keep `is` only for None/True/False) in test_step6_memory_activity.py, test_phase4_options.py and test_phase2_engine.py.

## Verification (targeted only)
- Lint (ruff) clean for the touched files; python -c "import server" works with no circular-import warnings.
- Engine outputs unchanged: before/after snapshot via scripts/runall_snapshot.py (or equivalent) on Reset + the Grand Ave, Gilman→Parker and Bay St→Gilman requests, diffed field by field = identical.
- Re-run: scripts/step12_check.py (explain_stop), scripts/step16_check.py (reset + fire email), scripts/step20_signin_check.py, and the Task 1 agent check (one real "Which van has the most spare time today?" call).
