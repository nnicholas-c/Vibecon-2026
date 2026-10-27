"""Step 17 A: auto-send quotes at once, commit_at = +5 s, auto-books at ~5 s; customer Accept racing the commit books once."""
import time
from datetime import datetime

import requests

API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/api"
TEXT = "pickup at 1300 Clay St Oakland, deliver to 1261 Fallon St by 3pm"

requests.post(f"{API}/demo/reset", timeout=90)
st = None
for race in (True,):
    k = requests.post(f"{API}/inbox", json={"text": TEXT, "source": "email", "sender": "Window test"}, timeout=60).json()["key"]
    t0, seen, raced = time.time(), {}, None
    while time.time() - t0 < 30:
        st = requests.get(f"{API}/customer/{k}").json()
        seen.setdefault(st["status"], round(time.time() - t0, 1))
        if st["status"] == "quoted" and "commit" not in seen:
            q = st["quote"]
            seen["commit"] = round((datetime.fromisoformat(q["commit_at"]).timestamp() - time.time()), 1)
            if race:
                time.sleep(max(0, seen["commit"] - 0.05))
                raced = requests.post(f"{API}/quotes/{q['key']}/accept", timeout=30).status_code
        if st["status"] == "booked":
            break
        time.sleep(0.3)
    n = sum(1 for q in requests.get(f"{API}/quotes", params={"request_key": k}).json() if q["status"] == "accepted")
    print(f"race={race}: seen {seen} | customer accept {raced} | accepted quotes {n} | {st.get('booked_line')}")
requests.post(f"{API}/demo/reset", timeout=90)
