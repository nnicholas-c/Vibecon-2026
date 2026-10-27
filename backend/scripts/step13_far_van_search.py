"""Throwaway: search scripted-email candidates for two cards on different vans with a clear price gap (Reset before each)."""
import sys
import time

import requests

API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/api"
C = [
    ("4900 Clarke St, Oakland", "3000 Telegraph Ave, Berkeley", "4pm"),
    ("5100 Racine St, Oakland", "1900 San Pablo Ave, Berkeley", "4:30pm"),
    ("3000 Telegraph Ave, Berkeley", "1900 San Pablo Ave, Berkeley", "4:30pm"),
    ("740 Ashby Ave, Berkeley", "1907 San Pablo Ave, Berkeley", "4:30pm"),
    ("680 40th St, Oakland", "5141 Racine St, Oakland", "3pm"),
    ("5800 Shellmound St, Emeryville", "1300 Clay St, Oakland", "1pm"),
    ("6400 Christie Ave, Emeryville", "2600 Tenth St, Berkeley", "10:30am"),
    ("2700 San Pablo Ave, Berkeley", "4100 Piedmont Ave, Oakland", "4pm"),
]
pick = [C[int(i)] for i in sys.argv[1:]] or C
for pu, do, by in pick:
    requests.post(f"{API}/demo/reset", timeout=90)
    time.sleep(8)
    text = f"Hi Bayline, can you pick up a box of samples today at {pu} and get it to {do} by {by}? Thanks, Ana, Hollis Street Bio"
    key = requests.post(f"{API}/inbox", json={"text": text, "source": "email", "sender": "Ana at Hollis Street Bio"}, timeout=60).json()["key"]
    d = None
    for _ in range(40):
        d = requests.get(f"{API}/inbox/{key}").json()
        if d["status"] != "reading":
            break
        time.sleep(1)
    cards = [(c["unit_name"], c["price"], "/".join(c["labels"])) for c in ((d.get("options") or {}).get("cards") or [])]
    others = [(c["unit_name"], c["price"]) for c in ((d.get("options") or {}).get("others") or [])]
    gap = (max(p for _, p, _ in cards) - min(p for _, p, _ in cards)) if len({u for u, _, _ in cards}) > 1 else 0
    print(f"{pu} -> {do} by {by} | {d['status']} | cards {cards} | others {others} | gap {gap}", flush=True)
