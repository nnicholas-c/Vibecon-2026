"""Throwaway: far-van candidates on the Task 9 seed, reporting cards AND other-van option cards (Reset before each, auto-send off)."""
import sys
import time

import requests

API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/api"
C = [  # (pickup, drop-off, deadline-or-window phrase) with explicit times / narrow windows
    ("3000 Telegraph Ave, Berkeley", "1900 San Pablo Ave, Berkeley", "by noon, pickup between 10:15 and 10:30am"),
    ("1100 Gilman St, Berkeley", "700 Parker St, Berkeley", "by 2pm, pickup between 12:15 and 12:30pm"),
    ("700 Parker St, Berkeley", "1100 Gilman St, Berkeley", "by 1pm, pickup between 11:30 and 11:45am"),
    ("4900 Clarke St, Oakland", "3000 Telegraph Ave, Berkeley", "by 4pm, pickup between 2:15 and 2:30pm"),
    ("600 40th St, Oakland", "1500 Cedar St, Berkeley", "by 5pm, pickup between 3 and 3:15pm"),
    ("1500 Cedar St, Berkeley", "2100 University Ave, Berkeley", "by 2pm, pickup between 12:30 and 12:45pm"),
    ("2700 Webster St, Berkeley", "3000 Telegraph Ave, Berkeley", "by 1pm, pickup between 11:30 and 11:45am"),
    ("126 Water St, Oakland", "1000 Broadway, Oakland", "by 1pm, pickup between 11 and 11:15am"),
    ("1100 Gilman St, Berkeley", "700 Parker St, Berkeley", "by 5:30pm, pickup at 4:30pm"),
    ("3000 Telegraph Ave, Berkeley", "1900 San Pablo Ave, Berkeley", "by 6pm, pickup between 4:30 and 5pm"),
]
pick = [C[int(i)] for i in sys.argv[1:]] or C
for pu, do, by in pick:
    requests.post(f"{API}/demo/reset", timeout=90)
    s = requests.get(f"{API}/settings").json()["settings"]
    requests.put(f"{API}/settings", json={**s, "auto_send_cheapest": False})
    body = f"Hi Bayline,\n\nCould you pick up a box of samples today at {pu} and drop it at {do} {by}?\n\nThanks,\nMaya Chen\nTelegraph Bio"
    key = requests.post(f"{API}/inbox", json={"text": body, "source": "email", "sender": "Maya Chen"}, timeout=60).json()["key"]
    t0 = time.time()
    d = None
    for _ in range(40):
        d = requests.get(f"{API}/inbox/{key}").json()
        if d["status"] != "reading":
            break
        time.sleep(1)
    o = d.get("options") or {}
    cards = [(c["unit_name"], c["price"], "/".join(c["labels"])) for c in o.get("cards") or []]
    others = [(c["unit_name"], c["price"]) for c in o.get("others") or []]
    print(f"{pu} -> {do} by {by} | {d['status']} {time.time() - t0:.0f}s {d.get('ai', {}).get('level')} | cards {cards} | others {others}", flush=True)
requests.post(f"{API}/demo/reset", timeout=90)
