"""Quotes (Send, Accept, Decline, Undo) and the Customer, Driver and Owner demo phones. Real texting stays off."""
import re
import uuid
from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import logging

from activity import log
from booking_common import after_undo, emails, find_option, now_iso, post  # noqa: F401
from core import BKEY, data_lock, db, get_business
from engine.timing import fmt_time
from engine.pricing import half_up, money_text
from engine_api import AcceptIn, engine_accept, undo_change

logger = logging.getLogger("drivepast.phones")
router = APIRouter(prefix="/api")
PHONES = ("customer", "driver", "owner")
ACCEPT_WORDS = {"ok", "okay", "yes", "yes please", "sounds good", "yep", "sure", "ok thanks", "ok thank you"}
STALE_CUSTOMER = "Sorry, that time just filled up. We'll send a new option shortly."
STALE_OWNER = "Couldn't add that stop. The route changed. Try another option."
LOSS_ASK = "This loses money at your usual price. Send anyway?"
CUSTOMER_PHONE = "(510) 555-0100"
DAY = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAYS = {"mon": "Monday", "tue": "Tuesday", "wed": "Wednesday", "thu": "Thursday", "fri": "Friday"}


def fail(status, message, **extra):
    return JSONResponse(status_code=status, content={"detail": {"message": message, **extra}})


def public(q):
    return {k: v for k, v in q.items() if k not in ("_id", "business_key")} if q else None


def first_name(req):
    cust = next((d["value"] for d in req.get("details") or [] if d["key"] == "customer"), None) or req.get("sender", "")
    return cust.split(",")[0].split(" at ")[0].strip() or "The customer"


async def get_req(key):
    r = await db.requests.find_one({"business_key": BKEY, "key": key})
    if not r:
        raise HTTPException(404, "We couldn't find that request.")
    return r


async def get_quote(key):
    q = await db.quotes.find_one({"business_key": BKEY, "key": key}, {"_id": 0})
    if not q:
        raise HTTPException(404, "We couldn't find that quote.")
    return dict(q)


async def log_sent(req, q, one_off, auto):
    per = "for the run" if one_off else "a visit"
    await log("assistant" if auto else "owner",
              f"Sent {q['unit_name']} at {money_text(q['price'])} {per} to {q['customer'] or req.get('sender') or 'the customer'} "
              f"(request #{req['number']}).", "send")


async def send_quote(req, option_id, confirm_loss=False, auto=False):
    """Create a Sent quote, set the request to Quoted and post it to the Customer phone."""
    o = find_option(req, option_id)
    if not o:
        return fail(404, "That option is gone. Ask the vans again.")
    biz = await get_business()
    s = biz.settings
    one_off = (req.get("job") or {}).get("frequency", {}).get("type") == "one_off"
    floor, usual = (s.floor_one_off, s.usual_one_off) if one_off else (s.floor_recurring, s.usual_recurring)
    if o["price"] < floor - 1e-9 or o["price"] > usual + 1e-9:
        return fail(409, "That price is outside your floor and usual price. Price it again.")
    if o.get("loses_money") and not confirm_loss:
        return fail(409, LOSS_ASK, needs_confirm=True)
    q = {"business_key": BKEY, "key": f"quote-{uuid.uuid4().hex[:8]}", "request_key": req["key"], "option_id": option_id,
         "unit_key": o["unit_key"], "unit_name": o["unit_name"], "price": o["price"], "per": o["per"],
         "pickup_label": o["pickup_label"], "dropoff_label": o.get("dropoff_label"), "customer_line": o["customer_line"],
         "labels": o.get("labels", []), "loses_money": bool(o.get("loses_money")), "status": "sent", "auto": auto,
         "customer": first_name(req), "created_at": now_iso(), "booking": None}
    await db.quotes.update_many({"business_key": BKEY, "request_key": req["key"], "status": "sent"}, {"$set": {"status": "replaced"}})
    q["price_text"] = money_text(o["price"])
    if emails(req):
        from google_api import email_quote
        await db.quotes.insert_one(dict(q))
        try:
            await email_quote(req, q, "for the run" if one_off else "a visit")
        except PermissionError as e:
            await db.quotes.update_one({"business_key": BKEY, "key": q["key"]}, {"$set": {"status": "refused"}})
            return fail(409, str(e))
        except Exception:  # noqa: BLE001
            await db.quotes.update_one({"business_key": BKEY, "key": q["key"]}, {"$set": {"status": "failed"}})
            return fail(502, "The quote email didn't go out. Try Send again in a minute.")
        await db.requests.update_one({"_id": req["_id"]}, {"$set": {"status": "quoted"}})
        await log_sent(req, q, one_off, auto)
        return public(await get_quote(q["key"]))
    await db.quotes.insert_one(q)
    await db.requests.update_one({"_id": req["_id"]}, {"$set": {"status": "quoted"}})
    await log_sent(req, q, one_off, auto)
    text = (f"Bayline Courier: {money_text(o['price'])} {'for the run' if one_off else 'a visit'}, "
            f"pickup about {o['pickup_label']}. {o['customer_line']}")
    await post("customer", text, kind="quote", quote_key=q["key"])
    return public(q)


def stop_phrase(stops, demo):
    pick = next((n for n in stops if n["kind"] != "dropoff"), stops[0])
    drops = [n for n in stops if n["kind"] == "dropoff" and n is not pick]
    street = (pick.get("address") or "").split(",")[0]
    line = f"{pick['name']}, {street}, about {pick['arrival_label']}"
    if drops:
        line += ", then " + ", then ".join(d["name"] for d in drops)
    return line + "."


def when_phrase(freq, demo):
    t = freq.get("type")
    if t == "weekday":
        start = freq.get("start_date")
        return f"New daily stop from {DAY[date.fromisoformat(start).weekday()]}." if start else "New daily stop from today."
    if t == "weekdays":
        return f"New stop every {' and '.join(DAYS[d] for d in freq.get('days') or [])}."
    day = freq.get("date")
    return "New stop today." if day == demo else f"New stop on {DAY[date.fromisoformat(day).weekday()]}."


STREET_WORDS = {"St": "Street", "Ave": "Avenue", "Blvd": "Boulevard", "Rd": "Road", "Dr": "Drive", "Way": "Way"}


def place_name(o):
    pick = next((n for n in o.get("new_stops") or [] if n["kind"] != "dropoff"), None)
    if not pick:
        return o.get("unit_name", "the stop")
    street = (pick.get("address") or "").split(",")[0].strip()
    m = re.match(r"^\d+[A-Za-z]?\s+(.+)$", street)
    if not m or " and " in street:
        return pick["name"]
    words = m.group(1).split()
    words[-1] = STREET_WORDS.get(words[-1], words[-1])
    return " ".join(words)


def booking_toast(q, o):
    usual, pb = o.get("usual"), o.get("pass_by")
    head = f"Booked {place_name(o)}, {money_text(q['price'])}"
    head += f" instead of {money_text(usual)}." if usual and q["price"] < usual - 1e-9 else "."
    if pb:
        d = pb["miles"]
        head += f" {q['unit_name']} already passes {'less than 0.1' if d < 0.05 else f'{d:.1f}'} mi away."
    return head


SUFFIX = {"st": "Street", "ave": "Avenue", "av": "Avenue", "blvd": "Boulevard", "rd": "Road", "dr": "Drive", "way": "Way", "pl": "Place", "ct": "Court", "ln": "Lane", "pkwy": "Parkway"}


def pickup_street(req):
    """'1300 Clay St, Oakland' -> 'Clay Street'."""
    stop = next((s for s in ((req.get("job") or {}).get("stops") or []) if s.get("kind") == "pickup"), None)
    words = re.sub(r"^\d+[a-zA-Z]?\s+", "", (stop or {}).get("address", "").split(",")[0].strip()).split()
    if words and words[-1].lower().rstrip(".") in SUFFIX:
        words[-1] = SUFFIX[words[-1].lower().rstrip(".")]
    return " ".join(words) or None


def booking_name(req, q):
    """Parsed customer or company, then sender display name, then the pickup street. Never an email address."""
    vals = {d["key"]: d.get("value") for d in req.get("details") or []}
    names = [vals.get("customer"), vals.get("company"), req.get("sender"), pickup_street(req)]
    return next((n for n in names if n and "@" not in str(n)), None) or "the customer"


def auto_booked_text(q, o, req):
    """Task 3 format: Booked {customer}, ${price} instead of ${usual}, {van} already passes {miles} mi away."""
    usual, pb = o.get("usual"), o.get("pass_by")
    text = f"Booked {booking_name(req, q)}, {money_text(q['price'])}"
    if usual and q["price"] < usual - 1e-9:
        text += f" instead of {money_text(usual)}"
    if pb:
        text += f", {q['unit_name']} already passes {pb['miles']:.1f} mi away"
    return text + "."


def earn_line(q, o, biz):
    """REQ-1403: the courier's side of the booking, from the booked price and the engine's added_cost."""
    if o.get("added_cost") is None:
        return None
    return f"{biz.name.split()[0]} earns {money_text(q['price'])} for a stop that costs it about ${int(half_up(o['added_cost'], 0))} extra."


def booked_seconds(req, booked_iso):
    """Booked time minus arrival: Gmail internalDate for Gmail requests, else received_at."""
    ms = (req.get("gmail") or {}).get("internal_ms")
    arrived = ms / 1000 if ms else datetime.fromisoformat(req["received_at"]).timestamp()
    return max(0, round(datetime.fromisoformat(booked_iso).timestamp() - arrived))


async def confirm_booking(req, q):
    """REQ-1052: confirm in the request's channel. A failed email keeps the booking and logs to Activity."""
    drop = f" and drops off around {q['dropoff_label']}" if q.get("dropoff_label") else ""
    reason = q.get("customer_line") or f"The price is {money_text(q['price'])}."
    text = f"You're booked. {q['unit_name']} picks up around {q['pickup_label']}{drop}. {reason}"
    if not emails(req):
        await post("customer", text)
        via = "phone"
    else:
        from google_api import send_in_thread
        from html import escape
        html = f'<p style="font-family:Arial,sans-serif;color:#111">{escape(text)}</p>'
        try:
            via = await send_in_thread(req, html, text)
        except Exception as e:  # noqa: BLE001
            logger.warning("Booking confirmation failed: %s", type(e).__name__)
            await log("customer", f"Confirmation email didn't send ({q['customer'] or 'customer'}, {q['unit_name']}).", "confirm")
            via = "failed"
    await db.quotes.update_one({"business_key": BKEY, "key": q["key"]}, {"$set": {"confirmation": {"via": via, "text": text, "at": now_iso()}}})


async def accept_quote(q, auto=False, by="customer"):
    if q["status"] != "sent":
        return fail(409, f"This quote is already {q['status']}.")
    req = await get_req(q["request_key"])
    res = await engine_accept(AcceptIn(option_id=q["option_id"]))
    if isinstance(res, JSONResponse):
        await db.quotes.update_one({"business_key": BKEY, "key": q["key"]}, {"$set": {"status": "stale"}})
        if req.get("gmail"):
            await db.requests.update_one({"_id": req["_id"]}, {"$set": {"status": "needs_attention"}})
        else:
            await post("customer", STALE_CUSTOMER)
        await post("owner", f"{STALE_OWNER} ({q['customer']}, {q['unit_name']})")
        return fail(409, STALE_OWNER, stale=True)
    biz = await get_business()
    o = find_option(req, q["option_id"]) or {}
    freq = (req.get("job") or {}).get("frequency", {})
    booking = {"unit_key": res["unit_key"], "stop_keys": res["stop_keys"], "at": now_iso(), "toast": booking_toast(q, o),
               "price": q["price"], "usual": o.get("usual"),
               "ruler": {"price": q["price"], "usual": o["usual"]} if o.get("usual") and q["price"] < o["usual"] - 1e-9 else None,
               "customer": booking_name(req, q), "unit_name": q["unit_name"], "added_cost": o.get("added_cost"),
               "earn_line": earn_line(q, o, biz)}
    if auto:
        booking["toast"] = auto_booked_text(q, o, req)
        await db.events.insert_one({"business_key": BKEY, "ts": now_iso(), "kind": "booked", "scope": "activity", "van_id": res["unit_key"],
                                    "text": booking["toast"], "actor": "assistant", "line": booking["toast"], "ruler": booking["ruler"],
                                    "earn_line": booking["earn_line"], "customer": booking["customer"], "unit_name": q["unit_name"],
                                    "request_key": q["request_key"]})
    booking["booked_seconds"] = booked_seconds(req, booking["at"])
    await db.quotes.update_one({"business_key": BKEY, "key": q["key"]}, {"$set": {"status": "accepted", "booking": booking}})
    await db.requests.update_one({"_id": req["_id"]}, {"$set": {"status": "accepted", "booked_at": booking["at"],
                                                                "booked_seconds": booking["booked_seconds"], "booked_by": by}})
    from inbox_api import later
    later(confirm_booking(req, q))
    await post("driver", f"{when_phrase(freq, biz.demo_date)} {stop_phrase(o.get('new_stops') or [], biz.demo_date)}")
    per = "for the run" if freq.get("type") == "one_off" else "a visit"
    await post("owner", f"{q['customer']} accepted: {money_text(q['price'])} {per} on {q['unit_name']}.")
    await log("customer", f"{q['customer'] or 'The customer'} accepted {money_text(q['price'])} {per} on {q['unit_name']}.", "accept")
    await log("driver", f"{q['unit_name']}'s driver got the new stop on their phone.", "driver")
    return {"ok": True, "quote": public({**q, "status": "accepted", "booking": booking}), "booking": booking}


async def decline_quote(q):
    if q["status"] != "sent":
        return fail(409, f"This quote is already {q['status']}.")
    await db.quotes.update_one({"business_key": BKEY, "key": q["key"]}, {"$set": {"status": "declined"}})
    await db.requests.update_one({"business_key": BKEY, "key": q["request_key"]}, {"$set": {"status": "declined"}})
    await post("owner", f"{q['customer']} declined the {money_text(q['price'])} quote on {q['unit_name']}.")
    await log("customer", f"{q['customer'] or 'The customer'} declined the {money_text(q['price'])} quote on {q['unit_name']}.", "decline")
    return {"ok": True, "quote": public({**q, "status": "declined"})}


async def undo_booking(q):
    if q["status"] != "accepted":
        return fail(409, "Only an accepted quote can be undone.")
    ch = await db.change_log.find_one({"business_key": BKEY, "option_id": q["option_id"], "undone": False})
    if not ch:
        return fail(409, "Nothing to undo")
    return await undo_change(ch)


class SendIn(BaseModel):
    option_id: str
    confirm_loss: bool = False


class TextIn(BaseModel):
    text: str


@router.post("/inbox/{key}/send")
async def inbox_send(key: str, body: SendIn, request: Request):
    from google_api import remember_base
    await remember_base(request)
    return await send_quote(await get_req(key), body.option_id, body.confirm_loss)


@router.post("/inbox/{key}/reject-option")
async def inbox_reject(key: str, body: SendIn):
    from engine.options import reject_option
    req = await get_req(key)
    if not req.get("options"):
        raise HTTPException(409, "Ask the vans first.")
    opts = reject_option(req["options"], body.option_id)
    await db.requests.update_one({"_id": req["_id"]}, {"$set": {"options": opts}})
    return {"options": opts}


@router.post("/inbox/{key}/send-question")
async def inbox_send_question(key: str, body: TextIn):
    req = await get_req(key)
    text = body.text.strip()
    if not text:
        raise HTTPException(422, "Write the question first.")
    await post("customer", f"Bayline Courier: {text}")
    q = {**(req.get("question") or {}), "text": text, "sent": True}
    await db.requests.update_one({"_id": req["_id"]}, {"$set": {"question": q}})
    return {"ok": True, "question": q}


@router.get("/quotes")
async def quotes_list(request_key: str = None, unit_key: str = None, status: str = None):
    q = {"business_key": BKEY}
    for k, v in (("request_key", request_key), ("unit_key", unit_key), ("status", status)):
        if v:
            q[k] = v
    return [public(x) async for x in db.quotes.find(q).sort("created_at", -1)]


async def accept_once(key, auto=None, by="customer"):
    """Accept under the quote lock so the customer page and the 20 s auto-commit can't both book."""
    from google_api import answer_lock
    async with answer_lock:
        q = await get_quote(key)  # re-read inside the lock
        if q["status"] == "accepted":  # the other side of the race already booked it
            return {"ok": True, "quote": public(q), "booking": q.get("booking"), "already_booked": True}
        return await accept_quote(q, auto=bool(q.get("auto")) if auto is None else auto, by=by)


@router.post("/quotes/{key}/accept")
async def quote_accept(key: str):
    return await accept_once(key)


@router.get("/customer/{request_key}")
async def customer_view(request_key: str):
    """The no-login customer page: only the request text, the sent option's customer_line and its times."""
    from inbox_api import api_status
    r = await db.requests.find_one({"business_key": BKEY, "key": request_key}, {"_id": 0, "raw_text": 1, "status": 1})
    if not r:
        raise HTTPException(404, "We couldn't find that request.")
    q = await db.quotes.find_one({"business_key": BKEY, "request_key": request_key, "status": {"$in": ["sent", "accepted", "declined"]}},
                                 {"_id": 0}, sort=[("created_at", -1)])
    return {"text": re.sub(r"^Subject:[^\n]*\n+", "", r.get("raw_text") or "").strip(), "status": api_status(r["status"]),
            "quote": {k: q.get(k) for k in ("key", "status", "customer_line", "pickup_label", "dropoff_label", "commit_at")} if q else None,
            "booked_line": f"Accepted. {q['unit_name']} arrives about {q['pickup_label']}." if q and q["status"] == "accepted" else None,
            "confirmation": (q.get("confirmation") or {}).get("text") if q and q["status"] == "accepted" else None}


@router.post("/quotes/{key}/decline")
async def quote_decline(key: str):
    return await decline_quote(await get_quote(key))


@router.post("/quotes/{key}/undo")
async def quote_undo(key: str):
    return await undo_booking(await get_quote(key))


@router.get("/phones")
async def phones():
    msgs = [m async for m in db.phone_messages.find({"business_key": BKEY}, {"_id": 0, "business_key": 0}).sort("at", 1)]
    quotes = {q["key"]: q["status"] async for q in db.quotes.find({"business_key": BKEY}, {"key": 1, "status": 1})}
    for m in msgs:
        if m.get("quote_key"):
            m["quote_status"] = quotes.get(m["quote_key"])
    return {p: [m for m in msgs if m["phone"] == p] for p in PHONES}


async def open_quote():
    return await db.quotes.find_one({"business_key": BKEY, "status": "sent"}, {"_id": 0}, sort=[("created_at", -1)])


DONE_WORDS = {"done", "delivered", "picked up", "stop done", "dropped off", "done here"}


async def driver_done():
    """Driver phone says done: mark the stop the van is at or heading to at the demo clock (van of the latest booking, else Van 2)."""
    from core import today_plans
    from routes_api import load_unit, mark_done
    biz = await get_business()
    clock = biz.settings.demo_clock_minutes
    q = await db.quotes.find_one({"business_key": BKEY, "status": "accepted"}, sort=[("booking.at", -1)])
    unit = await load_unit(q["booking"]["unit_key"] if q else "van-2")
    plan = (await today_plans(biz.demo_date)).get(unit.key)
    done = {d["key"] async for d in db.stops.find({"business_key": BKEY, "unit_key": unit.key, "done_date": biz.demo_date}, {"key": 1})}
    rows = plan.stops if plan else []
    nxt = next((r for r in rows if r["stop_key"] not in done and r["departure"] > clock + 1e-6), None)
    if not nxt:
        await post("driver", "No stop to mark done right now.")
        return {"ok": True, "action": "none", "message": "No stop to mark done right now."}
    stop = await db.stops.find_one({"business_key": BKEY, "key": nxt["stop_key"]}, {"customer_name": 1})
    reorder, shifts = await mark_done(unit, nxt["stop_key"], biz)
    plan = (await today_plans(biz.demo_date)).get(unit.key)
    keys = [r["stop_key"] for r in plan.stops] if plan else []
    i = keys.index(nxt["stop_key"]) + 1 if nxt["stop_key"] in keys else len(keys)
    after = plan.stops[i] if i < len(keys) else None
    nxt_doc = await db.stops.find_one({"business_key": BKEY, "key": after["stop_key"]}, {"customer_name": 1}) if after else None
    line = f"Marked done: {stop['customer_name']} at {fmt_time(clock)}."
    line += f" Next: {nxt_doc['customer_name']} at {fmt_time(after['arrival'])}." if nxt_doc else " That was your last stop."
    if shifts:
        names = {d["key"]: d["customer_name"] async for d in db.stops.find({"business_key": BKEY, "key": {"$in": list(shifts)}}, {"key": 1, "customer_name": 1})}
        line += " Times moved: " + ", ".join(f"{names.get(k, k)} {'+' if v > 0 else '−'}{abs(v)} min" for k, v in shifts.items()) + "."
    await post("driver", line + (f" {reorder['text']}." if reorder else ""))
    return {"ok": True, "action": "done", "stop_key": nxt["stop_key"], "message": line, "reorder": reorder, "shifts": shifts}


@router.post("/phones/{phone}/messages")
async def phone_reply(phone: str, body: TextIn):
    from inbox_api import new_request, read_one
    if phone not in PHONES:
        raise HTTPException(404, "There's no such phone.")
    text = body.text.strip()
    if not text:
        raise HTTPException(422, "Type a message first.")
    if len(text) > 2000:
        raise HTTPException(422, "Keep it under 2,000 characters.")
    await post(phone, text, from_me=True)
    if phone == "driver" and re.sub(r"[^a-z ]", "", text.lower()).strip() in DONE_WORDS:
        async with data_lock:
            return await driver_done()
    if phone != "customer":
        return {"ok": True, "action": "noted"}
    q = await open_quote()
    if q and re.sub(r"[^a-z ]", "", text.lower()).strip() in ACCEPT_WORDS:
        res = await accept_once(q["key"], auto=False)
        return res if isinstance(res, JSONResponse) else {**res, "action": "accepted"}
    if q:
        req = await get_req(q["request_key"])
        raw = f"{req.get('raw_text', '')}\n\nCustomer reply: {text}".strip()
        await db.requests.update_one({"_id": req["_id"]}, {"$set": {"raw_text": raw}})
        await read_one(await get_req(q["request_key"]))
        await post("owner", f"{q['customer']} replied to the quote. I re-read request {req['number']}.")
        return {"ok": True, "action": "reread", "request_key": q["request_key"]}
    r = await new_request("text", text, "Customer phone", CUSTOMER_PHONE)
    await post("customer", "Thanks. We're pricing that now.")
    done = await read_one(r)
    await post("owner", f"New text request {done['number']} from the customer phone.")
    return {"ok": True, "action": "new_request", "request_key": done["key"]}


@router.post("/demo/send-request-1")
async def demo_send_request_1():
    from inbox_api import read_one
    req = await get_req("req-01")
    await post("customer", req["raw_text"], from_me=True)
    if req["status"] in ("quoted", "accepted", "declined"):
        return {"ok": True, "request_key": "req-01", "status": req["status"]}
    done = await read_one(req)
    return {"ok": True, "request_key": "req-01", "status": (await get_req("req-01"))["status"], "read_status": done["status"]}


@router.post("/demo/customer-accept")
async def demo_customer_accept():
    q = await open_quote()
    if not q:
        return fail(409, "There's no open quote. Send one first.")
    return await accept_once(q["key"], auto=False)
