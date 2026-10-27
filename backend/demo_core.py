"""Shared demo pieces for server.py and live_api.py: seed writes, Reset and friendly errors."""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi.responses import JSONResponse

from core import BKEY, data_lock, db, get_business, rebuild_matrix
from engine import matrix
from seed.build import build_seed

PACIFIC = ZoneInfo("America/Los_Angeles")
SEEDED_COLLECTIONS = ["businesses", "units", "stops", "route_plans", "run_history", "directory", "prospects", "requests"]
CLEARED_ON_RESET = ["agent_threads", "quotes", "messages", "engine_options", "change_log", "phone_messages", "route_changes", "route_proposals",
                    "agent_rules", "events", "demo_runs", "import_sources", "time_shifts"]
logger = logging.getLogger("drivepast")


def friendly(status, message, fields=None):
    detail = {"message": message}
    if fields:
        detail["fields"] = fields
    return JSONResponse(status_code=status, content={"detail": detail})


def demo_date_label(iso):
    d = datetime.fromisoformat(iso).date()
    return d.strftime("%A, %B ") + str(d.day) + d.strftime(", %Y")


async def on_time_by_unit():
    pipeline = [{"$match": {"business_key": BKEY}},
                {"$group": {"_id": "$unit_key", "runs": {"$sum": 1}, "on_time": {"$sum": {"$cond": ["$on_time", 1, 0]}}}}]
    return {r["_id"]: (r["on_time"], r["runs"]) async for r in db.run_history.aggregate(pipeline)}


def today_pacific():
    return datetime.now(PACIFIC).date()


async def ensure_indexes():
    await db.units.create_index("key")
    await db.stops.create_index([("unit_key", 1), ("seq", 1)])
    await db.route_plans.create_index([("unit_key", 1), ("is_current", 1)])
    await db.run_history.create_index("stop_key")
    await db.run_history.create_index("unit_key")
    await db.agent_threads.create_index("agent_key", unique=True)


async def first_seed(team_numbers):
    """Fresh database only: insert seed data into empty collections. Never drops or deletes."""
    payload = build_seed(today_pacific(), team_numbers)
    for name in SEEDED_COLLECTIONS:
        if not await db[name].count_documents({}, limit=1):
            await db[name].insert_many(payload[name])
    await ensure_indexes()
    matrix.invalidate()
    await rebuild_matrix((await get_business()).settings.model_dump())


async def write_seed(team_numbers):
    payload = build_seed(today_pacific(), team_numbers)
    staged = []
    try:
        for name in SEEDED_COLLECTIONS:
            stage = f"staging_{name}"
            await db[stage].drop()
            if payload[name]:
                await db[stage].insert_many(payload[name])
            else:
                await db.create_collection(stage)
            staged.append(stage)
    except Exception:
        for stage in staged:
            await db[stage].drop()
        raise
    for name in SEEDED_COLLECTIONS:
        await db[f"staging_{name}"].rename(name, dropTarget=True)
    for name in CLEARED_ON_RESET:
        await db[name].delete_many({})
    await ensure_indexes()
    matrix.invalidate()
    await rebuild_matrix((await get_business()).settings.model_dump())


async def reset_demo():
    async with data_lock:
        old = await db.businesses.find_one({"key": BKEY})
        team = (old or {}).get("settings", {}).get("team_numbers", [])
        try:
            await write_seed(team)
        except Exception as exc:
            logger.exception("Reset failed: %s", exc)
            return friendly(500, "Reset didn't finish. Try again.")
        biz = await get_business()
        clock = biz.settings.demo_clock_minutes
        async for p in db.route_plans.find({"business_key": BKEY, "is_current": True}, {"stops": 1}):
            keys = [r["stop_key"] for r in p["stops"] if r["arrival"] < clock]
            await db.stops.update_many({"business_key": BKEY, "key": {"$in": keys}},
                                       {"$set": {"done_date": biz.demo_date, "done_minutes": float(clock)}})
        from morning import preload_morning
        try:
            await preload_morning(PACIFIC)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Morning preload failed: %s", exc)
    return {"ok": True, "message": "Demo data reset", "demo_date": biz.demo_date,
            "demo_date_label": demo_date_label(biz.demo_date)}
