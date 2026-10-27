"""Step 21: engine/options snapshot (Reset + three requests, auto-send off) for a before/after diff."""
import json
import sys
import time

import requests

API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/api"
OUT = sys.argv[1]
REQS = [
    ("Grand Ave", None, "pickup at 3220 Grand Ave Oakland between 1 and 2pm, drop at 4100 Piedmont Ave by 4pm"),
    ("Gilman->Parker", "Ana at Telegraph Bio <ana@telegraphbio.example>",
     "Hi Bayline, can you pick up a box of samples today at 1100 Gilman St, Berkeley and get it to 700 Parker St, Berkeley by 5pm? Thanks, Ana, Telegraph Bio"),
    ("Bay St->Gilman", "Maya Chen <maya@baystreetdesign.example>",
     "Subject: Pickup today, Emeryville to Berkeley\n\nHi Bayline,\n\nCould you pick up a box of samples today at 5600 Bay St, Emeryville and drop it at 1100 Gilman St, Berkeley by 4pm?\n\nThanks,\nMaya Chen\nBay Street Design"),
]
VOLATILE = {"option_id", "created_at", "updated_at", "received_at", "read_at", "priced_at", "ts", "at", "elapsed_ms", "read_ms",
            "price_ms", "key", "request_key", "source_key"}


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in sorted(o.items()) if k not in VOLATILE}
    if isinstance(o, list):
        return [clean(v) for v in o]
    return o


requests.post(f"{API}/demo/reset", timeout=60)
requests.put(f"{API}/settings", json={"auto_send_cheapest": False})
snap = {"fleet": clean(requests.get(f"{API}/fleet").json())}
for name, sender, text in REQS:
    body = {"text": text, "source": "email", **({"sender": sender} if sender else {})}
    r = requests.post(f"{API}/inbox", json=body, timeout=30).json()
    k = r.get("key") or r.get("request", {}).get("key")
    d = None
    for _ in range(30):
        d = requests.get(f"{API}/inbox/{k}").json()
        if d.get("request", d).get("status") not in ("reading", "new"):
            break
        time.sleep(1)
    req = d.get("request", d)
    snap[name] = {"status": req.get("status"), "parsed": clean(req.get("parsed") or req.get("fields")), "options": clean(d.get("options"))}
requests.put(f"{API}/settings", json={"auto_send_cheapest": True})
json.dump(snap, open(OUT, "w"), indent=1, sort_keys=True)
for name, _, _ in REQS:
    o = snap[name]["options"] or {}
    print(name, snap[name]["status"], [(c.get("title"), c.get("unit_name"), c.get("price")) for c in o.get("cards", [])])
