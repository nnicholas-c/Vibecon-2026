"""Step 17 F: the presenter's real email, through the Gmail ingest + reader + engine path (no email sent)."""
import os
import sys
import time
import uuid

import requests

API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/api"
sys.path.insert(0, "/app/backend")

SUBJECT = "Pickup today, Emeryville to Berkeley"
BODY = ("Hi Bayline,\n\nCould you pick up a box of samples today at 5600 Bay St, Emeryville and drop it at "
        "1100 Gilman St, Berkeley by 4pm?\n\nThanks,\nMaya Chen\nBay Street Design")

requests.post(f"{API}/demo/reset", timeout=60)
s = requests.get(f"{API}/settings").json()["settings"]
requests.put(f"{API}/settings", json={"auto_send_cheapest": False})


t0 = time.time()
key = requests.post(f"{API}/inbox", json={"text": f"Subject: {SUBJECT}\n\n{BODY}", "source": "email",
                    "sender": "Maya Chen <maya@baystreetdesign.example>"}, timeout=30).json()
key = key.get("key") or key.get("request", {}).get("key")
d = st = None
for _ in range(30):
    d = requests.get(f"{API}/inbox/{key}").json()
    st = d.get("request", d).get("status")
    if st not in ("reading", "new"):
        break
    time.sleep(1)
print(f"status {st} after {time.time() - t0:.1f}s")
o = d.get("options") or {}
for c in (o.get("cards") or []) + (o.get("others") or []):
    print(" ", c.get("label") or c.get("title"), "|", c.get("unit_name"), "| $", c.get("price"), "| pickup", c.get("pickup_label"),
          "|", (c.get("reasons") or [""])[0][:110])
print("customer line:", (d.get("customer_line") or o.get("customer_line") or "")[:240])
requests.put(f"{API}/settings", json={"auto_send_cheapest": True})
