"""Step 23 item 3 dry run: what Maya/Dana pass-by lines become if pass_by ignores stops already done before the clock."""
import asyncio
import sys
import time

import requests

sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv  # noqa: E402
load_dotenv("/app/backend/.env")

API = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/api"
MAYA = ("Maya Chen <maya@baystreetdesign.example>", "Subject: Pickup today, Emeryville to Berkeley\n\nHi Bayline,\n\nCould you pick up a box "
        "of samples today at 5600 Bay St, Emeryville and drop it at 1100 Gilman St, Berkeley by 4pm?\n\nThanks,\nMaya Chen\nBay Street Design")


def add(sender, text):
    k = requests.post(f"{API}/inbox", json={"text": text, "source": "email", "sender": sender}, timeout=30).json()
    k = k.get("key") or k.get("request", {}).get("key")
    for _ in range(30):
        d = requests.get(f"{API}/inbox/{k}").json()
        if d.get("status") not in ("reading", "new"):
            return k
        time.sleep(1)
    return k


def show(tag, o):
    for c in o["cards"] + o["others"]:
        pb = c.get("pass_by") or {}
        print(f"  {tag} {c['unit_name']} ${c['price']} pickup {c.get('pickup_label')} | passes {pb.get('miles')} mi at {pb.get('time')} | {c['customer_line']}")


async def main(keys):
    from core import db, get_business
    import engine.insertion as ins
    from engine_api import price_job
    from engine.timing import fmt_time
    orig = ins.pass_by
    biz = await get_business()
    for k in keys:
        r = await db.requests.find_one({"key": k})
        print(r["sender"], "NOW")
        show("now", r["options"])
        ins.pass_by = lambda name, base, first: orig(name, _Future(base), first)
        o = (await price_job(r["job"], biz, request_key=k))["options"]
        ins.pass_by = orig
        print(r["sender"], "IF done stops are skipped")
        for c in o["cards"] + o["others"]:
            c["pass_by"] = dict(c.get("pass_by") or {}, time=fmt_time(c["pass_by"]["time"]) if c.get("pass_by") else None)
        show("new", o)


class _Future:
    """The same base, but only the stops still ahead of the van (arrival at or after the clock)."""
    def __init__(self, base):
        keep = [i for i in range(len(base.arr)) if i >= base.min_pos]
        self.nodes = [base.nodes[i] for i in keep]
        self.arr = [base.arr[i] for i in keep]


requests.post(f"{API}/demo/reset", timeout=60)
requests.put(f"{API}/settings", json={"auto_send_cheapest": False})
from live_api import DEMO_EMAIL, FIRE_TEXT  # noqa: E402
keys = [add(*MAYA), add(f"{DEMO_EMAIL[0]} <{DEMO_EMAIL[1]}>", FIRE_TEXT)]
requests.put(f"{API}/settings", json={"auto_send_cheapest": True})
asyncio.run(main(keys))
