"""Step 17 C4: ask about the Grand Ave pickup before and after accepting it (auto-send off), report replies and chips."""
import time

import requests

API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/api"
Q = "Why is the Grand Ave pickup on Van 2 where it is?"


def ask():
    t = requests.post(f"{API}/agents/dispatch/messages", json={"text": Q}, timeout=120).json()["turns"][-1]
    return [(c.get("label"), c.get("stop_name")) for c in t["tool_calls"] if c["name"] == "explain_stop"], t["text"]


requests.post(f"{API}/demo/reset", timeout=90)
s = requests.get(f"{API}/settings").json()["settings"]
requests.put(f"{API}/settings", json={**s, "auto_send_cheapest": False})
k = requests.post(f"{API}/inbox", json={"text": "pickup at 3220 Grand Ave Oakland between 1 and 2pm, drop at 4100 Piedmont Ave by 4pm",
                                       "source": "email", "sender": "Grand Ave test"}, timeout=60).json()["key"]
d = None
for _ in range(30):
    d = requests.get(f"{API}/inbox/{k}").json()
    if d["status"] != "reading":
        break
    time.sleep(1)
card = d["options"]["cards"][0]
print("card:", card["unit_name"], card["price"])
print("BEFORE:", ask())
q = requests.post(f"{API}/inbox/{k}/send", json={"option_id": card["option_id"]}, timeout=30).json()
print("accept:", requests.post(f"{API}/quotes/{q['key']}/accept", timeout=30).status_code)
print("AFTER:", ask())
requests.put(f"{API}/settings", json={**s, "auto_send_cheapest": True})
