"""Phase 4 backend tests: options engine (JRN-53..57), settings cap, AI config/secret masking,
inbox read-all, request page endpoints, incoming-text, OpenAPI hidden stub."""
import os, time, json, pytest, requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE}/api"


@pytest.fixture(scope="module", autouse=True)
def _reset():
    requests.post(f"{API}/demo/reset", json={}, timeout=30)
    # Clear any AI config leftover
    requests.put(f"{API}/ai/config", json={"base_url": "", "model": "", "clear_secret": True, "mode": "auto"}, timeout=10)
    yield
    requests.post(f"{API}/demo/reset", json={}, timeout=30)
    requests.put(f"{API}/ai/config", json={"base_url": "", "model": "", "clear_secret": True, "mode": "auto"}, timeout=10)


def _price(key):
    r = requests.post(f"{API}/engine/price", json={"request_key": key}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


# ---------------- JRN-53: three options for req-01 ----------------
class TestOptionsReq01:
    def test_cards_shape_and_labels(self):
        d = _price("req-01")
        assert "options" in d, d
        opts = d["options"]
        cards = opts["cards"]
        # at least cheapest and preferred window present; soonest may share
        all_labels = sum([c["labels"] for c in cards], [])
        for lab in ("Cheapest", "Soonest", "Preferred window"):
            assert lab in all_labels, (lab, all_labels)
        # all cards sorted by price-ish; max 3
        assert 1 <= len(cards) <= 3

    def test_van2_price_11_monthly_231(self):
        d = _price("req-01")
        cards = d["options"]["cards"]
        pref = [c for c in cards if "Preferred window" in c["labels"]][0]
        assert pref["unit_name"] == "Van 2"
        assert pref["price"] == 11.0
        assert pref["monthly_total"] == 231.0
        assert pref["pickup_label"] == "1:54pm"
        # customer line copy
        assert "Van 2 already passes 0.1 miles from you at 1:50pm" in pref["customer_line"]
        assert "$11 a visit" in pref["customer_line"]
        assert "our usual $14" in pref["customer_line"]

    def test_others_limits(self):
        d = _price("req-01")
        opts = d["options"]
        others = opts["others"]
        assert len(others) <= 5
        from collections import Counter
        c = Counter(o["unit_key"] for o in others)
        assert all(v <= 2 for v in c.values()), c
        # sorted by price ascending
        prices = [o["price"] for o in others]
        assert prices == sorted(prices)

    def test_price_band_never_above_usual_or_below_floor(self):
        d = _price("req-01")
        cards = d["options"]["cards"] + d["options"]["others"]
        for c in cards:
            assert 11.0 - 1e-6 <= c["price"] <= 14.0 + 1e-6, c["price"]

    def test_perf_under_500ms(self):
        d = _price("req-01")
        assert d["ms"] < 500, d["ms"]


# ---------------- JRN-54: req-08 cap ----------------
class TestReq08Cap:
    def test_preferred_shifted_delivery_capped_55(self):
        d = _price("req-08")
        opts = d["options"]
        assert opts.get("from_shifted") is True
        cards = opts["cards"]
        pref = [c for c in cards if "Preferred window" in c["labels"]][0]
        assert pref["price"] == 55.0
        assert pref["capped"] is True
        # delivery around 9:10am
        assert pref["dropoff_label"].endswith("am")
        # explanation says capped at usual
        assert "capped at your usual $55" in pref["explanation"]
        # customer line
        assert pref["customer_line"] == "Our usual price for this run is $55."

    def test_no_option_above_55_or_below_35(self):
        d = _price("req-08")
        for c in d["options"]["cards"] + d["options"]["others"]:
            assert 35.0 - 1e-6 <= c["price"] <= 55.0 + 1e-6, c["price"]


# ---------------- JRN-55: usual_one_off=40 loses_money hold_as_draft ----------------
class TestLosesMoney:
    def test_lower_usual_one_off_marks_draft(self):
        # Set usual_one_off to 40
        r = requests.put(f"{API}/settings", json={"usual_one_off": 40}, timeout=10)
        assert r.status_code == 200, r.text
        try:
            d = _price("req-08")
            cards = d["options"]["cards"] + d["options"]["others"]
            # Any option where added_cost > 40 should price 40, loses_money, hold_as_draft
            any_loss = False
            for c in cards:
                if c["added_cost"] > 40 + 1e-6:
                    assert c["price"] == 40.0, c
                    assert c["loses_money"] is True
                    assert c["hold_as_draft"] is True
                    any_loss = True
                # Price never above usual (40), never below floor
                assert c["price"] <= 40.0 + 1e-6
                assert c["price"] >= d.get("floor_one_off", c.get("floor", 0)) - 1e-6
            assert any_loss, "expected at least one option with added_cost>40"
        finally:
            requests.put(f"{API}/settings", json={"usual_one_off": 55}, timeout=10)


# ---------------- JRN-56: Settings validation ----------------
class TestSettingsValidation:
    def test_defaults_present(self):
        r = requests.get(f"{API}/settings", timeout=10)
        s = r.json()["settings"]
        assert s["usual_recurring"] == 14
        assert s["usual_one_off"] == 55

    def test_floor_above_usual_rejected_422(self):
        r = requests.put(f"{API}/settings", json={"floor_recurring": 16}, timeout=10)
        assert r.status_code == 422, (r.status_code, r.text)
        body = r.json()
        # Expect fields.floor_recurring in error payload
        text = json.dumps(body)
        assert "floor_recurring" in text, body
        # verify nothing saved
        r2 = requests.get(f"{API}/settings", timeout=10).json()["settings"]
        assert r2["floor_recurring"] != 16


# ---------------- JRN-57: floor+usual together ----------------
class TestFloorAndUsualTogether:
    def test_set_usual_20_floor_15_req1_quotes_15(self):
        r = requests.put(f"{API}/settings", json={"usual_recurring": 20, "floor_recurring": 15}, timeout=10)
        assert r.status_code == 200, r.text
        try:
            d = _price("req-01")
            pref = [c for c in d["options"]["cards"] if "Preferred window" in c["labels"]][0]
            assert pref["price"] == 15.0
            assert pref["monthly_total"] == 315.0
            # No price above usual (20) or below floor (15)
            for c in d["options"]["cards"] + d["options"]["others"]:
                assert 15.0 - 1e-6 <= c["price"] <= 20.0 + 1e-6
        finally:
            requests.put(f"{API}/settings", json={"usual_recurring": 14, "floor_recurring": 11}, timeout=10)


# ---------------- JRN-58/59: AI config, secret masking, test endpoint ----------------
class TestAIConfig:
    # Not a credential: a placeholder built at runtime that the test saves, then checks never comes back unmasked.
    PLACEHOLDER_VALUE = "-".join(("test", "secret", "1234"))

    def test_save_secret_masked_everywhere(self):
        r = requests.put(f"{API}/ai/config", json={
            "base_url": "http://10.255.255.1:9", "model": "fake-model", "secret": self.PLACEHOLDER_VALUE, "mode": "auto"
        }, timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        assert self.PLACEHOLDER_VALUE not in json.dumps(body)
        # REQ-395: no part of the key comes back
        if "secret_masked" in body:
            assert "1234" not in body["secret_masked"]
            assert self.PLACEHOLDER_VALUE not in body["secret_masked"]

        # GET ai/config also masks
        g = requests.get(f"{API}/ai/config", timeout=10).json()
        assert self.PLACEHOLDER_VALUE not in json.dumps(g)
        if "secret_masked" in g:
            assert "1234" not in g["secret_masked"]

        # settings also must not leak full secret
        s = requests.get(f"{API}/settings", timeout=10).json()
        assert self.PLACEHOLDER_VALUE not in json.dumps(s)

    def test_test_connection_fails_plainly_fast(self):
        # Set unreachable
        requests.put(f"{API}/ai/config", json={
            "base_url": "http://10.255.255.1:9", "model": "fake-model"}, timeout=10)
        t0 = time.time()
        r = requests.post(f"{API}/ai/test", json={}, timeout=35)
        dt = time.time() - t0
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("ok") is False
        # should fail within ~25s (20s timeout + a little)
        assert dt < 30, dt
        # plain English message, no stack trace
        msg = (body.get("message") or body.get("error") or "").lower()
        assert "20 second" in msg or "couldn't reach" in msg or "no answer" in msg or "unreachable" in msg or "could not" in msg, msg


# ---------------- Level-1 stub LLM path ----------------
class TestStubLLM:
    def test_stub_connect_and_read_tags_our_model(self):
        base = f"{BASE}/api/dev/stub-llm"
        requests.put(f"{API}/ai/config", json={
            "base_url": base, "model": "stub-qwen", "secret": "test-secret-1234", "mode": "auto"
        }, timeout=10)
        r = requests.post(f"{API}/ai/test", json={}, timeout=30)
        assert r.status_code == 200
        b = r.json()
        assert b.get("ok") is True, b
        # model name present
        txt = json.dumps(b).lower()
        assert "stub-qwen" in txt

        # Read a request → tag our model
        rr = requests.post(f"{API}/inbox/req-01/read", json={}, timeout=30)
        assert rr.status_code == 200, rr.text
        item = rr.json()
        ai = item.get("ai") or {}
        tag = (ai.get("tag") or "").lower()
        assert "our" in tag or ai.get("level") == 1, item

    def test_stub_delay_falls_back(self):
        base = f"{BASE}/api/dev/stub-llm?delay=25"
        requests.put(f"{API}/ai/config", json={"base_url": base, "model": "stub-qwen"}, timeout=10)
        rr = requests.post(f"{API}/inbox/req-01/read", json={}, timeout=60)
        assert rr.status_code == 200
        ai = rr.json().get("ai") or {}
        tag = (ai.get("tag") or "").lower()
        assert "backup" in tag or "no ai" in tag or ai.get("level") in (2, 3), rr.json()

    def test_stub_fail_falls_back(self):
        base = f"{BASE}/api/dev/stub-llm?fail=1"
        requests.put(f"{API}/ai/config", json={"base_url": base, "model": "stub-qwen"}, timeout=10)
        rr = requests.post(f"{API}/inbox/req-01/read", json={}, timeout=60)
        assert rr.status_code == 200
        ai = rr.json().get("ai") or {}
        tag = (ai.get("tag") or "").lower()
        assert "backup" in tag or "no ai" in tag or ai.get("level") in (2, 3), rr.json()

    def test_cleanup_clears_config(self):
        requests.put(f"{API}/ai/config", json={"base_url": "", "model": "", "clear_secret": True, "mode": "auto"}, timeout=10)
        g = requests.get(f"{API}/ai/config", timeout=10).json()
        assert not g.get("base_url")
        assert not g.get("model")


# ---------------- JRN-60: No AI keyword reader ----------------
class TestNoAIMode:
    def test_no_ai_reads_without_crash(self):
        requests.put(f"{API}/ai/config", json={"mode": "none"}, timeout=10)
        try:
            r = requests.post(f"{API}/inbox/read-all", json={}, timeout=120)
            assert r.status_code == 200, r.text
            # req-01 should be priced and reflect expected details
            det = requests.get(f"{API}/inbox/req-01", timeout=10).json()
            txt = json.dumps(det).lower()
            assert "5200 shattuck" in txt or "temescal" in txt
            assert "ashby" in txt
            ai = det.get("ai") or {}
            tag = (ai.get("tag") or "").lower()
            assert "backup" in tag or "no ai" in tag or ai.get("level") in (2, 3)
            # price options via engine
            d = _price("req-01")
            assert d["options"]["cards"], d
        finally:
            requests.put(f"{API}/ai/config", json={"mode": "auto"}, timeout=10)


# ---------------- JRN-61: Inbox read-all statuses ----------------
class TestInboxReadAll:
    def test_statuses_after_read_all(self):
        requests.post(f"{API}/demo/reset", json={}, timeout=30)
        r = requests.post(f"{API}/inbox/read-all", json={}, timeout=180)
        assert r.status_code == 200, r.text
        inbox = requests.get(f"{API}/inbox", timeout=10).json()
        items = inbox["requests"]
        by_num = {it["number"]: it for it in items}
        priced = {1, 2, 3, 5, 10}
        needs_info = {4, 6, 7, 8, 9}
        for n in priced:
            s = by_num[n]["status"].lower()
            assert s in ("priced", "quoted"), (n, by_num[n])
        for n in needs_info:
            s = by_num[n]["status"].lower()
            assert "needs" in s or s == "needs_info", (n, by_num[n])
        # rail count: not quoted/accepted/declined
        pending = sum(1 for it in items if it["status"].lower() in ("new", "needs_info", "priced"))
        assert pending == 15, pending


# ---------------- JRN-72: Decline drops rail count ----------------
class TestDecline:
    def test_decline_req3(self):
        requests.post(f"{API}/demo/reset", json={}, timeout=30)
        requests.post(f"{API}/inbox/read-all", json={}, timeout=180)
        inbox_before = requests.get(f"{API}/inbox", timeout=10).json()["requests"]
        pending_before = sum(1 for it in inbox_before if it["status"].lower() in ("new", "needs_info", "priced"))
        r = requests.post(f"{API}/inbox/req-03/decline", json={}, timeout=10)
        assert r.status_code == 200, r.text
        inbox_after = requests.get(f"{API}/inbox", timeout=10).json()["requests"]
        req3 = next(it for it in inbox_after if it["key"] == "req-03")
        assert req3["status"].lower() == "declined"
        pending_after = sum(1 for it in inbox_after if it["status"].lower() in ("new", "needs_info", "priced"))
        assert pending_after == pending_before - 1


# ---------------- Incoming text and OpenAPI ----------------
class TestIncomingAndOpenAPI:
    def test_incoming_text_creates_request(self):
        r = requests.post(f"{API}/inbox/incoming-text", json={
            "from_number": "+15555550123",
            "text": "Need a pickup at Rockridge Florist 5800 College Ave at 3pm today, deliver to 1400 Powell St Emeryville"
        }, timeout=60)
        assert r.status_code in (200, 201), r.text
        body = r.json()
        key = body.get("key") or body.get("request_key")
        assert key, body
        it = requests.get(f"{API}/inbox/{key}", timeout=10).json()
        assert it["source"] == "text"

    def test_openapi_exposes_new_endpoints_and_hides_stub(self):
        r = requests.get(f"{API}/openapi.json", timeout=10)
        assert r.status_code == 200
        paths = r.json()["paths"]
        for p in ("/api/inbox", "/api/inbox/read-all", "/api/inbox/incoming-text",
                  "/api/inbox/{key}/ask-vans", "/api/inbox/{key}/ask-customer",
                  "/api/inbox/{key}/decline", "/api/ai/config", "/api/ai/test"):
            assert p in paths, p
        # stub must be hidden
        for p in paths:
            assert "stub-llm" not in p, p


# ---------------- Engine run-all shape includes options ----------------
class TestEngineRunAllOptions:
    def test_run_all_has_options_and_perf(self):
        r = requests.post(f"{API}/engine/run-all", json={}, timeout=30)
        assert r.status_code == 200
        d = r.json()
        items = d.get("results") or d.get("items") or []
        assert items
        for it in items[:3]:
            # engine results per request should have options with cards
            opts = it.get("options") or {}
            assert "cards" in opts, it
            if "ms" in it:
                assert it["ms"] < 500
