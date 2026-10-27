"""Snapshot run-all on the seeded requests plus the scripted Hollis St demo email. Usage: runall_snapshot.py out.json [compare.json]"""
import json
import os
import sys

import httpx

B = os.environ.get("API", "http://localhost:8001/api")
c = httpx.Client(base_url=B, timeout=180)
HOLLIS = ("Hi Bayline, can you pick up a box of samples today at 5900 Hollis St, Emeryville and get it to "
          "Emeryville Central Lab, 1400 Powell St, Emeryville by 3pm? Thanks, Ana, Hollis Street Bio")


def snap():
    c.post("/demo/reset")
    r = c.post("/inbox", json={"text": HOLLIS, "source": "email", "sender": "Ana at Hollis Street Bio"}).json()
    c.post(f"/inbox/{r['key']}/read")
    out = {}
    for row in c.post("/engine/run-all").json()["results"]:
        w = row.get("winner") or {}
        cards = [(" + ".join(o["labels"]), o["unit_name"], o["price"], o["pickup_label"]) for o in ((row.get("options") or {}).get("cards") or [])]
        out[str(row["number"])] = {"van": w.get("unit_name"), "price": w.get("price"), "usual": w.get("usual"),
                                   "added_min": w.get("added_minutes"), "added_mi": w.get("added_miles"),
                                   "pickup": (w.get("new_stops") or [{}])[0].get("arrival_label"),
                                   "reason": row.get("reason"), "cards": cards}
    c.post("/demo/reset")
    return out


res = snap()
json.dump(res, open(sys.argv[1], "w"), indent=1)
if len(sys.argv) > 2:
    old = json.load(open(sys.argv[2]))
    for k in sorted(res, key=int):
        a, b = old.get(k, {}), res[k]
        keys = ("van", "price", "usual", "added_min", "added_mi", "pickup", "reason")
        diff = {f: (a.get(f), b.get(f)) for f in keys if a.get(f) != b.get(f)}
        print(f"#{k}: " + ("same" if not diff else "; ".join(f"{f} {x} -> {y}" for f, (x, y) in diff.items())))
        if a.get("cards") != b.get("cards"):
            print(f"    cards {a.get('cards')}\n       -> {b.get('cards')}")
else:
    for k in sorted(res, key=int):
        print(k, res[k])
