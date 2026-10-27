"""Step 2 quote flows over HTTP: accept via text, decline, reject, loss-confirm, incoming text, stale slot.
Runs on demo data (reset first) - tests are serial and share state."""
import httpx

B = "http://localhost:8001/api"
c = httpx.Client(base_url=B, timeout=200)


def reset_and_read():
    assert c.post("/demo/reset").status_code == 200
    assert c.post("/inbox/read-all").status_code == 200


def vans(key):
    r = c.post(f"/inbox/{key}/ask-vans")
    assert r.status_code == 200, r.text
    return r.json()["options"]


def find_label(opts, label):
    for o in opts["cards"]:
        if label in o.get("labels", []):
            return o
    raise AssertionError(f"no {label}: {[o.get('labels') for o in opts['cards']]}")


def phone(p):
    return c.get("/phones").json()[p]


def test_flow_b_accept_by_text():
    reset_and_read()
    o = find_label(vans("req-04"), "Preferred window")
    assert o["unit_key"] == "van-4" and o["pickup_label"] == "4:15pm" and o["price"] == 35
    r = c.post("/inbox/req-04/send", json={"option_id": o["option_id"]})
    assert r.status_code == 200, r.text
    msgs = " ".join(m.get("text", "") for m in phone("customer"))
    assert "4:15pm" in msgs and "$35" in msgs
    r = c.post("/phones/customer/messages", json={"text": "ok"})
    assert r.status_code == 200, r.text
    req = c.get("/inbox/req-04").json()
    assert "accept" in str(req.get("status", req)).lower()
    assert any("Lakeshore" in m.get("text", "") for m in phone("driver"))


def test_decline_and_reject():
    reset_and_read()
    o = vans("req-02")["cards"][0]
    assert c.post("/inbox/req-02/send", json={"option_id": o["option_id"]}).status_code == 200
    qk = [m for m in phone("customer") if m.get("quote_key")][-1]["quote_key"]
    r = c.post(f"/quotes/{qk}/decline")
    assert r.status_code == 200, r.text
    assert "declin" in str(c.get("/inbox/req-02").json().get("status")).lower()
    opts = vans("req-01")
    first = opts["cards"][0]
    r = c.post("/inbox/req-01/reject-option", json={"option_id": first["option_id"]})
    assert r.status_code == 200, r.text
    assert first["option_id"] not in [o["option_id"] for o in r.json()["options"]["cards"]]


def test_loss_confirm_required():
    reset_and_read()
    s = c.get("/settings").json()["settings"]
    try:
        assert c.put("/settings", json={**s, "usual_one_off": 40.0}).status_code == 200
        opts = vans("req-08")
        loss = [o for o in opts["cards"] + opts.get("others", []) if o.get("loses_money")]
        assert loss, "no loses-money option for req 8 at $40"
        r = c.post("/inbox/req-08/send", json={"option_id": loss[0]["option_id"]})
        assert r.status_code >= 400, f"unconfirmed loss send accepted: {r.status_code}"
    finally:
        c.put("/settings", json={**s, "usual_one_off": 55.0})


def test_incoming_customer_text_creates_request():
    reset_and_read()
    before = {r["key"] for r in c.get("/inbox").json()["requests"]}
    r = c.post("/phones/customer/messages", json={"text": "tscheck pickup at 5800 College Ave at 3pm today to 1400 Powell St"})
    assert r.status_code == 200, r.text
    after = c.get("/inbox").json()["requests"]
    new = [x for x in after if x["key"] not in before]
    assert new, "no new request"


def test_stale_slot():
    reset_and_read()
    o1 = [o for o in vans("req-01")["cards"] if o["unit_key"] == "van-2"][0]
    o9 = [o for o in vans("req-09")["cards"] if o["unit_key"] == "van-2"][0]
    assert c.post("/inbox/req-01/send", json={"option_id": o1["option_id"]}).status_code == 200
    assert c.post("/inbox/req-09/send", json={"option_id": o9["option_id"]}).status_code == 200

    q1 = c.get("/inbox/req-01").json()["quote"]["key"]
    q9 = c.get("/inbox/req-09").json()["quote"]["key"]
    assert c.post(f"/quotes/{q1}/accept").status_code == 200
    c.post(f"/quotes/{q9}/accept")
    assert c.get("/inbox/req-09").json()["quote"]["status"] == "stale"
    assert any("filled up" in m.get("text", "") for m in phone("customer"))
    c.post("/demo/reset")
