"""Step 11 fix check: customer name order in the Booked line, and accepted→booked in /api/inbox."""
import os
import sys
import time

import requests
sys.path.insert(0, "/app/backend")
from phones_api import booking_name  # noqa: E402

q = {"customer": "nz@example.com"}
print(booking_name({"details": [{"key": "customer", "value": "Clay Street Law"}], "sender": "Nick"}, q))
print(booking_name({"details": [], "sender": "Nick Chen"}, q))
print(booking_name({"details": [], "sender": "nz@example.com"}, q))

API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0]
r = requests.post(f"{API}/api/demo/scripted-email", timeout=60)
t0 = time.time()
rows = st = None
for _ in range(30):
    rows = requests.get(f"{API}/api/inbox").json()["requests"]
    st = {x["status"] for x in rows}
    if "booked" in st:
        break
    time.sleep(1)
b = next((x for x in rows if x["status"] == "booked"), None)
print("inbox statuses:", sorted(st), "| booked row label:", b and b["status_label"], "| after", round(time.time() - t0, 1), "s")
if b:
    d = requests.get(f"{API}/api/inbox/{b['key']}").json()
    print("detail status:", d.get("status"))
ev = requests.get(f"{API}/api/events").json()
print("event:", next((e["text"] for e in (ev.get("events", ev) if isinstance(ev, dict) else ev) if e.get("kind") == "booked"), None))
print("openapi:", requests.get(f"{API}/api/openapi.json").status_code)
