"""Step 11 quick checks: Reset model-call cost, parse-on-ingest via Add a request with auto-send on, and the Booked event."""
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from pymongo import MongoClient

c = httpx.Client(base_url=os.environ.get("API", "http://localhost:8001/api"), timeout=120)
db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
day = datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
calls = lambda: (db.agent_usage.find_one({"date": day}) or {}).get("model_calls_today", 0)  # noqa: E731
BODY = "pickup 2 boxes at 1300 Clay St Oakland, deliver to 1261 Fallon St by 3pm today"

n0 = calls()
c.post("/demo/reset")
t0 = time.time()
st = []
while time.time() - t0 < 90:
    st = [r["status"] for r in c.get("/inbox").json()["requests"]]
    if "reading" not in st:
        break
    time.sleep(1)
print(f"reset: seeded reads done in {time.time() - t0:.0f}s, model calls {calls() - n0}, statuses {sorted(set(st))}")
print("ai levels:", sorted({(r.get('ai') or {}).get('label') for r in db.requests.find({}, {'ai': 1})} - {None}))
db.businesses.update_many({}, {"$set": {"settings.auto_send_cheapest": True}})
stops0 = {u["key"]: u["stops_count"] for u in c.get("/fleet").json()["units"]}
since = c.get("/events").json()["now"]
t0 = time.time()
r = c.post("/inbox", json={"text": BODY, "source": "email", "sender": "Ana at Clay Street Law"}).json()
print("created:", r["key"], r["status_label"])
row = {}
while time.time() - t0 < 30:
    row = next(x for x in c.get("/inbox").json()["requests"] if x["key"] == r["key"])
    if row["status"] in ("accepted", "declined", "needs_info", "priced", "quoted") and row["status"] != "quoted":
        break
    time.sleep(0.5)
print(f"status {row['status_label']} after {time.time() - t0:.1f}s")
stops1 = {u["key"]: u["stops_count"] for u in c.get("/fleet").json()["units"]}
print("stops delta:", {k: stops1[k] - stops0[k] for k in stops0 if stops1[k] != stops0[k]})
print("events:", [e["text"] for e in c.get("/events", params={"since": since}).json()["events"]])
db.businesses.update_many({}, {"$set": {"settings.auto_send_cheapest": False}})
