"""Step 9 Q-750: driver Done at 3 demo-clock times marks the stop the van is at or heading to; later stops re-time; 'No stop' after the day."""
import os

import httpx
from pymongo import MongoClient

c = httpx.Client(base_url=os.environ.get("API", "http://localhost:8001/api"), timeout=120)
db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
wrong = 0


def timeline(v):
    return c.get(f"/units/{v}").json()["timeline"]


def set_clock(m):
    db.businesses.update_many({}, {"$set": {"settings.demo_clock_minutes": m}})


c.post("/demo/reset")
orig = db.businesses.find_one({}, {"settings.demo_clock_minutes": 1})["settings"]["demo_clock_minutes"]
for clock in (600, 780, 1050):
    set_clock(clock)
    tl = timeline("van-2")
    done = {r["stop_key"] for r in tl if "Done" in (r.get("tags") or [])}
    expect = next((r for r in tl if r["stop_key"] not in done and r["departure"] > clock), None)
    res = c.post("/phones/driver/messages", json={"text": "done"}).json()
    got = res.get("stop_key")
    ok = (expect is None and res.get("action") == "none") or (expect is not None and got == expect["stop_key"])
    wrong += 0 if ok else 1
    after = timeline("van-2")
    row = next((r for r in after if r["stop_key"] == got), None)
    nxt = after[after.index(row) + 1] if row and after.index(row) + 1 < len(after) else None
    before_next = next((r for r in tl if nxt and r["stop_key"] == nxt["stop_key"]), None)
    print(f"clock {clock // 60}:{clock % 60:02d} expect {expect and expect['stop_key']} ({expect and expect['arrival_label']}) got {got} -> {'PASS' if ok else 'FAIL'}")
    print("   reply:", res.get("message"))
    if row:
        print(f"   done stop departs {row['departure']:.0f} (= clock {clock}); next {nxt and nxt['stop_key']} arrival {before_next and before_next['arrival_label']} -> {nxt and nxt['arrival_label']}; tags {row.get('tags')}")
set_clock(orig)
c.post("/demo/reset")
print("wrong stops marked:", wrong)
