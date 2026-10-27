"""Step 14 quick check: auto-send quotes at once, auto-commits after ~20 s, and customer Accept vs auto-commit books once."""
import asyncio
import sys
import time

import requests

API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/api"
TEXT = "pickup at 3220 Grand Ave Oakland between 1 and 2pm, drop at 4100 Piedmont Ave by 4pm"


def add():
    k = requests.post(f"{API}/inbox", json={"text": TEXT, "source": "email", "sender": "Grand Ave test"}, timeout=60).json()["key"]
    t0 = time.time()
    seen = {}
    st = None
    while time.time() - t0 < 40:
        st = requests.get(f"{API}/customer/{k}").json()
        seen.setdefault(st["status"], round(time.time() - t0, 1))
        if st["status"] == "booked":
            return k, seen, st
        if st["status"] == "quoted" and "race" in sys.argv and "raced" not in seen:
            seen["raced"] = True
            time.sleep(max(0, 20 - (time.time() - t0) + 0.3))  # land the customer Accept on the auto-commit
            r = requests.post(f"{API}/quotes/{st['quote']['key']}/accept", timeout=30)
            seen["customer_accept"] = r.status_code
        time.sleep(0.5)
    return k, seen, st


requests.post(f"{API}/demo/run", timeout=90)
time.sleep(8)
stops0 = {u["key"]: u["stops_count"] for u in requests.get(f"{API}/fleet").json()["units"]}
k, seen, st = add()
print("status first seen at (s):", seen, "| booked_line:", st.get("booked_line"))
print("customer view keys:", sorted(st), sorted(st["quote"] or {}))
stops1 = {u["key"]: u["stops_count"] for u in requests.get(f"{API}/fleet").json()["units"]}
print("stop delta:", {u: stops1[u] - stops0[u] for u in stops0 if stops1[u] != stops0[u]})
n = len([q for q in requests.get(f"{API}/quotes", params={"request_key": k}).json() if q["status"] == "accepted"])
print("accepted quotes for request:", n)
