"""Engine actions API: price, run all seeded requests, what-if, accept, undo, stats."""
import logging
import math
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from booking_common import after_undo
from core import (BKEY, data_lock, db, demo_week, ensure_matrix, get_business, learned_service_map, load_units,
                  recompute_unit, route_nodes, stops_for_day, today_plans, unit_stops)
from engine import matrix
from engine.insertion import PriceCtx, build_nodes, price_unit, region_of, run_engine
from engine.jobs import validate_job
from engine.pricing import added_cost, half_up
from engine.rules import active_rules, rules_sig
from engine.timing import compute_route, fmt_time
from models import Stop, Unit
from position import van_position
from routes_api import auto_optimize, restore_seqs

router = APIRouter(prefix="/api")
logger = logging.getLogger("drivepast.engine")
STALE = "This slot is no longer free. Price it again."
ENGINE_FAIL = "The engine hit a problem on this request. Try again."
HIDDEN = {"nodes", "base_keys", "_extras"}


def friendly(status, message):
    return JSONResponse(status_code=status, content={"detail": {"message": message}})


def clean(r):
    return {k: v for k, v in r.items() if k not in HIDDEN} if r else None


async def engine_context(job, biz, unit_key=None):
    s = biz.settings.model_dump()
    await ensure_matrix(s)
    travel = matrix.make_travel(s)
    f = job["frequency"]
    day = f["date"] if f["type"] == "one_off" else None
    service_map = await learned_service_map()
    ctx = []
    for u in await load_units():
        if unit_key and u.key != unit_key:
            continue
        ctx.append((u.public(), route_nodes(stops_for_day(await unit_stops(u.key), day), service_map)))
    return s, travel, ctx, day, day == biz.demo_date


async def store_options(out, job, request_key, day):
    found = [r for r in out["results"] if r["feasible"]]
    if out.get("shifted") and out["shifted"].get("found"):
        found.append(out["shifted"]["winner"])
    opts = out.get("options") or {}
    raw = opts.pop("_raw", [])
    for r, c in zip(raw, opts.get("cards", []) + opts.get("others", [])):
        r.setdefault("option_id", uuid.uuid4().hex[:12])
        c["option_id"] = r["option_id"]
        if all(r is not f for f in found):
            found.append(r)
    docs = []
    for r in found:
        r.setdefault("option_id", uuid.uuid4().hex[:12])
        docs.append({"option_id": r["option_id"], "business_key": BKEY, "unit_key": r["unit_key"], "request_key": request_key,
                     "job": job, "day": day, "sequence": r["sequence"], "base_keys": r["base_keys"], "nodes": r["nodes"],
                     "price": r["price"], "added_minutes": r["added_minutes"], "added_miles": r["added_miles"],
                     "new_stops": r["new_stops"],
                     "added_cost": r["added_cost"], "created_at": datetime.now(timezone.utc).isoformat()})
    if docs:
        await db.engine_options.insert_many(docs)
        old = await db.engine_options.find({}, {"_id": 1}).sort("created_at", -1).skip(500).to_list(5000)
        if old:
            await db.engine_options.delete_many({"_id": {"$in": [o["_id"] for o in old]}})


async def load_rules():
    return active_rules([d async for d in db.agent_rules.find({"business_id": BKEY, "active": True})])


async def refresh_for_rules(r):
    """Re-price an open request's options when the active rules changed since they were priced."""
    opts = r.get("options")
    if not opts or r.get("job_status") != "ready" or r.get("status") not in ("new", "needs_info", "priced"):
        return r
    if opts.get("rules_sig", "") == rules_sig(await load_rules()):
        return r
    res = await price_job(r["job"], await get_business(), None, r["key"])
    await db.requests.update_one({"_id": r["_id"]}, {"$set": {"options": res["options"]}})
    return {**r, "options": res["options"]}


async def price_job(job, biz, unit_key=None, request_key=None):
    s, travel, ctx, day, same_day = await engine_context(job, biz, unit_key)
    if unit_key and not ctx:
        raise HTTPException(404, "We couldn't find that van.")
    rules = await load_rules()
    started = time.perf_counter()
    out = run_engine(ctx, job, s, travel, biz.settings.demo_clock_minutes, same_day, with_options=True, rules=rules)
    out["options"]["rules_sig"] = rules_sig(rules)
    ms = round((time.perf_counter() - started) * 1000, 1)
    await store_options(out, job, request_key, day)
    shifted = out["shifted"]
    if shifted and shifted.get("winner"):
        shifted = {**shifted, "winner": clean(shifted["winner"])}
    return {"priceable": True, "request_key": request_key, "frequency": job["frequency"], "ms": ms,
            "results": [clean(r) for r in out["results"]], "winner_unit_key": out["winner_unit_key"],
            "winner": clean(out["winner"]), "shifted": shifted, "options": out["options"]}


class PriceIn(BaseModel):
    request_key: Optional[str] = None
    job: Optional[Dict[str, Any]] = None
    unit_key: Optional[str] = None


@router.get("/engine/jobs")
async def engine_jobs():
    cur = db.requests.find({"business_key": BKEY}).sort("number", 1)
    return [{"request_key": r["key"], "number": r["number"], "source": r["source"], "sender": r["sender"],
             "raw_text": r["raw_text"], "job_status": r.get("job_status"), "job_reason": r.get("job_reason"),
             "job_summary": r.get("job_summary"), "job": r.get("job")} async for r in cur]


@router.post("/engine/price")
async def engine_price(body: PriceIn):
    biz = await get_business()
    job = body.job
    if body.request_key:
        req = await db.requests.find_one({"business_key": BKEY, "key": body.request_key})
        if not req:
            raise HTTPException(404, "We couldn't find that request.")
        if req.get("job_status") != "ready":
            return {"priceable": False, "request_key": req["key"], "reason": req.get("job_reason") or "This request can't be priced yet."}
        job = req["job"]
    problem = validate_job(job)
    if problem:
        return friendly(422, problem)
    return await price_job(job, biz, body.unit_key, body.request_key)


@router.post("/engine/run-all")
async def engine_run_all():
    biz = await get_business()
    out = []
    async for req in db.requests.find({"business_key": BKEY}).sort("number", 1):
        head = {"request_key": req["key"], "number": req["number"], "summary": req.get("job_summary")}
        if req.get("job_status") != "ready":
            out.append({**head, "priceable": False, "reason": req.get("job_reason")})
            continue
        try:
            out.append({**head, **(await price_job(req["job"], biz, None, req["key"]))})
        except Exception:
            logger.exception("Engine failed on %s", req["key"])
            out.append({**head, "priceable": True, "error": ENGINE_FAIL})
    return {"results": out}


class WhatIfIn(BaseModel):
    stop_key: str
    to_unit_key: str


@router.post("/engine/what-if")
async def engine_what_if(body: WhatIfIn):
    biz = await get_business()
    stop = Stop.from_mongo(await db.stops.find_one({"business_key": BKEY, "key": body.stop_key}))
    if not stop:
        raise HTTPException(404, "We couldn't find that stop.")
    units = {u.key: u for u in await load_units()}
    src, dst = units.get(stop.unit_key), units.get(body.to_unit_key)
    if not dst:
        raise HTTPException(404, "We couldn't find that van.")
    if dst.key == src.key:
        return friendly(422, "Pick a different van to move it to.")
    s = biz.settings.model_dump()
    await ensure_matrix(s)
    travel, sm = matrix.make_travel(s), await learned_service_map()
    day = stop.date if stop.recurrence == "one_off" else None
    a_nodes = route_nodes(stops_for_day(await unit_stops(src.key), day), sm)
    before = compute_route(src.public(), a_nodes, s, travel=travel)
    after = compute_route(src.public(), [n for n in a_nodes if n["key"] != stop.key], s, travel=travel)
    svc = sm.get(stop.key, stop.service_minutes)
    a_min = int(half_up(max(0.0, before["driving_minutes"] - after["driving_minutes"]) + svc, 0))
    a_mi = half_up(max(0.0, before["total_miles"] - after["total_miles"]), 1)
    a_cost = added_cost(a_min, a_mi, s)
    job = {"stops": [{"ref": "moved", "kind": stop.kind, "name": stop.customer_name, "address": stop.address, "lat": stop.lat,
                      "lon": stop.lon, "window_start": stop.window_start, "window_end": stop.window_end,
                      "service_minutes": svc, "items": getattr(stop, "items", 1)}],
           "pairs": [], "frequency": {"type": "weekday"}}
    b_nodes = route_nodes(stops_for_day(await unit_stops(dst.key), day), sm)
    r = price_unit(dst.public(), b_nodes, PriceCtx(job, build_nodes(job, s), s, travel))
    to = {"unit_key": dst.key, "unit_name": dst.name, "feasible": r["feasible"]}
    if r["feasible"]:
        to.update(minutes=r["added_minutes"], miles=r["added_miles"], cost=r["added_cost"], arrival_label=r["new_stops"][0]["arrival_label"],
                  line=f"{dst.name} adds {r['added_minutes']} min and {r['added_miles']:.1f} mi (${r['added_cost']:.2f}), arriving at {r['new_stops'][0]['arrival_label']}.")
    else:
        to.update(reason=r["reason"], where=r["where"], line=f"{dst.name} can't take it: {r['reason']}.")
    return {"saved": False, "stop": {"key": stop.key, "name": stop.customer_name, "address": stop.address},
            "from": {"unit_key": src.key, "unit_name": src.name, "minutes": -a_min, "miles": -a_mi, "cost": -a_cost,
                     "line": f"{src.name} saves {a_min} min and {a_mi:.1f} mi (${a_cost:.2f})."},
            "to": to}


class AcceptIn(BaseModel):
    option_id: str
    start_date: Optional[str] = None


def assign_seqs(seq):
    out, i = {}, 0
    while i < len(seq):
        if not seq[i].get("is_new"):
            i += 1
            continue
        j = i
        while j < len(seq) and seq[j].get("is_new"):
            j += 1
        lo = seq[i - 1]["seq"] if i > 0 else 0.0
        hi = seq[j]["seq"] if j < len(seq) else lo + 1.0
        for t in range(j - i):
            out[seq[i + t]["key"]] = lo + (hi - lo) * (t + 1) / (j - i + 1)
        i = j
    return out


@router.post("/engine/accept")
async def engine_accept(body: AcceptIn):
    async with data_lock:
        opt = await db.engine_options.find_one({"business_key": BKEY, "option_id": body.option_id})
        if not opt:
            raise HTTPException(404, "We couldn't find that option. Price it again.")
        biz = await get_business()
        s = biz.settings.model_dump()
        unit = Unit.from_mongo(await db.units.find_one({"business_key": BKEY, "key": opt["unit_key"]}))
        sm = await learned_service_map()
        day_stops = route_nodes(stops_for_day(await unit_stops(unit.key), opt["day"]), sm)
        if [n["key"] for n in day_stops] != opt["base_keys"]:
            return friendly(409, STALE)
        by_key = {n["key"]: n for n in day_stops} | {n["key"]: n for n in opt["nodes"]}
        seq = [by_key[k] for k in opt["sequence"]]
        await ensure_matrix(s)
        timed = compute_route(unit.public(), seq, s, travel=matrix.make_travel(s))
        if not timed["feasible"]:
            return friendly(409, STALE)
        arrival = {r["stop_key"]: r["arrival"] for r in timed["stops"]}
        prev_seqs = {st["key"]: st["seq"] for st in await unit_stops(unit.key)}
        f, seqs = opt["job"]["frequency"], assign_seqs(seq)
        new_keys = {n["key"]: f"q-{uuid.uuid4().hex[:8]}" for n in opt["nodes"]}
        refs = {n["ref"]: new_keys[n["key"]] for n in opt["nodes"]}
        partner = {}
        for p, d in opt["job"].get("pairs") or []:
            partner.setdefault(refs[p], refs[d])
            partner.setdefault(refs[d], refs[p])
        now = datetime.now(timezone.utc).isoformat()
        docs = []
        for idx, n in enumerate(opt["nodes"]):
            key = new_keys[n["key"]]
            at = arrival[n["key"]]
            ws, we = max(n["window_start"], math.floor(at - 15)), min(n["window_end"], math.ceil(at + 15))
            docs.append(Stop(
                key=key, business_key=BKEY, unit_key=unit.key, seq=seqs[n["key"]], customer_name=n["customer_name"],
                customer_type="From a quote", address=n["address"], area=region_of(n), lat=n["lat"], lon=n["lon"],
                kind=n["kind"], items=n["items"], window_start=ws, window_end=we,
                service_minutes=n["service_minutes"], recurrence={"one_off": "one_off", "weekdays": "weekdays"}.get(f["type"], "weekday"),
                weekdays=f.get("days"), date=f.get("date"),
                start_date=(body.start_date or f.get("start_date")) if f["type"] == "weekday" else None,
                price_per_visit=opt["price"] if idx == 0 else 0.0, paired_stop_key=partner.get(key), source="quote",
                request_key=opt["request_key"], option_id=opt["option_id"], approximate=n.get("approximate", False), created_at=now,
            ).to_mongo())
        await db.stops.insert_many(docs)
        await db.change_log.insert_one({"business_key": BKEY, "unit_key": unit.key, "stop_keys": list(new_keys.values()),
                                        "option_id": opt["option_id"], "request_key": opt["request_key"], "undone": False,
                                        "prev_seqs": prev_seqs, "created_at": now})
        await recompute_unit(unit, s, biz.demo_date, sm)
        optimized = await auto_optimize(unit, s, biz.demo_date, sm, biz.settings.demo_clock_minutes)
    return {"ok": True, "message": f"Booked on {unit.name}.", "unit_key": unit.key, "stop_keys": list(new_keys.values()), "optimized": optimized}


@router.post("/engine/undo")
async def engine_undo():
    ch = await db.change_log.find_one({"business_key": BKEY, "undone": False}, sort=[("created_at", -1), ("_id", -1)])
    if not ch:
        return {"ok": False, "message": "Nothing to undo"}
    return await undo_change(ch)


async def undo_change(ch):
    async with data_lock:
        ch = await db.change_log.find_one({"_id": ch["_id"], "undone": False})
        if not ch:
            return {"ok": False, "message": "Nothing to undo"}
        biz = await get_business()
        unit = Unit.from_mongo(await db.units.find_one({"business_key": BKEY, "key": ch["unit_key"]}))
        await db.stops.delete_many({"business_key": BKEY, "key": {"$in": ch["stop_keys"]}})
        await restore_seqs(ch.get("prev_seqs"))
        await db.change_log.update_one({"_id": ch["_id"]}, {"$set": {"undone": True}})
        await recompute_unit(unit, biz.settings.model_dump(), biz.demo_date)
    await after_undo(ch)
    from activity import log
    await log("owner", f"Undid the booking on {unit.name}.", "undo")
    return {"ok": True, "message": f"Undid the last booking on {unit.name}.", "unit_key": unit.key, "removed_stop_keys": ch["stop_keys"]}


@router.get("/engine/options/{option_id}")
async def engine_option(option_id: str):
    """Read-only view of a priced option, used by 'Show on map'. Never books anything."""
    opt = await db.engine_options.find_one({"business_key": BKEY, "option_id": option_id}, {"_id": 0, "job": 0, "nodes": 0})
    if not opt:
        raise HTTPException(404, "We couldn't find that option. Price it again.")
    return opt


@router.get("/landing/price")
async def landing_price():
    """The landing's example: a recurring visit that adds 4 minutes and 0.6 miles, priced with the current Settings."""
    from engine.pricing import price_quote
    s = (await get_business()).settings.model_dump()
    minutes, miles = 4, 0.6
    cost = added_cost(minutes, miles, s)
    q = price_quote(minutes, miles, cost, "Van 2", {"type": "weekday"}, s)
    return {"added_minutes": minutes, "added_miles": miles,
            "time_cost": half_up(minutes * s["wage_per_hour"] / 60), "mile_cost": half_up(miles * s["cost_per_mile"]),
            "cost": cost, "cost_with_markup": half_up(cost * (1 + s["markup_pct"] / 100)),
            "floor": q["floor"], "usual": q["usual"], "offer": q["price"],
            "wage_per_hour": s["wage_per_hour"], "cost_per_mile": s["cost_per_mile"], "markup_pct": s["markup_pct"]}


@router.get("/map/fleet")
async def map_fleet():
    biz = await get_business()
    plans = await today_plans(biz.demo_date)
    out = []
    for u in await load_units():
        plan = plans.get(u.key)
        by_key = {x["key"]: x for x in await unit_stops(u.key)}
        stops = []
        for r in (plan.stops if plan else []):
            s = by_key.get(r["stop_key"])
            if s:
                stops.append({"key": s["key"], "seq": r["seq"], "lat": s["lat"], "lon": s["lon"], "name": s["customer_name"],
                              "address": s["address"], "arrival_label": fmt_time(r["arrival"]),
                              "window_label": f"{fmt_time(s['window_start'])} to {fmt_time(s['window_end'])}",
                              "is_new": s.get("source") == "quote", "done": s.get("done_date") == biz.demo_date})
        coords = {k: (v["lat"], v["lon"]) for k, v in by_key.items()}
        out.append({"unit_key": u.key, "name": u.name, "nickname": u.nickname, "color": u.color,
                    "start_location": u.start_location, "end_location": u.end_location, "stops": stops,
                    "spare_minutes": plan.spare_minutes if plan else None,
                    "position": van_position(plan, coords, u.start_location, u.end_location, biz.settings.demo_clock_minutes)})
    return {"units": out}


@router.get("/engine/changes")
async def engine_changes():
    cur = db.change_log.find({"business_key": BKEY}, {"_id": 0}).sort("created_at", -1)
    return await cur.to_list(100)


async def run_stats():
    pipeline = [{"$match": {"business_key": BKEY}},
                {"$group": {"_id": {"u": "$unit_key", "pm": {"$gte": ["$window_start", 720]}}, "runs": {"$sum": 1},
                            "on_time": {"$sum": {"$cond": ["$on_time", 1, 0]}},
                            "late": {"$sum": {"$cond": [{"$gt": ["$actual_arrival", "$window_end"]}, 1, 0]}},
                            "late_min": {"$sum": {"$cond": [{"$gt": ["$actual_arrival", "$window_end"]},
                                                            {"$subtract": ["$actual_arrival", "$window_end"]}, 0]}}}}]
    out = {}
    async for r in db.run_history.aggregate(pipeline):
        out.setdefault(r["_id"]["u"], {})["pm" if r["_id"]["pm"] else "am"] = r
    return out


def rate(good, runs):
    return round(100 * good / runs, 1) if runs else None


async def stats_for(units):
    biz = await get_business()
    s = biz.settings.model_dump()
    await ensure_matrix(s)
    travel, sm = matrix.make_travel(s), await learned_service_map()
    plans, runs, week = await today_plans(biz.demo_date), await run_stats(), demo_week(biz.demo_date)
    out = []
    for u in units:
        plan = plans.get(u.key)
        all_stops = await unit_stops(u.key)
        by_key = {x["key"]: x for x in all_stops}
        today = [by_key[r["stop_key"]] for r in (plan.stops if plan else []) if r["stop_key"] in by_key]
        n = len(today)
        cost_total = (plan.total_minutes * s["wage_per_hour"] / 60 + plan.total_miles * s["cost_per_mile"]) if plan else 0
        days = []
        for d in week:
            r = compute_route(u.public(), route_nodes(stops_for_day(all_stops, d), sm), s, travel=travel)
            days.append({"date": d, "day": datetime.fromisoformat(d).strftime("%A"), "spare_minutes": r["spare_minutes"]})
        am, pm = runs.get(u.key, {}).get("am", {}), runs.get(u.key, {}).get("pm", {})
        total_runs = am.get("runs", 0) + pm.get("runs", 0)
        late = am.get("late", 0) + pm.get("late", 0)
        out.append({
            "unit_key": u.key, "unit_name": u.name, "nickname": u.nickname, "stops_count": n,
            "spare_minutes_today": plan.spare_minutes if plan else 0, "spare_minutes_by_weekday": days,
            "spare_minutes_week_total": sum(x["spare_minutes"] for x in days),
            "revenue_per_day": round(sum(x["price_per_visit"] for x in today), 2),
            "cost_per_stop": round(cost_total / n, 2) if n else 0,
            "on_time_rate": rate(am.get("on_time", 0) + pm.get("on_time", 0), total_runs),
            "morning_on_time_rate": rate(am.get("on_time", 0), am.get("runs", 0)),
            "afternoon_on_time_rate": rate(pm.get("on_time", 0), pm.get("runs", 0)),
            "late_runs": late, "total_runs": total_runs,
            "average_minutes_late": round((am.get("late_min", 0) + pm.get("late_min", 0)) / late, 1) if late else 0,
            "return_label": fmt_time(plan.return_time) if plan else "",
        })
    return out


@router.get("/stats/fleet")
async def fleet_stats():
    units = await stats_for(await load_units())
    return {"units": units, "week": demo_week((await get_business()).demo_date)}


@router.get("/stats/units/{unit_key}")
async def unit_stats_api(unit_key: str):
    unit = Unit.from_mongo(await db.units.find_one({"business_key": BKEY, "key": unit_key}))
    if not unit:
        raise HTTPException(404, "We couldn't find that van.")
    return (await stats_for([unit]))[0]
