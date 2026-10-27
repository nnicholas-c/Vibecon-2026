"""Step 1 backend tests: 14 seeded requests, built-in-key reading model/examples/assistant model
(REQ-246..250), multi-job split (REQ-258/259), inbox count after Read all = 15, stand-in label
'test stand-in' (REQ-251/252/253), new requests 11..14 read correctly (JRN-77).
Must be run with -n 0 (shared demo state)."""
import os, json, time, pytest, requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE}/api"


@pytest.fixture(scope="module", autouse=True)
def _reset():
    requests.post(f"{API}/demo/reset", json={}, timeout=30)
    requests.put(f"{API}/ai/config", json={
        "base_url": "", "model": "", "clear_secret": True, "mode": "auto",
        "reading_model": "claude-haiku-4-5", "reading_examples": 5, "assistant_model": "claude-sonnet-5-5"
    }, timeout=10)
    yield
    requests.post(f"{API}/demo/reset", json={}, timeout=30)
    requests.put(f"{API}/ai/config", json={
        "base_url": "", "model": "", "clear_secret": True, "mode": "auto",
        "reading_model": "claude-haiku-4-5", "reading_examples": 5, "assistant_model": "claude-sonnet-5-5"
    }, timeout=10)


# ---------- Seed count ----------
class TestSeed14:
    def test_14_seeded_requests_after_reset(self):
        requests.post(f"{API}/demo/reset", json={}, timeout=30)
        inbox = requests.get(f"{API}/inbox", timeout=10).json()
        rows = inbox["requests"]
        assert len(rows) == 14, [r["number"] for r in rows]
        assert inbox["open_count"] == 14
        # Verify 11-14 senders
        by_num = {r["number"]: r for r in rows}
        assert "Lakeshore Dental" in by_num[11]["sender"]
        assert "Montgomery Partners" in by_num[12]["sender"]
        assert "Elmwood Pharmacy" in by_num[13]["sender"]
        assert "Rockridge Florist" in by_num[14]["sender"]
        for n in (11, 12, 13, 14):
            assert by_num[n]["status"] == "new"


# ---------- REQ-246..250: AI config defaults and choices ----------
class TestAIConfigModels:
    def test_defaults(self):
        g = requests.get(f"{API}/ai/config", timeout=10).json()
        assert g["reading_model"] == "claude-haiku-4-5"
        assert g["reading_examples"] == 5
        assert g["assistant_model"] == "claude-sonnet-5-5"
        assert g["mode"] == "auto"
        assert g["base_url"] == ""
        # All four model options are offered
        models = g.get("models") or {}
        for k in ("claude-haiku-4-5", "claude-sonnet-5-5", "gpt-5-5", "gemini-3-flash"):
            assert k in models, (k, list(models.keys()))

    def test_put_valid_values(self):
        r = requests.put(f"{API}/ai/config", json={
            "reading_model": "gemini-3-flash", "reading_examples": 0, "assistant_model": "gpt-5-5"
        }, timeout=10)
        assert r.status_code == 200, r.text
        g = requests.get(f"{API}/ai/config", timeout=10).json()
        assert g["reading_model"] == "gemini-3-flash"
        assert g["reading_examples"] == 0
        assert g["assistant_model"] == "gpt-5-5"
        # restore defaults
        requests.put(f"{API}/ai/config", json={
            "reading_model": "claude-haiku-4-5", "reading_examples": 5, "assistant_model": "claude-sonnet-5-5"
        }, timeout=10)

    def test_invalid_reading_model_422(self):
        r = requests.put(f"{API}/ai/config", json={"reading_model": "garbage"}, timeout=10)
        assert r.status_code == 422, r.text
        assert "reading_model" in json.dumps(r.json())

    def test_invalid_reading_examples_422(self):
        r = requests.put(f"{API}/ai/config", json={"reading_examples": 3}, timeout=10)
        assert r.status_code == 422, r.text
        assert "reading_examples" in json.dumps(r.json())

    def test_invalid_assistant_model_422(self):
        r = requests.put(f"{API}/ai/config", json={"assistant_model": "foo"}, timeout=10)
        assert r.status_code == 422, r.text
        assert "assistant_model" in json.dumps(r.json())


# ---------- Read all → 15 (after request 14 splits), JRN-80 ----------
class TestReadAllFifteen:
    def test_read_all_splits_req14_and_count_is_15(self):
        requests.post(f"{API}/demo/reset", json={}, timeout=30)
        r = requests.post(f"{API}/inbox/read-all", json={}, timeout=240)
        assert r.status_code == 200, r.text
        results = r.json()["results"]
        # Request 14 should have parts=2
        r14 = next(x for x in results if x["number"] == 14)
        assert r14.get("parts") == 2, r14
        inbox = requests.get(f"{API}/inbox", timeout=10).json()
        rows = inbox["requests"]
        # Rail count: not quoted/accepted/declined
        pending = sum(1 for it in rows if it["status"].lower() in ("new", "needs_info", "priced"))
        assert pending == 15, pending
        # There must be a request number 15 that is linked to 14
        by_num = {r["number"]: r for r in rows}
        assert 15 in by_num, sorted(by_num)
        # Each part shows group with of=2
        d14 = requests.get(f"{API}/inbox/req-14", timeout=10).json()
        d15 = requests.get(f"{API}/inbox/{by_num[15]['key']}", timeout=10).json()
        g14 = d14.get("group") or {}
        g15 = d15.get("group") or {}
        assert g14.get("of") == 2 and g14.get("part") == 1, g14
        assert g15.get("of") == 2 and g15.get("part") == 2, g15
        # Linked keys cross-reference each other
        assert d14["key"] in (g15.get("keys") or []) and d15["key"] in (g14.get("keys") or [])

    def test_rereading_req14_does_not_duplicate(self):
        # Re-reading 14 must reuse the same linked request
        inbox_before = requests.get(f"{API}/inbox", timeout=10).json()["requests"]
        count_before = len(inbox_before)
        r = requests.post(f"{API}/inbox/req-14/read", json={}, timeout=120)
        assert r.status_code == 200, r.text
        inbox_after = requests.get(f"{API}/inbox", timeout=10).json()["requests"]
        assert len(inbox_after) == count_before, (count_before, len(inbox_after))


# ---------- Request 11 (forwarded PO) and 13 (WhatsApp) content ----------
class TestNewRequestsContent:
    """Read all has already run in previous class (module scope). Check details.
    Note: tests depend on auto-order within module; keep classes sequential.
    """

    def _details_lower(self, key):
        d = requests.get(f"{API}/inbox/{key}", timeout=10).json()
        return d, json.dumps(d).lower()

    def test_req11_po_lakeshore_to_piedmont(self):
        d, txt = self._details_lower("req-11")
        assert "lakeshore dental" in txt
        assert "piedmont" in txt
        # 3pm pickup
        assert ("3pm" in txt or "3:00" in txt or "15:00" in txt)

    def test_req12_reply_chain_thirdstreet_to_montgomery(self):
        d, txt = self._details_lower("req-12")
        assert "third street print" in txt or "600 3rd" in txt
        assert "montgomery" in txt

    def test_req13_whatsapp_elmwood_to_ashby(self):
        d, txt = self._details_lower("req-13")
        assert "elmwood pharmacy" in txt
        assert "ashby medical" in txt


# ---------- REQ-251/252/253: stand-in label 'test stand-in' ----------
class TestStandInLabel:
    def test_stub_reads_and_tags_as_test_stand_in(self):
        base = f"{BASE}/api/dev/stub-llm"
        r = requests.put(f"{API}/ai/config", json={
            "base_url": base, "model": "stub-qwen", "secret": "test-secret-1234", "mode": "auto"
        }, timeout=10)
        assert r.status_code == 200
        rr = requests.post(f"{API}/inbox/req-01/read", json={}, timeout=30)
        assert rr.status_code == 200, rr.text
        item = rr.json()
        ai = item.get("ai") or {}
        # Must be level 1 and tag 'test stand-in' (never 'our model')
        assert ai.get("level") == 1, ai
        assert ai.get("tag") == "test stand-in", ai
        assert ai.get("label") == "Test stand-in", ai
        # last_answered reflected in /api/ai/config
        g = requests.get(f"{API}/ai/config", timeout=10).json()
        la = g.get("last_answered") or {}
        assert la.get("tag") == "test stand-in", la
        assert la.get("label") == "Test stand-in", la
        # Clear
        requests.put(f"{API}/ai/config", json={"base_url": "", "model": "", "clear_secret": True, "mode": "auto"}, timeout=10)


# ---------- JRN-78/Q-39: stub source code hides path + flag-off → 404 ----------
class TestStubHidden:
    def test_openapi_hides_stub(self):
        paths = requests.get(f"{API}/openapi.json", timeout=10).json()["paths"]
        assert not any("stub-llm" in p for p in paths)

    def test_stub_source_default_flag_off(self):
        # Code review: the backend source should default DEV_STUB_ENABLED to false
        with open("/app/backend/ai_api.py") as f:
            src = f.read()
        assert 'os.environ.get("DEV_STUB_ENABLED", "false")' in src, "stub flag default must be false"
        assert "include_in_schema=False" in src, "stub must be hidden from OpenAPI"


# ---------- REQ-262: Option cards do not expose Send/Accept/Reject ----------
class TestOptionCardsNoSendAccept:
    def test_price_result_does_not_include_send_accept_reject_fields(self):
        d = requests.post(f"{API}/engine/price", json={"request_key": "req-01"}, timeout=30).json()
        txt = json.dumps(d).lower()
        # These action verbs must not appear as structural fields
        for word in ("send_url", "accept_url", "reject_url", "send_button", "accept_button", "reject_button"):
            assert word not in txt, word
