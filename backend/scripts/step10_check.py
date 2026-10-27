"""Step 10 checks: savings tally after 2 bookings and 1 undo (Q-800), and Done time-jump tags at a few clock times."""
import os

import httpx
from pymongo import MongoClient

c = httpx.Client(base_url=os.environ.get("API", "http://localhost:8001/api"), timeout=120)
db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
HOLLIS = ("Hi Bayline, can you pick up a box of samples today at 5900 Hollis St, Emeryville and get it to "
          "Emeryville Central Lab, 1400 Powell St, Emeryville by 3pm? Thanks, Ana, Hollis Street Bio")


def truth():
    tot = 0.0
    for q in db.quotes.find({"status": "accepted"}):
        b = q.get("booking") or {}
        tot += max(0.0, (b.get("usual") or 0) - q["price"]) if b.get("usual") else 0
    return round(tot, 2)


def book(key):
    d = c.post(f"/inbox/{key}/read").json()
    o = d["options"]["cards"][0]
    q = c.post(f"/inbox/{key}/send", json={"option_id": o["option_id"]}).json()
    r = c.post(f"/quotes/{q['key']}/accept").json()
    print(f"  booked {key}: {o['unit_name']} ${o['price']} (usual ${o.get('usual')}) -> {r.get('booking', {}).get('toast')}")


c.post("/demo/reset")
print("after reset: tally", c.get("/live").json()["saved_today"])
r = c.post("/inbox", json={"text": HOLLIS, "source": "email", "sender": "Ana at Hollis Street Bio"}).json()
book(r["key"])
print("after booking 1: tally", c.get("/live").json()["saved_today"], "truth", truth())
book("req-02")
print("after booking 2: tally", c.get("/live").json()["saved_today"], "truth", truth())
u = c.post("/engine/undo").json()
print("undo:", u.get("message"))
t = c.get("/live").json()["saved_today"]
print("after undo: tally", t, "truth", truth(), "diff", round(t - truth(), 2))

c.post("/demo/reset")
orig = db.businesses.find_one({}, {"settings.demo_clock_minutes": 1})["settings"]["demo_clock_minutes"]
for clock in (560, 600, 690, 780, 900):
    db.businesses.update_many({}, {"$set": {"settings.demo_clock_minutes": clock}})
    res = c.post("/phones/driver/messages", json={"text": "done"}).json()
    tl = c.get("/units/van-2").json()["timeline"]
    tags = [(x["stop_key"], x["time_shift"]) for x in tl if x.get("time_shift")]
    print(f"clock {clock // 60}:{clock % 60:02d} done {res.get('stop_key')} shifts {res.get('shifts')} | van page tags {tags}")
    print("   phone:", res.get("message"))
db.businesses.update_many({}, {"$set": {"settings.demo_clock_minutes": orig}})
c.post("/demo/reset")
