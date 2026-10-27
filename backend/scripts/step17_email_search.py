"""Throwaway: best presenter email for the Task 9 seed (Reset before each, auto-send off, same reader/engine path)."""
import time

import requests

API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/api"
SIGN = "Thanks,\nMaya Chen\nTelegraph Bio"
C = [
    ("3000 Telegraph Ave, Berkeley", "1900 San Pablo Ave, Berkeley", "4:30pm"),
    ("5600 Bay St, Emeryville", "1100 Gilman St, Berkeley", "4pm"),
    ("600 40th St, Oakland", "3100 Telegraph Ave, Berkeley", "3pm"),
    ("4900 Clarke St, Oakland", "2900 Telegraph Ave, Berkeley", "3pm"),
    ("700 Parker St, Berkeley", "1100 Gilman St, Berkeley", "5pm"),
    ("5100 Racine St, Oakland", "1900 San Pablo Ave, Berkeley", "4:30pm"),
    ("1100 Gilman St, Berkeley", "700 Parker St, Berkeley", "5pm"),
    ("5600 Bay St, Emeryville", "4900 Clarke St, Oakland", "1pm"),
    ("3000 Telegraph Ave, Berkeley", "5600 Bay St, Emeryville", "3pm"),
]
for pu, do, by in C:
    requests.post(f"{API}/demo/reset", timeout=90)
    s = requests.get(f"{API}/settings").json()["settings"]
    requests.put(f"{API}/settings", json={**s, "auto_send_cheapest": False})
    body = f"Hi Bayline,\n\nCould you pick up a box of samples today at {pu} and drop it at {do} by {by}?\n\n{SIGN}"
    key = requests.post(f"{API}/inbox", json={"text": f"Subject: Pickup today\n\n{body}", "source": "email", "sender": "Maya Chen"}, timeout=60).json()["key"]
    d = None
    for _ in range(40):
        d = requests.get(f"{API}/inbox/{key}").json()
        if d["status"] != "reading":
            break
        time.sleep(1)
    cards = [(c["unit_name"], c["price"], "/".join(c["labels"])) for c in ((d.get("options") or {}).get("cards") or [])]
    gap = (max(p for _, p, _ in cards) - min(p for _, p, _ in cards)) if len({u for u, _, _ in cards}) > 1 else 0
    print(f"{pu} -> {do} by {by} | {d['status']} | {cards} | gap {gap}", flush=True)
requests.post(f"{API}/demo/reset", timeout=90)
