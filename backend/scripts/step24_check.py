"""Step 24 quick checks: concurrent accepts, stuck-read re-claim, other-card discount wording, Fire demo toast."""
import asyncio
import os
import subprocess
import sys
import time

import httpx
import pymongo
import requests
from dotenv import load_dotenv

sys.path.insert(0, "/app/backend")
load_dotenv("/app/backend/.env")
API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/api"
db = pymongo.MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
MAYA = ("Maya Chen <maya@baystreetdesign.example>", "Subject: Pickup today, Emeryville to Berkeley\n\nHi Bayline,\n\nCould you pick up a box "
        "of samples today at 5600 Bay St, Emeryville and drop it at 1100 Gilman St, Berkeley by 4pm?\n\nThanks,\nMaya Chen\nBay Street Design")
GILMAN = ("Ana at Telegraph Bio <ana@telegraphbio.example>", "Hi Bayline, can you pick up a box of samples today at 1100 Gilman St, Berkeley "
          "and get it to 700 Parker St, Berkeley by 5pm? Thanks, Ana, Telegraph Bio")


def add(sender, text):
    d = None
    k = requests.post(f"{API}/inbox", json={"text": text, "source": "email", "sender": sender}, timeout=30).json()
    k = k.get("key") or k.get("request", {}).get("key")
    for _ in range(30):
        d = requests.get(f"{API}/inbox/{k}").json()
        if d.get("status") not in ("reading", "new"):
            return k, d
        time.sleep(1)
    return k, d


async def race(qkey):
    async with httpx.AsyncClient(timeout=60) as c:
        a, b = await asyncio.gather(c.post(f"{API}/quotes/{qkey}/accept"), c.post(f"{API}/phones/customer/messages", json={"text": "ok"}))
    return (a.status_code, a.json().get("already_booked"), (a.json().get("detail") or {}).get("message")), \
           (b.status_code, b.json().get("action"), b.json().get("already_booked"), (b.json().get("detail") or {}).get("message"))


requests.post(f"{API}/demo/reset", timeout=60)
requests.put(f"{API}/settings", json={"auto_send_cheapest": False})
from live_api import DEMO_EMAIL, FIRE_TEXT  # noqa: E402

# 3. Options: main cards and discount wording on every "other" card below usual
for sender, text in [MAYA, (f"{DEMO_EMAIL[0]} <{DEMO_EMAIL[1]}>", FIRE_TEXT)]:
    k, d = add(sender, text)
    print(sender.split(" <")[0], "main:", [(c["unit_name"], c["price"], c["customer_line"][:60]) for c in d["options"]["cards"]])
    bad = [c for c in d["options"]["others"] if c["price"] < c["usual"] - 1e-9 and "already passes" not in c["customer_line"]]
    print("   others below usual:", sum(c["price"] < c["usual"] for c in d["options"]["others"]), "| missing discount wording:", len(bad))

# 1. Race: one sent quote, the locked accept and the customer "ok" at the same moment
k, d = add(*GILMAN)
opt = d["options"]["cards"][0]["option_id"]
q = requests.post(f"{API}/inbox/{k}/send", json={"option_id": opt}, timeout=30).json()
qkey = (q.get("quote") or {}).get("key") or db.quotes.find_one({"request_key": k})["key"]
print("race results:", asyncio.run(race(qkey)))
qq = db.quotes.find_one({"key": qkey})
print("quote status:", qq["status"], "| request status:", db.requests.find_one({"key": k})["status"],
      "| quotes for request:", db.quotes.count_documents({"request_key": k}),
      "| booked stops:", db.stops.count_documents({"key": {"$in": (qq.get("booking") or {}).get("stop_keys", [])}}),
      "| stale msgs:", db.phone_messages.count_documents({"phone": "customer", "text": {"$regex": "no longer"}}))

# 2. Stuck read with an old claim from an earlier restart
k2, _ = add(*MAYA)
db.requests.update_one({"key": k2}, {"$set": {"status": "reading", "options": None, "resumed_at": time.time() - 120, "resume_tries": 1}})
requests.put(f"{API}/settings", json={"auto_send_cheapest": True})
t0 = time.time()
subprocess.run(["sudo", "supervisorctl", "restart", "backend"], check=True, stdout=subprocess.DEVNULL)
st = None
for _ in range(40):
    time.sleep(1)
    try:
        st = requests.get(f"{API}/inbox/{k2}", timeout=5).json().get("status")
    except Exception:  # noqa: BLE001
        continue
    if st not in (None, "reading"):
        break
r2 = db.requests.find_one({"key": k2})
print(f"stuck read: {st} {time.time() - t0:.0f}s after restart | resume_tries {r2.get('resume_tries')} | quotes {db.quotes.count_documents({'request_key': k2})}")

# 4. Fire demo email toast
b = {}
time.sleep(12)
requests.post(f"{API}/demo/reset", timeout=60)
requests.post(f"{API}/demo/fire-email", timeout=30)
for _ in range(40):
    b = requests.get(f"{API}/live").json().get("last_booking") or {}
    if (b.get("customer") or "").startswith("Dana"):
        break
    time.sleep(1)
print("TOAST:", b.get("toast"))
