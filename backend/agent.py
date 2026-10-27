"""Dispatch agent: one OpenAI-compatible chat completion loop with engine-backed tools."""
import json
import logging
import os
import re
from datetime import datetime, timezone

import httpx

from core import BKEY, data_lock, db, ensure_matrix, get_business, learned_service_map, load_units, recompute_unit, today_plans
from agent_usage import DAILY_LIMIT, PACIFIC, over_limit, take_call  # noqa: F401  (re-exported: old import names keep working)
from booking_common import find_option
from demo_core import on_time_by_unit
from engine import matrix
from engine.insertion import Base, pass_by
from engine.pricing import added_cost, half_up
from engine.timing import compute_route, fmt_time
from position import van_position
from routes_api import apply_order, auto_optimize, today_nodes

logger = logging.getLogger("drivepast.agent")
ERROR_REPLY = "I couldn't reach the model. Try again."
LIMIT_REPLY = "Daily model limit reached"
MAX_TOOL_ROUNDS = 3
HISTORY = 8
INSTRUCTIONS = ("You are Fleet, the owner's fleet assistant. Answer in at most 120 words. Always cite numbers from tools, never estimate. "
                "If asked to move or book something, call the tool and state the result. If the owner states a standing rule "
                "(for example 'never send Van 2 to SF after 3pm'), call save_rule and confirm in one line. "
                "The fleet is only the vans listed above; if asked about any other van (like Van 5), say there is no such van. "
                "If you do not know a stop key, pass the customer name; the tool will match it. "
                "Talk like a dispatcher to the owner: short plain sentences, numbers first, no filler. "
                "When asked why a job went on a van, call explain_stop and give: booked or not, the pass-by distance, "
                "the added minutes and miles, and the extra cost (added_cost).")


def _fn(name, desc, props=None, required=None):
    return {"type": "function", "function": {"name": name, "description": desc, "parameters": {
        "type": "object", "properties": props or {}, "required": required or []}}}


VAN = {"van_id": {"type": "string", "description": "Van id like van-2"}}
TOOLS = [
    _fn("get_fleet_summary", "Per-van stops today, spare minutes, next stop and on-time rate."),
    _fn("get_van_route", "Ordered stops for a van today with ETAs and time windows.", VAN, ["van_id"]),
    _fn("explain_stop", "Why a stop sits where it does: added minutes and miles, window and the pass-by line. "
        "stop_key may be a stop key or a customer name / street.",
        {**VAN, "stop_key": {"type": "string"}}, ["van_id", "stop_key"]),
    _fn("get_options", "The option cards already computed for an inbox request.", {"request_key": {"type": "string"}}, ["request_key"]),
    _fn("move_stop", "Move a stop to a new 1-based position in a van's route and re-time it. Only when the owner explicitly asks.",
        {**VAN, "stop_key": {"type": "string"}, "new_position": {"type": "integer"}}, ["van_id", "stop_key", "new_position"]),
    _fn("save_rule", "Save a standing rule the owner stated.", {"text": {"type": "string"}}, ["text"]),
]


async def _ontime():
    return await on_time_by_unit()


async def _stop_docs(keys):
    return {d["key"]: d async for d in db.stops.find({"business_key": BKEY, "key": {"$in": keys}}, {"_id": 0})}


async def _unit(van_id):
    doc = await db.units.find_one({"business_key": BKEY, "key": van_id})
    if not doc:
        raise ValueError(f"No van called {van_id}.")
    from models import Unit
    return Unit.from_mongo(doc)


async def van_rows(units, biz):
    plans, ontime = await today_plans(biz.demo_date), await _ontime()
    clock = biz.settings.demo_clock_minutes
    rows = []
    for u in units:
        plan = plans.get(u.key)
        keys = [r["stop_key"] for r in (plan.stops if plan else [])]
        docs = await _stop_docs(keys)
        pos = van_position(plan, {k: (d["lat"], d["lon"]) for k, d in docs.items()}, u.start_location, u.end_location, clock)
        nxt = plan.stops[pos["next_index"]] if plan and pos["next_index"] < len(plan.stops) else None
        good, runs = ontime.get(u.key, (0, 0))
        rows.append({"van_id": u.key, "name": u.name, "driver": u.driver_name,
                     "shift": f"{fmt_time(u.shift_start)} to {fmt_time(u.shift_end)}", "stops_today": len(keys),
                     "spare_minutes": plan.spare_minutes if plan else 0,
                     "next_stop": docs[nxt["stop_key"]]["customer_name"] if nxt else None,
                     "next_stop_eta": fmt_time(nxt["arrival"]) if nxt else None,
                     "on_time_rate": round(100 * good / runs, 1) if runs else None})
    return rows


async def t_fleet_summary(biz, **_):
    return {"vans": await van_rows(await load_units(), biz)}


async def t_van_route(biz, van_id, **_):
    u = await _unit(van_id)
    plan = (await today_plans(biz.demo_date)).get(u.key)
    rows = plan.stops if plan else []
    docs = await _stop_docs([r["stop_key"] for r in rows])
    return {"van_id": u.key, "stops": [{"position": i + 1, "stop_key": r["stop_key"], "name": docs[r["stop_key"]]["customer_name"],
                                        "eta": fmt_time(r["arrival"]),
                                        "window": f"{fmt_time(docs[r['stop_key']]['window_start'])} to {fmt_time(docs[r['stop_key']]['window_end'])}"}
                                       for i, r in enumerate(rows) if r["stop_key"] in docs]}


NOISE = re.compile(r"\b(pickup|pick-up|pick up|drop-off|dropoff|drop off|drop|delivery|stop|the)\b", re.I)


def _lev(a, b):
    row = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, row[0] = row[0], i
        for j, cb in enumerate(b, 1):
            prev, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, prev + (ca != cb))
    return row[-1]


def _match(query, cands):
    """cands: [(item, [texts])]. Case-insensitive substring first, then closest edit distance (within ~40%)."""
    q = re.sub(r"\s+", " ", NOISE.sub(" ", query)).strip().lower() or query.lower()
    hits = [c for c in cands if any(q in t.lower() for t in c[1] if t)]
    if hits:
        return hits[0][0]
    scored = [(min(_lev(q, t.lower()[:len(q) + 4]) for t in c[1] if t), c[0]) for c in cands if any(c[1])]
    best = min(scored, key=lambda x: x[0], default=None)
    return best[1] if best and best[0] <= max(2, int(len(q) * 0.4)) else None


def _option_facts(o):
    pb = o.get("pass_by") or {}
    return {"added_minutes": o.get("added_minutes"), "added_miles": o.get("added_miles"), "pass_by": pb.get("line"),
            "added_cost": o.get("added_cost")}


async def _booked_facts(stop_key):
    q = await db.quotes.find_one({"business_key": BKEY, "status": "accepted", "booking.stop_keys": stop_key}, {"_id": 0})
    req = q and await db.requests.find_one({"business_key": BKEY, "key": q["request_key"]}, {"_id": 0, "options": 1})
    o = req and find_option(req, q["option_id"])
    return _option_facts(o) if o else None


async def _request_cands(van_id):
    cands = []
    async for r in db.requests.find({"business_key": BKEY, "status": {"$nin": ["accepted", "declined"]}, "options": {"$ne": None}},
                                    {"_id": 0, "key": 1, "number": 1, "sender": 1, "details": 1, "job": 1, "options": 1}):
        opts = r.get("options") or {}
        o = next((c for c in (opts.get("cards") or []) + (opts.get("others") or []) if c.get("unit_key") == van_id), None)
        if not o:
            continue
        texts = [r.get("sender")] + [d.get("value") for d in r.get("details") or [] if d.get("key") in ("customer", "company")]
        texts += [x for s in ((r.get("job") or {}).get("stops") or []) for x in (s.get("name"), s.get("address"))]
        cands.append(((r, o), [str(t) for t in texts if t]))
    return cands


def _pending_facts(r, o):
    pick = next((s for s in o.get("new_stops") or [] if s.get("kind") == "pickup"), {})
    return {"request_key": r["key"], "request_number": r["number"], "status": "not booked yet", "name": pick.get("name"),
            "address": pick.get("address"), "position": pick.get("position"), "arrival": pick.get("arrival_label"),
            "price": o.get("price"), "is_cheapest": "Cheapest" in (o.get("labels") or []), **_option_facts(o)}


async def _open_request_match(van_id, query):
    """REQ-911: an open inbox request with an option on this van, matched by customer name or address."""
    hit = _match(query, await _request_cands(van_id))
    return _pending_facts(*hit) if hit else None


async def _find_node(nodes, stop_key):
    node = next((n for n in nodes if n["key"] == stop_key), None)
    if node:
        return node
    docs = await _stop_docs([n["key"] for n in nodes])
    cands = [(n, [n.get("customer_name"), (docs.get(n["key"]) or {}).get("address")]) for n in nodes]
    cands.sort(key=lambda c: (docs.get(c[0]["key"]) or {}).get("source") != "quote")  # stops booked today win ties
    hit = _match(stop_key, cands)
    if hit:
        return hit
    by_key = {n["key"]: n for n in nodes}
    booked = []
    async for q in db.quotes.find({"business_key": BKEY, "status": "accepted"}, {"_id": 0, "customer": 1, "booking": 1}):
        b = q.get("booking") or {}
        first = next((by_key[k] for k in b.get("stop_keys") or [] if k in by_key), None)
        if first:
            booked.append((first, [str(t) for t in (b.get("customer"), q.get("customer")) if t]))
    return _match(stop_key, booked)


def _stop_effect(u, nodes, node, s, travel):
    stop_key = node["key"]
    unit = u.public()
    with_it = compute_route(unit, nodes, s, travel=travel)
    without = Base(unit, [n for n in nodes if n["key"] != stop_key], s, travel, None)
    d_drive = with_it["driving_minutes"] - without.result["driving_minutes"]
    d_miles = with_it["total_miles"] - without.result["total_miles"]
    pb = pass_by(u.name, without, node)
    idx = [n["key"] for n in nodes].index(stop_key)
    stop_row = next((r for r in with_it.get("stops", []) if r.get("stop_key") == stop_key), None)
    minutes = int(half_up(max(0.0, d_drive) + node["service_minutes"], 0))
    miles = half_up(max(0.0, d_miles), 1)
    # Every stop on today's route is booked; seeded stops have no quote, so the engine's added_cost comes from here.
    return {"van_id": u.key, "stop_key": stop_key, "name": node["customer_name"], "position": idx + 1, "status": "booked",
            "arrival": fmt_time(stop_row["arrival"]) if stop_row and stop_row.get("arrival") is not None else None,
            "added_minutes": minutes, "added_miles": miles, "added_cost": added_cost(minutes, miles, s),
            "window": f"{fmt_time(node['window_start'])} to {fmt_time(node['window_end'])}",
            "pass_by": pb["line"] if pb else None}


async def t_explain_stop(biz, van_id, stop_key, **_):
    u = await _unit(van_id)
    s = biz.settings.model_dump()
    await ensure_matrix(s)
    travel = matrix.make_travel(s)
    nodes = await today_nodes(u, biz.demo_date)
    node = await _find_node(nodes, stop_key)
    if not node:
        pending = await _open_request_match(u.key, stop_key)
        if pending:
            return {"van_id": u.key, **pending}
        return {"van_id": u.key, "matched": False, "stop_names": [n["customer_name"] for n in nodes]}
    out = _stop_effect(u, nodes, node, s, travel)
    booked = await _booked_facts(node["key"])
    if booked:
        out.update(booked_today=True, **booked)
    return out


async def t_get_options(biz, request_key, **_):
    r = await db.requests.find_one({"business_key": BKEY, "key": request_key}, {"_id": 0, "options": 1, "number": 1})
    if not r:
        raise ValueError(f"No request {request_key}.")
    opts = r.get("options") or {}
    keep = ("labels", "unit_name", "price", "added_minutes", "added_miles", "pickup_label", "dropoff_label", "customer_line")
    return {"request_key": request_key, "cards": [{k: c.get(k) for k in keep} for c in opts.get("cards", [])]}


async def t_move_stop(biz, van_id, stop_key, new_position, **_):
    u = await _unit(van_id)
    s = biz.settings.model_dump()
    async with data_lock:
        await ensure_matrix(s)
        sm = await learned_service_map()
        nodes = await today_nodes(u, biz.demo_date, sm)
        keys = [n["key"] for n in nodes]
        if stop_key not in keys:
            raise ValueError(f"{stop_key} isn't on {u.name}'s route today.")
        idx = max(0, min(int(new_position) - 1, len(keys) - 1))
        order = [n for n in nodes if n["key"] != stop_key]
        order.insert(idx, nodes[keys.index(stop_key)])
        travel = matrix.make_travel(s)
        before = compute_route(u.public(), nodes, s, travel=travel)
        after = compute_route(u.public(), order, s, travel=travel)
        if not after["feasible"]:
            return {"moved": False, "reason": "That order breaks a time window.", "before_minutes": round(before["total_minutes"])}
        await apply_order([n["key"] for n in order])
        await recompute_unit(u, s, biz.demo_date, sm)
        reorder = await auto_optimize(u, s, biz.demo_date, sm, biz.settings.demo_clock_minutes)
    return {"moved": True, "new_position": idx + 1, "before_minutes": round(before["total_minutes"]),
            "after_minutes": round(after["total_minutes"]), "spare_minutes_after": after["spare_minutes"],
            "auto_reorder": reorder["text"] if reorder else None}


async def t_save_rule(biz, text, **_):
    res = await db.agent_rules.insert_one({"business_id": BKEY, "text": text.strip()[:300], "active": True,
                                           "created_at": datetime.now(timezone.utc).isoformat()})
    return {"rule_id": str(res.inserted_id)}


HANDLERS = {"get_fleet_summary": t_fleet_summary, "get_van_route": t_van_route, "explain_stop": t_explain_stop,
            "get_options": t_get_options, "move_stop": t_move_stop, "save_rule": t_save_rule}


async def run_tool(scope, name, args, biz):
    try:
        result = await HANDLERS[name](biz, **args) if name in HANDLERS else {"error": f"Unknown tool {name}."}
    except Exception as exc:
        result = {"error": str(exc) or "Tool failed."}
    text = json.dumps(result, default=str)
    await db.events.insert_one({"ts": datetime.now(timezone.utc).isoformat(), "scope": scope, "tool": name, "args": args,
                                "result_summary": text[:300]})
    return text


async def system_prompt(scope, biz):
    units = [u for u in await load_units() if scope == "dispatch" or u.key == scope]
    s = biz.settings
    rules = [r["text"] async for r in db.agent_rules.find({"business_id": BKEY, "active": True}).sort("created_at", 1)]
    vans = "\n".join(f"- {v['name']} ({v['van_id']}): driver {v['driver']}, shift {v['shift']}, {v['stops_today']} stops today, "
                     f"{v['spare_minutes']} spare minutes, next stop {v['next_stop'] or 'none'} at {v['next_stop_eta'] or '-'}, "
                     f"on-time {v['on_time_rate']}%" for v in await van_rows(units, biz))
    return (f"Business: {biz.name} ({biz.type}). Today is {biz.demo_date}, demo clock {fmt_time(s.demo_clock_minutes)}.\n"
            f"Vans in scope:\n{vans}\n"
            f"Pricing: cost ${s.wage_per_hour}/hour and ${s.cost_per_mile}/mile, markup {s.markup_pct}%, floor ${s.floor_recurring} a visit "
            f"(${s.floor_one_off} one-off), usual price ${s.usual_recurring} a visit (${s.usual_one_off} one-off).\n"
            f"Active rules:\n" + ("\n".join(f"- {r}" for r in rules) or "- none") + f"\n\n{INSTRUCTIONS}")


async def complete(messages, tool_choice):
    base = os.environ["AGENT_API_BASE"].rstrip("/")
    url = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
    body = {"model": os.environ.get("AGENT_MODEL") or "gpt-6-luna", "messages": messages, "tools": TOOLS,
            "tool_choice": tool_choice, "max_completion_tokens": 300, "reasoning_effort": "none"}
    timeout = float(os.environ.get("AGENT_TIMEOUT_SECONDS") or 15)
    async with httpx.AsyncClient(timeout=timeout) as client:
        res = await client.post(url, json=body, headers={"Authorization": f"Bearer {os.environ['AGENT_API_KEY']}"})
    if res.status_code >= 400:
        raise RuntimeError(f"model HTTP {res.status_code}: {res.text[:300]}")
    return res.json()["choices"][0]["message"]


def history_messages(turns):
    out = []
    for t in turns[-HISTORY:]:
        if t.get("text"):
            out.append({"role": "user" if t["role"] == "owner" else "assistant", "content": t["text"]})
    return out


def tool_label(name, result):
    """Chat label for an explain_stop line, from the tool result."""
    if name != "explain_stop":
        return {}
    r = json.loads(result)
    if r.get("status") == "not booked yet":
        return {"label": "Not booked yet", "stop_name": r.get("name") or r.get("address")}
    return {"label": "Booked", "stop_name": r.get("name")} if r.get("name") else {}


BOOKING_WORDS = ("not booked yet", "isn't booked", "is not booked", "is booked", "already booked", "booked today")


def with_booking_status(answer, lines):
    """Task 7: a reply that explains a stop always says "booked" or "not booked yet", matching the chip."""
    for c in lines:
        label = c.get("label")
        said = answer.lower().replace("\u2019", "'")
        if label and label.lower() not in said and not any(w in said for w in BOOKING_WORDS):
            answer = f"{answer} ({c.get('stop_name') or 'This stop'}: {label.lower()}.)"
    return answer


async def reply(scope, text, turns):
    """Returns (reply_text, tool_lines)."""
    if await over_limit():
        return LIMIT_REPLY, []
    biz = await get_business()
    messages = [{"role": "system", "content": await system_prompt(scope, biz)}, *history_messages(turns),
                {"role": "user", "content": text}]
    lines = []
    try:
        return await _rounds(scope, messages, biz, lines), lines
    except Exception as exc:
        logger.warning("Agent model call failed: %s", exc)
        return ERROR_REPLY, lines


def _tool_args(call):
    try:
        return json.loads(call["function"].get("arguments") or "{}")
    except ValueError:
        return {}


async def _run_calls(scope, calls, biz, messages, lines):
    for c in calls:
        name = c["function"]["name"]
        args = _tool_args(c)
        result = await run_tool(scope, name, args, biz)
        messages.append({"role": "tool", "tool_call_id": c["id"], "content": result})
        lines.append({"name": name, "args": args, **tool_label(name, result)})


async def _rounds(scope, messages, biz, lines):
    """Model/tool rounds; returns the reply text (tool lines are appended to `lines`)."""
    for rnd in range(MAX_TOOL_ROUNDS + 1):
        if not await take_call():
            return LIMIT_REPLY
        msg = await complete(messages, "auto" if rnd < MAX_TOOL_ROUNDS else "none")
        calls = msg.get("tool_calls") or []
        if not calls or rnd == MAX_TOOL_ROUNDS:
            content = (msg.get("content") or "").split("</think>")[-1].strip()
            return with_booking_status(content, lines) if content else ERROR_REPLY
        messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": calls})
        await _run_calls(scope, calls, biz, messages, lines)
    return ERROR_REPLY
