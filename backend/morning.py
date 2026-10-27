"""Step 22: the preloaded morning (REQ-1413 to 1418). Two bookings priced by the engine on stops that were already
on the vans' routes before 10:00am, one held request, their Activity, two rules and the phones. Routes are not touched."""
import uuid
from datetime import datetime, timedelta, timezone

from core import BKEY, db, ensure_matrix, get_business, learned_service_map, load_units
from engine import matrix
from engine.insertion import Base, pass_by
from engine.options import customer_line
from engine.pricing import added_cost, half_up, money_text, price_quote
from engine.timing import compute_route, fmt_time
from routes_api import today_nodes

# (van, sender, minutes after midnight the email came in, minutes until it was booked by itself)
BOOKINGS = [("van-2", "Lena at {pickup}", 7 * 60 + 38, 9), ("van-1", "Marcus at {pickup}", 7 * 60 + 51, 8)]
HELD = {"sender": "Priya at Rockridge Florist", "minutes": 9 * 60 + 46,
        "text": "Subject: Flowers to our other shop\n\nHi, can you collect two flower boxes from our shop this afternoon and take them "
                "to our other location? Thanks, Priya, Rockridge Florist",
        "reason": "We need the pickup and delivery addresses."}
RULES = ["Never send Van 3 to SF after 4pm.", "Call the customer if a pickup will be more than 15 minutes late."]


def _at(demo_date, minutes, pacific):
    d = datetime.fromisoformat(demo_date)
    return d.replace(hour=int(minutes // 60), minute=int(minutes % 60), tzinfo=pacific)


async def _engine_option(u, nodes, pick, drop, s, travel, sm):
    """Price the two stops the way the engine prices a new job: the route with them minus the route without them."""
    unit = u.public()
    with_it = compute_route(unit, nodes, s, travel=travel)
    without = Base(unit, [n for n in nodes if n["key"] not in (pick["key"], drop["key"])], s, travel, None)
    minutes = int(half_up(max(0.0, with_it["driving_minutes"] - without.result["driving_minutes"])
                          + pick["service_minutes"] + drop["service_minutes"], 0))
    miles = half_up(max(0.0, with_it["total_miles"] - without.result["total_miles"]), 1)
    cost = added_cost(minutes, miles, s)
    freq = {"type": "one_off", "days": []}
    priced = price_quote(minutes, miles, cost, u.name, freq, s)
    pb = pass_by(u.name, without, pick)
    plan = await db.route_plans.find_one({"business_key": BKEY, "unit_key": u.key, "is_current": True}, {"stops": 1})
    rows = {r["stop_key"]: r for r in plan["stops"]}  # the times the van actually had for these stops this morning
    o = {"option_id": f"opt-{uuid.uuid4().hex[:10]}", "unit_key": u.key, "unit_name": u.name, "color": u.color,
         "added_minutes": minutes, "added_miles": miles, "added_cost": cost, "pass_by": pb, "labels": ["Cheapest"],
         "title": "Cheapest", "feasible": True, "pickup_label": fmt_time(rows[pick["key"]]["arrival"]),
         "dropoff_label": fmt_time(rows[drop["key"]]["arrival"]), **priced,
         "new_stops": [{"kind": k, "name": n["customer_name"], "address": n.get("address"), "arrival": rows[n["key"]]["arrival"],
                        "arrival_label": fmt_time(rows[n["key"]]["arrival"])} for k, n in (("pickup", pick), ("dropoff", drop))]}
    o["customer_line"] = customer_line(o, {"frequency": freq})
    return o


def _event(ts, actor, line, kind):
    return {"business_key": BKEY, "ts": ts.astimezone(timezone.utc).isoformat(), "scope": "activity", "kind": kind, "actor": actor, "line": line}


async def preload_morning(pacific):
    biz = await get_business()
    s = biz.settings.model_dump()
    await ensure_matrix(s)
    travel, sm = matrix.make_travel(s), await learned_service_map()
    units = {u.key: u for u in await load_units()}
    now = datetime.now(timezone.utc)
    events, n = [], 0
    last = None  # set by every BOOKINGS entry; BOOKINGS is a non-empty constant
    for i, (van, sender_fmt, minutes, wait) in enumerate(BOOKINGS):
        u = units[van]
        nodes = await today_nodes(u, biz.demo_date, sm)
        docs = {d["key"]: d async for d in db.stops.find({"business_key": BKEY, "unit_key": van}, {"_id": 0})}
        pick, drop = nodes[0], nodes[1]
        for nd in (pick, drop):
            nd["address"] = docs[nd["key"]]["address"]
        o = await _engine_option(u, nodes, pick, drop, s, travel, sm)
        n += 1
        sender = sender_fmt.format(pickup=pick["customer_name"])
        got = _at(biz.demo_date, minutes, pacific)
        booked = got + timedelta(seconds=wait)
        order_at = (now - timedelta(minutes=30 - i)).isoformat()  # before any live booking, so the live one is always newest
        text = (f"Subject: Run to {drop['customer_name']} this morning\n\nHi Bayline, can you pick up a box at {pick['address']} "
                f"and drop it at {drop['address']} by {o['dropoff_label']}? Thanks, {sender}")
        key = f"req-{n:02d}"
        toast = f"Booked {pick['customer_name']}, {money_text(o['price'])} instead of {money_text(o['usual'])}"
        toast += f", {u.name} already passes {o['pass_by']['miles']:.1f} mi away." if o.get("pass_by") else "."
        confirm = f"You're booked. {u.name} picks up around {o['pickup_label']} and drops off around {o['dropoff_label']}. {o['customer_line']}"
        earn = f"Bayline earns {money_text(o['price'])} for a stop that costs it about ${int(half_up(o['added_cost'], 0))} extra."
        await db.requests.insert_one({
            "key": key, "business_key": BKEY, "number": n, "source": "email", "sender": sender, "sender_contact": None, "raw_text": text,
            "file": None, "received_at": got.isoformat(), "parsed": None, "problems": [], "status": "accepted", "seeded": True,
            "preloaded": True, "job_status": "ready", "job": None, "job_reason": None, "read_error": None, "auto_sent": True,
            "job_summary": f"{pick['customer_name']} to {drop['customer_name']}.", "needs_clarification": False,
            "summary": f"{pick['address']} to {drop['address']}, by {o['dropoff_label']}. One-off today.",
            "details": [{"key": "customer", "label": "Customer", "value": pick["customer_name"], "confidence": "high", "needs_clarification": False},
                        {"key": "time", "label": "Time", "value": f"By {o['dropoff_label']}", "confidence": "high", "needs_clarification": False},
                        {"key": "frequency", "label": "How often", "value": "One-off today", "confidence": "high", "needs_clarification": False}],
            "options": {"cards": [o], "others": [], "blocked": [], "rules_sig": ""}, "booked_at": booked.isoformat(),
            "booked_seconds": wait, "booked_by": "auto"})
        await db.quotes.insert_one({
            "business_key": BKEY, "key": f"quote-{uuid.uuid4().hex[:8]}", "request_key": key, "option_id": o["option_id"],
            "unit_key": van, "unit_name": u.name, "price": o["price"], "price_text": money_text(o["price"]), "per": "run",
            "pickup_label": o["pickup_label"], "dropoff_label": o["dropoff_label"], "customer_line": o["customer_line"],
            "labels": o["labels"], "loses_money": False, "status": "accepted", "auto": True, "preloaded": True,
            "customer": sender.split(" at ")[0], "created_at": order_at,
            "confirmation": {"via": "phone", "text": confirm, "at": order_at},
            "booking": {"unit_key": van, "stop_keys": [pick["key"], drop["key"]], "at": order_at, "toast": toast, "price": o["price"],
                        "usual": o["usual"], "ruler": {"price": o["price"], "usual": o["usual"]}, "customer": pick["customer_name"],
                        "unit_name": u.name, "added_cost": o["added_cost"], "earn_line": earn, "booked_seconds": wait}})
        auto_line = f"Auto-sent within your rules: booked {pick['customer_name']} on {u.name} at {money_text(o['price'])}."
        events += [_event(got + timedelta(seconds=2), "assistant", f"Read {sender}'s email and priced it: {u.name} at {money_text(o['price'])}.", "read"),
                   _event(booked, "assistant", auto_line, "auto_sent"),
                   _event(booked + timedelta(seconds=1), "driver", f"{u.name}'s driver got the new stop on their phone.", "driver"),
                   _event(booked + timedelta(seconds=2), "customer", f"{sender.split(' at ')[0]} got the confirmation with the reason.", "confirm"),
                   _event(_at(biz.demo_date, o["new_stops"][0]["arrival"], pacific), "driver", f"Marked done: {pick['customer_name']}.", "done"),
                   _event(_at(biz.demo_date, o["new_stops"][1]["arrival"], pacific), "driver", f"Marked done: {drop['customer_name']}.", "done")]
        last = (van, pick, o, confirm, booked)
    n += 1
    got = _at(biz.demo_date, HELD["minutes"], pacific)
    await db.requests.insert_one({
        "key": f"req-{n:02d}", "business_key": BKEY, "number": n, "source": "email", "sender": HELD["sender"], "sender_contact": None,
        "raw_text": HELD["text"], "file": None, "received_at": got.isoformat(), "parsed": None, "status": "needs_info", "seeded": True,
        "preloaded": True, "problems": [{"kind": "missing", "text": HELD["reason"], "detail": None, "what": "addresses", "where": ""}],
        "job_status": "cant_price", "job": None, "job_reason": HELD["reason"], "job_summary": HELD["reason"], "read_error": None,
        "needs_clarification": True, "summary": "Two flower boxes from Rockridge Florist to their other shop. No addresses yet.",
        "details": [{"key": "customer", "label": "Customer", "value": "Rockridge Florist", "confidence": "high", "needs_clarification": False},
                    {"key": "time", "label": "Time", "value": "This afternoon", "confidence": "medium", "needs_clarification": False},
                    {"key": "frequency", "label": "How often", "value": "One-off today", "confidence": "high", "needs_clarification": False}],
        "options": None})
    events.append(_event(got + timedelta(seconds=3), "assistant", f"Held {HELD['sender']}'s email for you: {HELD['reason']}", "held"))
    for i, text in enumerate(RULES):
        await db.agent_rules.insert_one({"business_id": BKEY, "text": text, "active": True,
                                         "created_at": (_at(biz.demo_date, 7 * 60 + i, pacific)).astimezone(timezone.utc).isoformat()})
    events.sort(key=lambda e: e["ts"])
    await db.events.insert_many(events)
    van, pick, o, confirm, booked = last
    at = (now - timedelta(minutes=28)).isoformat()
    await db.phone_messages.insert_many([
        {"business_key": BKEY, "key": uuid.uuid4().hex[:12], "phone": "driver", "from_me": False, "kind": "text", "quote_key": None, "at": at,
         "text": f"New stop: pick up at {pick['customer_name']}, {pick['address']}, around {o['pickup_label']}."},
        {"business_key": BKEY, "key": uuid.uuid4().hex[:12], "phone": "customer", "from_me": False, "kind": "text", "quote_key": None, "at": at,
         "text": f"Bayline Courier: {money_text(o['price'])} for the run, pickup about {o['pickup_label']}. {o['customer_line']}"},
        {"business_key": BKEY, "key": uuid.uuid4().hex[:12], "phone": "customer", "from_me": False, "kind": "text", "quote_key": None, "at": at,
         "text": confirm}])
