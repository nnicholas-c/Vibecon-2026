"""Live state for the owner screen (booking toasts, inbox count) and the presenter demo."""
import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request

from core import BKEY, db
from demo_core import reset_demo

router = APIRouter(prefix="/api")

SCRIPTED_SENDER = ("Ana at Telegraph Bio", "ana@telegraphbio.example")
SCRIPTED_TEXT = ("Hi Bayline, can you pick up a box of samples today at 1100 Gilman St, Berkeley and get it to "
                 "700 Parker St, Berkeley by 5pm? Thanks, Ana, Telegraph Bio")


async def inbox_count():
    return await db.requests.count_documents({"business_key": BKEY, "status": {"$nin": ["quoted", "accepted", "declined"]}})


def booking_view(q):
    b = q.get("booking") or {}
    return {"id": q["key"], "at": b.get("at"), "unit_key": b.get("unit_key"), "stop_keys": b.get("stop_keys", []),
            "toast": b.get("toast"), "ruler": b.get("ruler"), "request_key": q["request_key"], "auto": bool(q.get("auto")),
            "customer": b.get("customer"), "unit_name": q.get("unit_name"), "earn_line": b.get("earn_line")}


HELD = ("needs_info", "needs_attention")


async def latest_request():
    """REQ-1401/1402: the newest live request (not the preloaded morning), so Fleet can show it being read or held."""
    r = await db.requests.find_one({"business_key": BKEY, "seeded": False, "parent_key": {"$exists": False}}, sort=[("number", -1)])
    if not r:
        return None
    held = r["status"] in HELD or (r["status"] == "new" and r.get("read_error"))
    reason = next((p.get("text") for p in r.get("problems") or [] if p.get("text")), None) or r.get("job_reason") or r.get("read_error")
    return {"key": r["key"], "sender": r.get("sender"), "status": r["status"], "held": bool(held), "reason": reason if held else None}


async def demo_state():
    run = await db.demo_runs.find_one({"business_key": BKEY})
    if not run:
        return None
    req = await db.requests.find_one({"business_key": BKEY, "number": {"$gt": run["max_number"]}, "seeded": False,
                                      "parent_key": {"$exists": False}}, sort=[("number", 1)])
    q = await db.quotes.find_one({"business_key": BKEY, "request_key": req["key"], "status": {"$ne": "replaced"}},
                                 sort=[("created_at", -1)]) if req else None
    conn = await db.google_conn.find_one({"business_key": BKEY}, {"email": 1, "expired": 1})
    return {"started_at": run["started_at"], "gmail": conn["email"] if conn and not conn.get("expired") else None,
            "request": {"key": req["key"], "number": req["number"], "status": req["status"], "sender": req.get("sender"),
                        "flag": req.get("job_reason") if req["status"] not in ("priced", "quoted", "accepted") else None} if req else None,
            "quote": {"key": q["key"], "status": q["status"], "unit_key": q["unit_key"], "unit_name": q["unit_name"],
                      "price_text": q.get("price_text")} if q else None,
            "booking": booking_view(q) if q and q["status"] == "accepted" else None}


@router.get("/events")
async def reorder_events(since: str = ""):
    """Reorder events after `since` (ISO time) for the 10 s toast poll. Without `since`, returns only the cursor."""
    now = datetime.now(timezone.utc).isoformat()
    if not since:
        recent = await db.events.find({"kind": {"$in": ["reorder", "booked"]}}, {"_id": 0, "ts": 1, "kind": 1, "van_id": 1, "text": 1}).sort("ts", -1).to_list(20)
        return {"now": now, "events": recent[::-1]}
    rows = await db.events.find({"kind": {"$in": ["reorder", "booked"]}, "ts": {"$gt": since}},
                                {"_id": 0, "ts": 1, "kind": 1, "van_id": 1, "text": 1, "ruler": 1, "old_order": 1, "new_order": 1,
                                 "earn_line": 1, "customer": 1, "unit_name": 1, "request_key": 1}).sort("ts", 1).to_list(50)
    return {"now": rows[-1]["ts"] if rows else since, "events": rows}


async def routes_sig():
    agg = await db.route_plans.aggregate([{"$match": {"business_key": BKEY, "is_current": True}},
                                          {"$group": {"_id": None, "v": {"$sum": "$version"}, "n": {"$sum": 1}}}]).to_list(1)
    done = await db.stops.count_documents({"business_key": BKEY, "done_date": {"$type": "string"}})  # a driver Done redraws within 5 s
    return f"{agg[0]['n']}-{agg[0]['v']}-{done}" if agg else ""


async def saved_today():
    """Sum of (usual - quoted) over accepted quotes, from the engine numbers stored at booking."""
    total = 0.0
    async for q in db.quotes.find({"business_key": BKEY, "status": "accepted"}, {"price": 1, "booking": 1}):
        b = q.get("booking") or {}
        usual = b.get("usual") or (b.get("ruler") or {}).get("usual")
        if usual:
            total += max(0.0, usual - q["price"])
    return round(total, 2)


@router.get("/live")
async def live(request: Request):
    from google_api import remember_base
    await remember_base(request)  # opening the live site saves its public address for email links
    q = await db.quotes.find_one({"business_key": BKEY, "status": "accepted"}, sort=[("booking.at", -1)])
    return {"inbox_new_count": await inbox_count(), "last_booking": booking_view(q) if q else None, "demo": await demo_state(),
            "routes_sig": await routes_sig(), "saved_today": await saved_today(), "latest_request": await latest_request()}


@router.post("/demo/run")
async def demo_run():
    res = await reset_demo()
    if not isinstance(res, dict):
        return res
    await db.businesses.update_one({"key": BKEY}, {"$set": {"settings.auto_send_cheapest": True}})
    last = await db.requests.find_one({"business_key": BKEY}, sort=[("number", -1)])
    await db.demo_runs.delete_many({"business_key": BKEY})
    await db.demo_runs.insert_one({"business_key": BKEY, "started_at": datetime.now(timezone.utc).isoformat(),
                                   "max_number": last["number"] if last else 0})
    return {"ok": True, "demo": await demo_state()}


@router.post("/demo/stop")
async def demo_stop():
    await db.demo_runs.delete_many({"business_key": BKEY})
    return {"ok": True}


DEMO_EMAIL = ("Dana at Grand Lake Optometry", "dana@grandlakeoptometry.example")
FIRE_TEXT = "pickup at 3220 Grand Ave Oakland between 1 and 2pm, drop at 4100 Piedmont Ave by 4pm"


@router.post("/demo/fire-email")
async def demo_fire_email():
    """/dev backup: the Grand Ave request through the Gmail ingest path, without emailing the example address."""
    from google_api import handle_message
    mid = f"demo-{uuid.uuid4().hex[:12]}"
    m = {"id": mid, "thread_id": None, "rfc_id": None, "references": "", "subject": "Pickup today", "from_name": DEMO_EMAIL[0],
         "from_email": DEMO_EMAIL[1], "files": [], "text": FIRE_TEXT, "internal_ms": int(time.time() * 1000), "demo": True}
    res = await handle_message(m, None)
    req = await db.requests.find_one({"business_key": BKEY, "source_key": mid}, {"_id": 0, "key": 1})
    return {"ok": res == "created", "request_key": req["key"] if req else None}


TRICKY_EMAIL = ("Front desk at Lakeshore Dental", "frontdesk@lakeshoredental.example")
TRICKY_TEXT = "need pickup at 5pm today at lakeshore dental to piedmont ave lab"


@router.post("/demo/fire-tricky-email")
async def demo_fire_tricky_email():
    """/dev: the old seeded request 4 (office closes at 4:30) through the Gmail ingest path."""
    from google_api import handle_message
    mid = f"demo-{uuid.uuid4().hex[:12]}"
    m = {"id": mid, "thread_id": None, "rfc_id": None, "references": "", "subject": "Pickup at 5pm", "from_name": TRICKY_EMAIL[0],
         "from_email": TRICKY_EMAIL[1], "files": [], "text": TRICKY_TEXT, "internal_ms": int(time.time() * 1000), "demo": True}
    res = await handle_message(m, None)
    req = await db.requests.find_one({"business_key": BKEY, "source_key": mid}, {"_id": 0, "key": 1})
    return {"ok": res == "created", "request_key": req["key"] if req else None}


@router.post("/demo/scripted-email")
async def demo_scripted_email():
    from inbox_api import new_request, read_one
    from phones_api import post
    state = await demo_state()
    if state and state["request"]:
        return {"ok": True, "request_key": state["request"]["key"], "demo": state}
    await post("customer", SCRIPTED_TEXT, from_me=True)
    r = await new_request("email", SCRIPTED_TEXT, *SCRIPTED_SENDER)
    await read_one(r)
    return {"ok": True, "request_key": r["key"], "demo": await demo_state()}
