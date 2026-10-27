import asyncio
import hashlib
import logging
import os
import time
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException

from core import BKEY, data_lock, db, ensure_matrix, get_business, learned_service_map, plan_dates, recompute_unit, route_nodes, stops_for_day, unit_stops
from engine import matrix
from engine.optimize import optimize
from engine.timing import compute_route, haversine_miles
from models import Unit

router = APIRouter(prefix="/api")
logger = logging.getLogger("drivepast.routes")
UA = "Drivepast/1.0 (demo courier dispatch; street lines for map drawing)"
NO_LINES = "Street lines unavailable, showing straight lines."
_osrm = {"lock": asyncio.Lock(), "last": 0.0}


async def load_unit(unit_key):
    doc = await db.units.find_one({"business_key": BKEY, "key": unit_key})
    if not doc:
        raise HTTPException(404, "We couldn't find that van.")
    return Unit.from_mongo(doc)


async def today_nodes(unit, demo_date, sm=None):
    stops = await unit_stops(unit.key)
    day = demo_date if demo_date in plan_dates(stops, demo_date) else None
    return route_nodes(stops_for_day(stops, day), sm if sm is not None else await learned_service_map(), day)


async def apply_order(order_keys):
    """Give the reordered stops the same seq slots they held, in the new order."""
    docs = await db.stops.find({"business_key": BKEY, "key": {"$in": order_keys}}, {"_id": 0, "key": 1, "seq": 1}).to_list(None)
    slots = sorted(d["seq"] for d in docs)
    for k, seq in zip(order_keys, slots):
        await db.stops.update_one({"business_key": BKEY, "key": k}, {"$set": {"seq": seq}})


async def restore_seqs(prev):
    for k, seq in (prev or {}).items():
        await db.stops.update_one({"business_key": BKEY, "key": k}, {"$set": {"seq": seq}})


def summary(res):
    b, a = res["before"], res["after"]
    return {"improved": res["improved"], "saves_miles": round(b["total_miles"] - a["total_miles"], 1),
            "saves_minutes": round(b["total_minutes"] - a["total_minutes"]),
            "before_miles": round(b["total_miles"], 1), "after_miles": round(a["total_miles"], 1)}


async def run_optimizer(unit, s, demo_date, sm=None, clock=None):
    """Existing optimizer. With a clock, stops already done or passed stay put and only the rest is reordered."""
    await ensure_matrix(s)
    nodes = await today_nodes(unit, demo_date, sm)
    travel, u = matrix.make_travel(s), unit.public()
    if clock is None:
        return nodes, optimize(u, nodes, s, travel)
    timed = compute_route(u, nodes, s, travel=travel)
    done = {d["key"] async for d in db.stops.find({"business_key": BKEY, "unit_key": unit.key, "done_date": demo_date}, {"key": 1})}
    locked = [i for i, (n, r) in enumerate(zip(nodes, timed["stops"])) if n["key"] in done or r["departure"] <= clock]
    k = locked[-1] + 1 if locked else 0
    head, tail = nodes[:k], nodes[k:]
    sub = {**u, "start_location": head[-1], "shift_start": timed["stops"][k - 1]["departure"]} if head else u
    res = optimize(sub, tail, s, travel)
    order = head + res["order"]
    after = compute_route(u, order, s, travel=travel)
    improved = (res["improved"] and after["feasible"] and after["total_miles"] < timed["total_miles"] - 0.1
                and max_gap(after) <= max(GAP_LIMIT, max_gap(timed)) + 0.5)
    return nodes, {"order": order if improved else nodes, "before": timed, "after": after if improved else timed, "improved": improved}


GAP_LIMIT = 30


def max_gap(route):
    arr = [r["arrival"] for r in route["stops"]]
    return max((b - a for a, b in zip(arr, arr[1:])), default=0)


async def auto_optimize(unit, s, demo_date, sm, clock=None):
    """After a booking, stop done, stop move or fleet change: keep a new order only if it's shorter and feasible."""
    nodes, res = await run_optimizer(unit, s, demo_date, sm, clock)
    if not res["improved"]:
        return None
    await apply_order([n["key"] for n in res["order"]])
    await recompute_unit(unit, s, demo_date, sm)
    await db.time_shifts.delete_many({"business_key": BKEY, "unit_key": unit.key})
    out = summary(res)
    saved = round(res["before"]["driving_minutes"] - res["after"]["driving_minutes"])
    text = f"{unit.name} reordered, saves {saved} min" if saved >= 1 else f"{unit.name} reordered, saves under 1 min"
    await db.events.insert_one({"business_key": BKEY, "ts": datetime.now(timezone.utc).isoformat(), "kind": "reorder", "scope": "activity",
                                "van_id": unit.key, "text": text, "actor": "assistant", "line": f"{text} ({out['saves_miles']} mi shorter).",
                                "old_order": [n["key"] for n in nodes], "new_order": [n["key"] for n in res["order"]]})
    return {**out, "text": text}


async def mark_done(unit, stop_key, biz):
    """Mark a stop done at the demo clock. Returns (reorder, shifts) where shifts maps later stop keys to arrival change in minutes."""
    from core import today_plans
    s = biz.settings.model_dump()
    before = (await today_plans(biz.demo_date)).get(unit.key)
    old_arr = {r["stop_key"]: r["arrival"] for r in (before.stops if before else [])}
    res = await db.stops.update_one({"business_key": BKEY, "unit_key": unit.key, "key": stop_key},
                                    {"$set": {"done_date": biz.demo_date, "done_minutes": float(biz.settings.demo_clock_minutes)}})
    if not res.matched_count:
        raise HTTPException(404, "That stop isn't on this van.")
    sm = await learned_service_map()
    await recompute_unit(unit, s, biz.demo_date, sm)
    reorder = await auto_optimize(unit, s, biz.demo_date, sm, biz.settings.demo_clock_minutes)
    after = (await today_plans(biz.demo_date)).get(unit.key)
    rows = after.stops if after else []
    keys = [r["stop_key"] for r in rows]
    later = rows[keys.index(stop_key) + 1:] if stop_key in keys else []
    shifts = {r["stop_key"]: round(r["arrival"] - old_arr[r["stop_key"]]) for r in later
              if r["stop_key"] in old_arr and abs(r["arrival"] - old_arr[r["stop_key"]]) >= 1}
    await db.time_shifts.delete_many({"business_key": BKEY, "unit_key": unit.key})
    if shifts:
        await db.time_shifts.insert_one({"business_key": BKEY, "unit_key": unit.key, "done_key": stop_key, "shifts": shifts,
                                         "at": datetime.now(timezone.utc).isoformat()})
    return reorder, shifts


async def current_shifts(unit_key):
    """Time-jump tags from the last Done, for 60 s."""
    d = await db.time_shifts.find_one({"business_key": BKEY, "unit_key": unit_key})
    if not d or (datetime.now(timezone.utc) - datetime.fromisoformat(d["at"])).total_seconds() > 60:
        return {}
    return d["shifts"]


@router.post("/units/{unit_key}/stops/{stop_key}/done")
async def stop_done(unit_key: str, stop_key: str):
    async with data_lock:
        unit = await load_unit(unit_key)
        reorder, shifts = await mark_done(unit, stop_key, await get_business())
    return {"ok": True, "message": "Marked done.", "reorder": reorder, "shifts": shifts}


async def reoptimise_all():
    biz = await get_business()
    s, sm = biz.settings.model_dump(), await learned_service_map()
    for d in await db.units.find({"business_key": BKEY}).to_list(None):
        await auto_optimize(Unit.from_mongo(d), s, biz.demo_date, sm, biz.settings.demo_clock_minutes)


@router.post("/units/{unit_key}/optimize/preview")
async def optimize_preview(unit_key: str):
    unit = await load_unit(unit_key)
    biz = await get_business()
    nodes, res = await run_optimizer(unit, biz.settings.model_dump(), biz.demo_date)
    out = summary(res)
    if not res["improved"]:
        return {**out, "message": "This is already the shortest order we found"}
    pid = hashlib.sha1(f"{unit_key}{time.time()}".encode()).hexdigest()[:10]
    await db.route_proposals.insert_one({"business_key": BKEY, "key": pid, "unit_key": unit_key,
                                         "base_keys": [n["key"] for n in nodes], "order": [n["key"] for n in res["order"]],
                                         "summary": out, "created_at": datetime.now(timezone.utc).isoformat()})
    return {**out, "proposal_id": pid, "message": f"Saves {out['saves_miles']} mi and {out['saves_minutes']} min"}


@router.post("/units/{unit_key}/optimize/apply/{proposal_id}")
async def optimize_apply(unit_key: str, proposal_id: str):
    async with data_lock:
        p = await db.route_proposals.find_one({"business_key": BKEY, "key": proposal_id, "unit_key": unit_key})
        if not p:
            raise HTTPException(404, "That suggestion expired. Press Optimize route again.")
        unit = await load_unit(unit_key)
        biz = await get_business()
        s = biz.settings.model_dump()
        if [n["key"] for n in await today_nodes(unit, biz.demo_date)] != p["base_keys"]:
            raise HTTPException(409, "The route changed since then. Press Optimize route again.")
        prev = {st["key"]: st["seq"] for st in await unit_stops(unit_key)}
        await apply_order(p["order"])
        await db.route_changes.insert_one({"business_key": BKEY, "unit_key": unit_key, "prev_seqs": prev, "undone": False,
                                           "summary": p["summary"], "created_at": datetime.now(timezone.utc).isoformat()})
        await db.route_proposals.delete_many({"business_key": BKEY, "unit_key": unit_key})
        await recompute_unit(unit, s, biz.demo_date)
    return {"ok": True, "message": f"New order saved on {unit.name}.", **p["summary"]}


@router.get("/units/{unit_key}/optimize/last")
async def optimize_last(unit_key: str):
    ch = await db.route_changes.find_one({"business_key": BKEY, "unit_key": unit_key, "undone": False}, {"_id": 0, "summary": 1}, sort=[("created_at", -1)])
    return {"change": ch}


@router.post("/units/{unit_key}/optimize/undo")
async def optimize_undo(unit_key: str):
    async with data_lock:
        ch = await db.route_changes.find_one({"business_key": BKEY, "unit_key": unit_key, "undone": False}, sort=[("created_at", -1)])
        if not ch:
            return {"ok": False, "message": "Nothing to undo"}
        await restore_seqs(ch["prev_seqs"])
        await db.route_changes.update_one({"_id": ch["_id"]}, {"$set": {"undone": True}})
        unit = await load_unit(unit_key)
        biz = await get_business()
        await recompute_unit(unit, biz.settings.model_dump(), biz.demo_date)
    return {"ok": True, "message": f"Back to the previous order on {unit.name}."}


async def fetch_osrm(pts):
    async with _osrm["lock"]:
        wait = 1.0 - (time.monotonic() - _osrm["last"])
        if wait > 0:
            await asyncio.sleep(wait)
        try:
            coords = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in pts)
            url = f"{os.environ['OSRM_URL']}/route/v1/driving/{coords}"
            async with httpx.AsyncClient(timeout=10, headers={"User-Agent": UA}) as c:
                r = await c.get(url, params={"overview": "full", "geometries": "geojson"})
            data = r.json()
            if r.status_code != 200 or data.get("code") != "Ok":
                raise ValueError(data.get("code") or r.status_code)
            return trim_detours(data, pts)
        finally:
            _osrm["last"] = time.monotonic()


def _km(a, b):
    return haversine_miles(a[0], a[1], b[0], b[1]) * 1.609


def trim_detours(data, pts):
    """Split the street line at each stop; a leg that wanders far (a stop snapped onto a freeway) becomes a straight line."""
    route = data["routes"][0]
    line = [(round(lat, 6), round(lon, 6)) for lon, lat in route["geometry"]["coordinates"]]
    idx, start = [], 0
    for w in data["waypoints"]:
        la, lo = w["location"][1], w["location"][0]
        d2 = [(line[i][0] - la) ** 2 + (line[i][1] - lo) ** 2 for i in range(start, len(line))]
        hit = next((i for i, v in enumerate(d2) if v < 1e-10), None)
        start += hit if hit is not None else d2.index(min(d2))
        idx.append(start)
    out = []
    for k, leg in enumerate(route["legs"]):
        seg = line[idx[k]:idx[k + 1] + 1]
        if leg["distance"] / 1000 > max(1.5, 3 * _km(pts[k], pts[k + 1])) or len(seg) < 2:
            seg = [pts[k], pts[k + 1]]
        out.extend(seg if not out else seg[1:])
    return [[a, b] for a, b in out]


@router.get("/map/geometry/{unit_key}")
async def route_geometry(unit_key: str):
    unit = await load_unit(unit_key)
    biz = await get_business()
    plan = await db.route_plans.find_one({"business_key": BKEY, "unit_key": unit_key, "is_current": True,
                                          "$or": [{"day_type": "date", "date": biz.demo_date}, {"day_type": "weekday"}]},
                                         {"_id": 0, "stops.stop_key": 1, "day_type": 1}, sort=[("day_type", 1)])
    keys = [r["stop_key"] for r in (plan or {}).get("stops", [])]
    by_key = {d["key"]: d for d in await db.stops.find({"business_key": BKEY, "key": {"$in": keys}}, {"_id": 0, "key": 1, "lat": 1, "lon": 1}).to_list(None)}
    pts = [(unit.start_location["lat"], unit.start_location["lon"]), *[(by_key[k]["lat"], by_key[k]["lon"]) for k in keys if k in by_key],
           (unit.end_location["lat"], unit.end_location["lon"])]
    ck = hashlib.sha1(";".join(f"{a:.5f},{b:.5f}" for a, b in pts).encode()).hexdigest()
    hit = await db.route_geometry.find_one({"key": ck}, {"_id": 0, "coords": 1})
    if hit:
        return {"ok": True, "source": "cache", "coords": hit["coords"]}
    try:
        line = await fetch_osrm(pts)
    except Exception as e:  # noqa: BLE001
        logger.warning("Street routing failed for %s: %s", unit_key, e)
        return {"ok": False, "message": NO_LINES}
    await db.route_geometry.update_one({"key": ck}, {"$set": {"key": ck, "coords": line, "created_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
    return {"ok": True, "source": "osrm", "coords": line}
