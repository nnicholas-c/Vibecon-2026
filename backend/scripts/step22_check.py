"""Step 22: Maya and Dana after Reset, plus non-request emails through handle_message (no entry, no reply)."""
import asyncio
import sys
import time
import uuid

import requests

sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv  # noqa: E402
load_dotenv("/app/backend/.env")

API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/api"
MAYA = ("Maya Chen <maya@baystreetdesign.example>", "Subject: Pickup today, Emeryville to Berkeley\n\nHi Bayline,\n\nCould you pick up a box "
        "of samples today at 5600 Bay St, Emeryville and drop it at 1100 Gilman St, Berkeley by 4pm?\n\nThanks,\nMaya Chen\nBay Street Design")


def price(sender, text):
    body = {"text": text, "source": "email", **({"sender": sender} if sender else {})}
    k = requests.post(f"{API}/inbox", json=body, timeout=30).json()
    k = k.get("key") or k.get("request", {}).get("key")
    d = {}
    for _ in range(30):
        d = requests.get(f"{API}/inbox/{k}").json()
        if d.get("status") not in ("reading", "new"):
            break
        time.sleep(1)
    o = d["options"]
    return [(c["unit_name"], c["price"]) for c in o["cards"]], [(c["unit_name"], c["price"]) for c in o["others"]]


async def non_requests():
    from core import BKEY, db
    from google_api import handle_message
    out = []
    for subj, text in [("Lunch on Friday?", "Hey, are you free for lunch on Friday? I'll stop by around noon."),
                       ("Weekend run", "Want to go for a run this weekend? We could do the route by the lake."),
                       ("Your receipt", "Thanks for your order. Your package total was $42.10.")]:
        mid = f"test-{uuid.uuid4().hex[:10]}"
        before = (await db.requests.count_documents({}), await db.events.count_documents({}), await db.gmail_sent.count_documents({}))
        res = await handle_message({"id": mid, "thread_id": None, "rfc_id": None, "references": "", "subject": subj, "from_name": "A Friend",
                                    "from_email": "friend@example.com", "files": [], "text": text, "internal_ms": int(time.time() * 1000)}, None)
        after = (await db.requests.count_documents({}), await db.events.count_documents({}), await db.gmail_sent.count_documents({}))
        out.append((subj, res, "no entry/activity/reply" if before == after else f"CHANGED {before}->{after}", BKEY))
    return out

requests.post(f"{API}/demo/reset", timeout=60)
requests.put(f"{API}/settings", json={"auto_send_cheapest": False})
print("Maya:", price(*MAYA))
from live_api import DEMO_EMAIL, FIRE_TEXT  # noqa: E402
print("Dana:", price(f"{DEMO_EMAIL[0]} <{DEMO_EMAIL[1]}>", FIRE_TEXT))
requests.put(f"{API}/settings", json={"auto_send_cheapest": True})
for row in asyncio.run(non_requests()):
    print("non-request:", row[:3])
