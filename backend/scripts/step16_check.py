"""Step 16 quick check: Reset is exact (REQ-1100), makes zero model calls, then Grand Ave cards and Fire demo email."""
import os
import time

import requests
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/api"
calls = lambda: sum(d.get("model_calls_today", 0) for d in db.agent_usage.find())  # noqa: E731

c0 = calls()
print("reset:", requests.post(f"{API}/demo/reset", timeout=90).status_code)
time.sleep(3)
s = requests.get(f"{API}/settings").json()["settings"]
fleet = requests.get(f"{API}/fleet").json()
gaps = {}
for u in fleet["units"]:
    tl = requests.get(f"{API}/units/{u['key']}").json()["timeline"]
    done = [r for r in tl if "Done" in (r.get("tags") or [])]
    early = [r for r in tl if r.get("arrival", 0) < 600]
    print(f"{u['key']}: {len(tl)} stops, {len(done)} Done, before 10:00am {len(early)} |",
          [(r["arrival_label"], r["address"].split(",")[0]) for r in tl])
print("clock:", s["demo_clock_minutes"], "| auto_send:", s["auto_send_cheapest"], "| floor:", s["floor_one_off"], "| usual:", s["usual_one_off"])
print("requests:", db.requests.count_documents({}), "| events:", db.events.count_documents({}), "| rules:", db.agent_rules.count_documents({}),
      "| new_stops:", fleet["totals"]["new_stops"], "| saved:", requests.get(f"{API}/live").json()["saved_today"])
print("reset model calls:", calls() - c0)

# Grand Ave cards with auto-send off, then restore
requests.put(f"{API}/settings", json={**s, "auto_send_cheapest": False})
k = requests.post(f"{API}/inbox", json={"text": "pickup at 3220 Grand Ave Oakland between 1 and 2pm, drop at 4100 Piedmont Ave by 4pm",
                                       "source": "email", "sender": "Grand Ave test"}, timeout=60).json()["key"]
d = None
for _ in range(30):
    d = requests.get(f"{API}/inbox/{k}").json()
    if d["status"] != "reading":
        break
    time.sleep(1)
print("grand ave cards:", [(c["unit_name"], c["price"], c["labels"], c["customer_line"]) for c in d["options"]["cards"]])
requests.post(f"{API}/demo/reset", timeout=90)
print("openapi:", requests.get(f"{API}/openapi.json").status_code)
