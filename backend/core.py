"""Shared database handle and route-plan helpers (weekday plans, date plans, today's plan, travel matrix)."""
import asyncio
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from engine import matrix
from engine.timing import compute_route
from models import Business, RoutePlan, Stop, Unit
from seed import data as D

load_dotenv(Path(__file__).parent / ".env")
client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]
BKEY = D.BUSINESS_KEY
data_lock = asyncio.Lock()
WEEKDAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


async def get_business():
    doc = await db.businesses.find_one({"key": BKEY})
    if not doc:
        raise HTTPException(503, "Drivepast is still setting up. Try again in a moment.")
    return Business.from_mongo(doc)


async def learned_service_map():
    pipeline = [{"$match": {"business_key": BKEY}},
                {"$group": {"_id": "$stop_key", "avg": {"$avg": "$actual_service_minutes"}}}]
    return {r["_id"]: round(r["avg"], 2) async for r in db.run_history.aggregate(pipeline)}


async def load_units():
    return [Unit.from_mongo(u) async for u in db.units.find({"business_key": BKEY}).sort("key", 1)]


async def unit_stops(unit_key):
    cur = db.stops.find({"business_key": BKEY, "unit_key": unit_key})
    return [Stop.from_mongo(s).public() for s in await cur.to_list(2000)]


def weekday_key(date_iso):
    return WEEKDAY_KEYS[date.fromisoformat(date_iso).weekday()]


def stops_for_day(stops, date_iso=None):
    """Weekday route when date_iso is None, else that date's route (weekday + its weekdays + its one-offs)."""
    wd = weekday_key(date_iso) if date_iso else None
    keep = [s for s in stops if s.get("recurrence") == "weekday"
            or (date_iso and s.get("recurrence") == "weekdays" and wd in (s.get("weekdays") or []))
            or (date_iso and s.get("recurrence") == "one_off" and s.get("date") == date_iso)]
    return sorted(keep, key=lambda s: (s["seq"], s["key"]))


def route_nodes(stops, service_map, day=None):
    """Nodes for timing. With a day, stops the driver marked done that day carry done_at (minutes)."""
    out = []
    for s in stops:
        n = {**s, "service_minutes": service_map.get(s["key"], s["service_minutes"])}
        n.pop("done_at", None)
        if day and s.get("done_date") == day and s.get("done_minutes") is not None:
            n["done_at"] = float(s["done_minutes"])
        out.append(n)
    return out


def plan_dates(stops, demo_date):
    dates = {s["date"] for s in stops if s.get("recurrence") == "one_off" and s.get("date")}
    if any(s.get("recurrence") == "weekdays" and weekday_key(demo_date) in (s.get("weekdays") or []) for s in stops):
        dates.add(demo_date)
    if any(s.get("done_date") == demo_date for s in stops):
        dates.add(demo_date)
    return sorted(dates)


async def save_plan(unit_key, day_type, date_iso, result):
    q = {"business_key": BKEY, "unit_key": unit_key, "day_type": day_type, "date": date_iso}
    old = await db.route_plans.find_one({**q, "is_current": True})
    version = (old["version"] + 1) if old else 1
    await db.route_plans.delete_many({**q, "is_current": False})
    if old:
        await db.route_plans.update_one({"_id": old["_id"]}, {"$set": {"is_current": False}})
    suffix = date_iso or "weekday"
    plan = RoutePlan(key=f"{unit_key}-{suffix}-v{version}", business_key=BKEY, unit_key=unit_key, day_type=day_type,
                     date=date_iso, version=version, is_current=True,
                     computed_at=datetime.now(timezone.utc).isoformat(), **result)
    await db.route_plans.insert_one(plan.to_mongo())


async def recompute_unit(unit: Unit, s, demo_date, service_map=None):
    service_map = service_map if service_map is not None else await learned_service_map()
    travel = matrix.make_travel(s)
    stops = await unit_stops(unit.key)
    u = unit.public()
    await save_plan(unit.key, "weekday", None, compute_route(u, route_nodes(stops_for_day(stops), service_map), s, travel=travel))
    dates = plan_dates(stops, demo_date)
    for d in dates:
        await save_plan(unit.key, "date", d, compute_route(u, route_nodes(stops_for_day(stops, d), service_map, d), s, travel=travel))
    await db.route_plans.update_many(
        {"business_key": BKEY, "unit_key": unit.key, "day_type": "date", "is_current": True, "date": {"$nin": dates}},
        {"$set": {"is_current": False}})


async def recompute_all(s, demo_date):
    service_map = await learned_service_map()
    for unit in await load_units():
        await recompute_unit(unit, s, demo_date, service_map)


async def today_plans(demo_date):
    """Today's plan per unit: the demo date's plan if it has one, else the weekday plan."""
    out = {}
    cur = db.route_plans.find({"business_key": BKEY, "is_current": True,
                               "$or": [{"day_type": "weekday"}, {"day_type": "date", "date": demo_date}]})
    async for p in cur:
        if p["day_type"] == "date" or p["unit_key"] not in out:
            out[p["unit_key"]] = RoutePlan.from_mongo(p)
    return out


async def matrix_points():
    points = [Stop.from_mongo(s).public() for s in await db.stops.find({"business_key": BKEY, "source": "seed"}).to_list(5000)]
    seen = set()
    for u in await load_units():
        for loc in (u.start_location, u.end_location):
            k = matrix.node_key(loc)
            if k not in seen:
                seen.add(k)
                points.append(loc)
    return points


async def rebuild_matrix(s):
    return await matrix.build_matrix(db, s, await matrix_points())


async def ensure_matrix(s):
    """Load the stored matrix into memory if it matches the current settings, else rebuild it."""
    first = await db.travel_matrix.find_one({})
    if not first or first.get("sig") != matrix.signature(s):
        await rebuild_matrix(s)
        return
    if matrix._cache["sig"] == matrix.signature(s) and matrix._cache["pairs"]:
        return
    matrix.invalidate()
    matrix.make_travel(s)
    pairs = matrix._cache["pairs"]
    async for doc in db.travel_matrix.find({}):
        for dest, miles, mins in doc["dest"]:
            pairs[(doc["origin"], dest)] = (miles, mins)


def demo_week(demo_date):
    d = date.fromisoformat(demo_date)
    monday = d - timedelta(days=d.weekday()) if d.weekday() < 5 else d + timedelta(days=7 - d.weekday())
    return [(monday + timedelta(days=i)).isoformat() for i in range(5)]
