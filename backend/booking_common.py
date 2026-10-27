"""Booking pieces shared by phones_api.py and engine_api.py (breaks their import cycle)."""
import uuid
from datetime import datetime, timezone

from activity import log
from core import BKEY, db


def now_iso():
    return datetime.now(timezone.utc).isoformat()


async def post(phone, text, from_me=False, kind="text", quote_key=None):
    doc = {"business_key": BKEY, "key": uuid.uuid4().hex[:12], "phone": phone, "text": text, "from_me": from_me,
           "kind": kind, "quote_key": quote_key, "at": now_iso()}
    await db.phone_messages.insert_one(doc)
    doc.pop("_id", None)
    return doc


def find_option(req, option_id):
    opts = req.get("options") or {}
    return next((o for o in (opts.get("cards") or []) + (opts.get("others") or []) if o.get("option_id") == option_id), None)


def emails(req):
    """Real Gmail requests get email; the /dev "Fire demo email" request (gmail.demo) uses the Customer demo phone."""
    return bool(req.get("gmail")) and not req["gmail"].get("demo")


async def after_undo(ch):
    """Called after the engine undoes a booking: the quote goes back to Sent and the request to Quoted."""
    q = await db.quotes.find_one({"business_key": BKEY, "option_id": ch.get("option_id"), "status": "accepted"}, {"_id": 0})
    if not q:
        return
    await db.quotes.update_one({"business_key": BKEY, "key": q["key"]}, {"$set": {"status": "sent", "booking": None}})
    await db.requests.update_one({"business_key": BKEY, "key": q["request_key"]}, {"$set": {"status": "quoted"}})
    req = await db.requests.find_one({"business_key": BKEY, "key": q["request_key"]})
    o = find_option(req or {}, q["option_id"]) or {}
    name = next((n["name"] for n in o.get("new_stops") or [] if n["kind"] != "dropoff"), "The new stop")
    await post("driver", f"Change cancelled: {name} is off your route.")
    await log("driver", f"{q['unit_name']}'s driver was told {name} is off the route.", "driver")
    if req and emails(req):
        from google_api import email_cancelled
        await email_cancelled(req)
