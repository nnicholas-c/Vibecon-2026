import copy, uuid, os
from pymongo import MongoClient


def _vans(c, job):
    o = c.post("/engine/price", json={"job": job}).json()["options"]
    return {x["unit_key"] for x in o["cards"] + o["others"]}, o.get("blocked", [])


def _save_rule_from_chat(c, tag):
    text = f"Don't send Van 2 downtown after 3 ({tag})"
    r = c.post("/agents/dispatch/messages", json={"text": f"Please save this rule: {text}"}, timeout=120)
    assert r.status_code in (200, 201), r.text
    rules = c.get("/memory/rules").json()["rules"]
    mine = [x for x in rules if tag in x["text"]]
    assert mine, f"no rule saved: {str(r.json())[:400]}"
    assert mine[0]["active"] and mine[0]["enforced"]
    return mine[0]["id"]


def _late_downtown_job():
    db = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))[os.environ.get("DB_NAME", "test_database")]
    job = copy.deepcopy(db.requests.find_one({"key": "req-02"})["job"])
    job["stops"][0].update(window_start=915, window_end=960)
    job["stops"][1].update(window_end=1020)
    return job


def _assert_activity_logged(c):
    ev = c.get("/activity").json()["events"]
    assert "Turned off" in ev[0]["line"] and ev[0]["actor"] == "owner", ev[0]
    assert any(e.get("tool") == "save_rule" or "rule" in e["line"].lower() and e["actor"] == "assistant" for e in ev[:10]), ev[:5]


def test_rule_from_chat_blocks_and_toggles(c):
    rid = _save_rule_from_chat(c, f"tscheck-rules-{uuid.uuid4().hex[:6]}")
    job = _late_downtown_job()
    on, blocked = _vans(c, job)
    assert "van-2" not in on and any(b["unit_key"] == "van-2" for b in blocked), (on, blocked)
    assert c.patch(f"/memory/rules/{rid}", json={"active": False}).json()["active"] is False
    off, _ = _vans(c, job)
    assert "van-2" in off, off
    _assert_activity_logged(c)
    assert c.delete(f"/memory/rules/{rid}").status_code == 200
    assert c.delete(f"/memory/rules/{rid}").status_code == 404
