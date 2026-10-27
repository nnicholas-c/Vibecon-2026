"""Step 15 quick check: undated texts land on the demo day, tomorrow stays next day, confirmations, booked-by labels."""
import asyncio
import sys
import time

import requests

sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv  # noqa: E402
load_dotenv("/app/backend/.env")

API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/api"
UNDATED = ["pickup at 3220 Grand Ave Oakland between 1 and 2pm, drop at 4100 Piedmont Ave by 4pm",
           "Can you grab a package from 5100 Racine St, Oakland and take it to 1900 San Pablo Ave, Berkeley by 4:30pm?",
           "Pick up 2 boxes at 1300 Clay St Oakland, deliver to 1261 Fallon St by 3pm"]
TOMORROW = "Tomorrow: pickup at 3220 Grand Ave Oakland, drop at 4100 Piedmont Ave by 4pm"


def add(text, who):
    k = requests.post(f"{API}/inbox", json={"text": text, "source": "email", "sender": who}, timeout=60).json()["key"]
    d = None
    for _ in range(60):
        d = requests.get(f"{API}/inbox/{k}").json()
        if d["status"] not in ("reading", "quoted") or (d["status"] == "quoted" and "--wait" not in sys.argv):
            return d
        time.sleep(1)
    return d


def stage():
    requests.post(f"{API}/demo/run", timeout=90)
    time.sleep(8)
    out = []
    for i, t in enumerate(UNDATED):
        d = add(t, f"Undated {i + 1}")
        q = next(x for x in requests.get(f"{API}/quotes", params={"request_key": d["key"]}).json() if x["status"] == "sent")
        how = "customer" if i == 0 else "auto"
        if how == "customer":
            requests.post(f"{API}/quotes/{q['key']}/accept", timeout=30)
        out.append((d["key"], q, how, d["job"]["frequency"]))
    t0 = time.time()
    while time.time() - t0 < 30 and any(requests.get(f"{API}/inbox/{k}").json()["status"] != "booked" for k, *_ in out):
        time.sleep(1)
    demo = requests.get(f"{API}/settings").json()["settings"]
    for k, q, how, freq in out:
        d = requests.get(f"{API}/inbox/{k}").json()
        unit = q["unit_key"]
        tl = requests.get(f"{API}/units/{unit}").json()["timeline"]
        new = [s["customer_name"] for s in tl if "New" in (s.get("tags") or [])]
        print(f"{k}: date {freq.get('date')} | {d['status']} | {d['booked_by']} | on today's {unit} page with New: {len(new)} stops")
    msgs = [m["text"] for m in requests.get(f"{API}/phones").json().get("customer", []) if m["text"].startswith("Booked.")]
    print("customer phone confirmations:", len(msgs), "|", msgs[-1] if msgs else None)
    return demo


async def gmail_stub():
    import google_api as g
    import phones_api as p
    from core import db, BKEY
    sent = []

    async def fake_send(req, html, text):
        if await g.blocked_address(req["gmail"]["from_email"]):
            raise PermissionError("blocked")
        sent.append((req["gmail"]["thread_id"], text))
        await db.gmail_sent.insert_one({"business_key": BKEY, "message_id": "stub-sent-1", "thread_id": req["gmail"]["thread_id"], "at": time.time()})
        return "gmail"
    g.send_in_thread = fake_send
    q = await db.quotes.find_one({"business_key": BKEY, "status": "accepted"}, {"_id": 0})
    req = {"gmail": {"thread_id": "thr-1", "from_email": "nick@example.com", "subject": "Pickup"}}
    await p.confirm_booking(req, q)
    print("gmail confirmation (stubbed send):", sent, "| quote.confirmation:", (await db.quotes.find_one({"key": q["key"]}))["confirmation"]["via"])
    print("own reply re-ingested?", await g.ingest_ids({}, "t", ["stub-sent-1"]))
    blocked = None
    for coll in ("prospects", "directory"):
        for f in ("email", "contact_email", "contact"):
            d = await db[coll].find_one({"business_key": BKEY, f: {"$regex": "@"}}, {f: 1})
            blocked = blocked or (d and d[f])
    print("blocked sample:", blocked)
    if blocked:
        await p.confirm_booking({"gmail": {"thread_id": "thr-2", "from_email": blocked, "subject": "x"}}, q)
        ev = await db.events.find_one({"text": {"$regex": "^Confirmation email didn't send"}}, sort=[("ts", -1)])
        print("blocked address -> via:", (await db.quotes.find_one({"key": q["key"]}))["confirmation"]["via"], "| activity:", ev and ev["text"])
    await db.gmail_sent.delete_many({"message_id": "stub-sent-1"})


stage()
t = requests.post(f"{API}/inbox", json={"text": TOMORROW, "source": "email", "sender": "Tomorrow test"}, timeout=60).json()["key"]
time.sleep(6)
print("tomorrow ->", requests.get(f"{API}/inbox/{t}").json()["job"]["frequency"].get("date"))
asyncio.run(gmail_stub())
print("openapi:", requests.get(f"{API}/openapi.json").status_code)
