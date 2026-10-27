"""Step 6 check: area/time rules exclude options, toggling restores them, activity logs rule changes. Uses the live API."""
import copy
import os
import sys

import httpx
from pymongo import MongoClient

B = os.environ.get("API", "http://localhost:8001/api")
c = httpx.Client(base_url=B, timeout=60)
db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
fails = []


def check(ok, what):
    print(("PASS " if ok else "FAIL ") + what)
    if not ok:
        fails.append(what)


def vans(job):
    opts = c.post("/engine/price", json={"job": job}).json()["options"]
    return {x["unit_key"] for x in opts["cards"] + opts["others"]}, opts.get("blocked", [])


job = copy.deepcopy(db.requests.find_one({"key": "req-02"})["job"])
job["stops"][0].update(window_start=915, window_end=960)
job["stops"][1].update(window_end=1020)
before, _ = vans(job)
print("vans offered with no rules:", sorted(before))
check("van-2" in before or len(before) > 0, "downtown 3:15pm job has options")
target = "van-2" if "van-2" in before else sorted(before)[0]
text = f"Don't send {target.replace('van-', 'Van ')} downtown after 3"
from core import BKEY  # noqa: E402
rid = str(db.agent_rules.insert_one({"business_id": BKEY, "text": text, "active": True, "created_at": "2026-10-25T00:00:00+00:00"}).inserted_id)
after, blocked = vans(job)
check(target not in after, f"{target} excluded while rule on")
check(any(b["unit_key"] == target and text in b["reason"] for b in blocked), "blocked row says why")
r = c.patch(f"/memory/rules/{rid}", json={"active": False})
check(r.status_code == 200 and r.json()["active"] is False, "toggle off persists")
again, blocked2 = vans(job)
check(target in again and not blocked2, f"{target} offered again when rule off")
rules = c.get("/memory/rules").json()["rules"]
check(any(x["id"] == rid and x["enforced"] for x in rules), "rule listed and enforced")
check(c.delete(f"/memory/rules/{rid}").status_code == 200, "delete rule")
check(all(x["id"] != rid for x in c.get("/memory/rules").json()["rules"]), "rule gone after delete")
ev = c.get("/activity").json()["events"]
check(ev and "Deleted the rule" in ev[0]["line"] and ev[0]["actor"] == "owner", "activity newest-first with rule change")
sys.exit(1 if fails else 0)
