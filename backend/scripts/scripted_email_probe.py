"""Try candidate scripted demo emails and print which van the engine picks, price, usual and pass-by. Resets data after."""
import os
import sys

import httpx

B = os.environ.get("API", "http://localhost:8001/api")
c = httpx.Client(base_url=B, timeout=120)
TEXTS = sys.argv[1:] or [
    "Hi Bayline, can you pick up 2 boxes of filings today at 1300 Clay St, Oakland and get them to the Fallon Street Courthouse (Fallon St and 12th St, Oakland) by 3pm? Thanks, Ana, Clay Street Law Group",
]
for t in TEXTS:
    r = c.post("/inbox", json={"text": t, "source": "email", "sender": "Probe"}).json()
    key = r.get("key") or r.get("request", {}).get("key")
    d = c.post(f"/inbox/{key}/read").json()
    cards = (d.get("options") or {}).get("cards") or []
    print("\n", t[:90], "| status", d.get("status"), "|", d.get("job_reason"))
    for o in cards:
        pb = o.get("pass_by") or {}
        print("   ", o["labels"], o["unit_name"], o["price"], "usual", o.get("usual"), "pass", pb.get("miles"), o["pickup_label"], o.get("loses_money"))
c.post("/demo/reset")
