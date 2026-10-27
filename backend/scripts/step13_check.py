"""Step 13 quick check: scripted cards + gap, auto-book toast, booked_seconds truth, chat labels, import sync line."""
import time
from datetime import datetime

import requests

API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/api"


def wait(key):
    d = None
    for _ in range(40):
        d = requests.get(f"{API}/inbox/{key}").json()
        if d["status"] != "reading":
            return d
        time.sleep(1)
    return d


def ask(text):
    t = requests.post(f"{API}/agents/dispatch/messages", json={"text": text}, timeout=120).json()["turns"][-1]
    return [(c.get("label"), c.get("stop_name")) for c in t["tool_calls"] if c["name"] == "explain_stop"], t["text"][:160]


requests.post(f"{API}/demo/reset", timeout=90)
time.sleep(8)
k = requests.post(f"{API}/demo/scripted-email", timeout=90).json()["request_key"]
d = wait(k)
cards = [(c["unit_name"], c["price"]) for c in d["options"]["cards"]]
print("scripted (auto-send off):", d["status"], cards, "gap", max(p for _, p in cards) - min(p for _, p in cards), "| booked_seconds:", d.get("booked_seconds"))

g = wait(requests.post(f"{API}/inbox", json={"text": "pickup at 3220 Grand Ave Oakland between 1 and 2pm, drop at 4100 Piedmont Ave by 4pm",
                                               "source": "email", "sender": "Grand Ave test"}, timeout=60).json()["key"])
print("grand ave label:", ask("Why is the Grand Ave pickup on Van 2 where it is?"))
print("seeded label:", ask("Why is Quarry Copy Center on Van 2 where it is?"))

requests.post(f"{API}/demo/run", timeout=90)
time.sleep(8)
k = requests.post(f"{API}/demo/scripted-email", timeout=90).json()["request_key"]
d = wait(k)
live = requests.get(f"{API}/live").json().get("last_booking") or {}
print("auto-book:", d["status"], "| toast:", live.get("toast"), "| ruler:", live.get("ruler"))
truth = round(datetime.fromisoformat(d["booked_at"]).timestamp() - datetime.fromisoformat(d["received_at"]).timestamp())
row = next(r for r in requests.get(f"{API}/inbox").json()["requests"] if r["key"] == k)
print("booked_seconds:", d["booked_seconds"], "| truth:", truth, "| row:", row["booked_seconds"],
      "| unbooked rows with a timer:", sum(1 for r in requests.get(f"{API}/inbox").json()["requests"] if r["status"] != "booked" and r["booked_seconds"] is not None))
print("booked label:", ask("Why is the Telegraph Ave pickup on Van 2 where it is?"))
src = requests.get(f"{API}/import/sources").json()
print("import:", src["sheet_connected"], src["last_auto_sync"])
print("openapi:", requests.get(f"{API}/openapi.json").status_code)
