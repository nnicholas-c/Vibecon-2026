"""Step 12 CHECK: Reset, add the Grand Ave request, compare the two cards, ask the agent; plus landing and Hollis numbers."""
import time

import requests

API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/api"
TEXT = "pickup at 3220 Grand Ave Oakland between 1 and 2pm, drop at 4100 Piedmont Ave by 4pm"

print("reset:", requests.post(f"{API}/demo/reset", timeout=90).status_code)
s = requests.get(f"{API}/settings").json()["settings"]
print("settings:", {k: s[k] for k in ("floor_one_off", "usual_one_off", "markup_pct", "wage_per_hour", "cost_per_mile", "auto_send_cheapest")})
lp = requests.get(f"{API}/landing/price").json()
print("landing:", {k: lp[k] for k in ("cost", "cost_with_markup", "floor", "usual", "offer")})

key = requests.post(f"{API}/inbox", json={"text": TEXT, "source": "email", "sender": "Grand Ave test"}, timeout=60).json()["key"]
d = None
for _ in range(40):
    d = requests.get(f"{API}/inbox/{key}").json()
    if d["status"] != "reading":
        break
    time.sleep(1)
cards = (d.get("options") or {}).get("cards") or []
print("status:", d["status"])
for c in cards:
    print(f"  {c['unit_name']} ${c['price']} {c['labels']} +{c['added_minutes']} min +{c['added_miles']} mi | {c['customer_line']}")
prices = [c["price"] for c in cards]
print("PASS cards" if len(prices) == 2 and len(set(prices)) == 2 and 35 not in prices else "FAIL cards", prices)

r = requests.post(f"{API}/agents/dispatch/messages", json={"text": "Why is the Grand Ave pickup on Van 2 where it is?"}, timeout=120).json()
reply = r.get("answer") or r.get("reply") or r
print("agent:", reply)
