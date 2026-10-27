"""Q-53 check: optimize all six vans plus Van 2 with request 1 booked; count window breaks and quoted-time moves."""
import os
import sys

import httpx

API = os.environ["API_URL"].rstrip("/") + "/api"
c = httpx.Client(timeout=120)


def breaks(unit_key, booked=None):
    d = c.get(f"{API}/units/{unit_key}").json()
    bad = [r["customer_name"] for r in d["timeline"] if not (r["window_start"] <= r["arrival"] <= r["window_end"])]
    moved = [k for k, at in (booked or {}).items() for r in d["timeline"] if r["stop_key"] == k and abs(r["arrival"] - at) > 15]
    return bad, moved, d["unit"]["spare_minutes"]


c.post(f"{API}/demo/reset")
total = 0
for u in range(1, 7):
    key = f"van-{u}"
    p = c.post(f"{API}/units/{key}/optimize/preview").json()
    if p.get("proposal_id"):
        c.post(f"{API}/units/{key}/optimize/apply/{p['proposal_id']}")
    bad, _, spare = breaks(key)
    total += len(bad)
    print(f"{key}: {p['message']} | breaks {len(bad)} | spare {spare}")

c.post(f"{API}/demo/reset")
res = c.post(f"{API}/engine/price", json={"request_key": "req-01"}).json()
win = res["winner"]
quoted = {s["ref"]: s["arrival"] for s in win["new_stops"]}
acc = c.post(f"{API}/engine/accept", json={"option_id": win["option_id"]}).json()
stops = c.get(f"{API}/units/van-2").json()["timeline"]
new = [r for r in stops if r["stop_key"] in acc["stop_keys"]]
booked = {r["stop_key"]: quoted[ref] for r, ref in zip(sorted(new, key=lambda r: r["arrival"]), ["p1", "d1"])}
bad, moved, spare = breaks("van-2", booked)
p = c.post(f"{API}/units/van-2/optimize/preview").json()
print(f"van-2 + request 1: auto-optimized {acc.get('optimized')} | then: {p['message']} | breaks {len(bad)} | quoted moves >15 min {len(moved)}")
total += len(bad) + len(moved)
c.post(f"{API}/demo/reset")
print("Q-53 total breaks/moves:", total)
sys.exit(1 if total else 0)
